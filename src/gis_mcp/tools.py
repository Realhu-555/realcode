"""表驱动 MCP 工具注册：把 gis_toolkit 的 9 个工具映射为 gis_* MCP 工具。

- 工具集合 / 命名 / 描述取自 src.gis_toolkit.schemas.TOOL_SCHEMAS（表驱动，新增工具自动暴露）；
- handler 复用 create_gis_engine 创建引擎并调用对应方法，安全边界（输入白名单 / 产物文件名净化）
  由引擎内建的 _check_input_path / _sanitize_filename 承担，本层只负责工具映射；
- Gate 1 阶段：全局单引擎、首次工具调用时懒加载；EngineManager 结构上预留多会话扩展。

注：handler 参数使用纯类型注解（配合 docstring 参数说明生成 MCP schema），
不使用 Annotated[pydantic.Field]，以兼容 mcp SDK 1.12.x 的 issubclass 校验。
"""

from __future__ import annotations

import datetime
import functools
from pathlib import Path
from typing import Literal

# 预热重库：mapclassify 由 geopandas.plot(scheme=...) 延迟导入，若在 MCP 工具
# handler 首次触发可耗时数百秒；模块级提前加载（主线程）可将其压缩到数秒。
import mapclassify  # noqa: F401  (prewarm)
from mcp.server.fastmcp import FastMCP

from src.gis_toolkit.approval import DANGEROUS_TOOLS, ApprovalGate
from src.gis_toolkit.engine import GisEngine, create_gis_engine
from src.gis_toolkit.schemas import TOOL_SCHEMAS
from src.utils.config import settings

# 项目根 = <project>/src/gis_mcp/tools.py 的 3 级父目录
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# 默认产物目录 / 输入白名单从 settings 读取（.env 可覆盖，见 src/utils/config.py）
DEFAULT_OUT_ROOT = settings.gis_out_root
DEFAULT_ALLOWED_ROOTS = list(settings.gis_allowed_roots) or [str(_PROJECT_ROOT / "data")]
# 权限模式从 settings 读取（.env 可覆盖，默认 ask）
DEFAULT_PERMISSION_MODE = getattr(settings, "gis_permission_mode", "ask")
# MCP 审批超时（秒）：对话式确认可能跨多个来回，放宽到 10 分钟
MCP_APPROVAL_TTL_SECONDS = 600


def resolve_out_root(out_root: str | None = None) -> str:
    """产物根目录：显式传入则原样使用；默认生成 run-<时间戳> 子目录隔离各次运行。

    每次 MCP Server 启动（对应一次 dsh 连接）写入独立子目录，
    避免多次运行的产物在共享根目录互相覆盖。
    """
    if out_root:
        return out_root
    base = Path(DEFAULT_OUT_ROOT)
    run_dir = base / f"run-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return str(run_dir)


def _warmup_matplotlib() -> None:
    """预热 matplotlib 渲染栈，避免首个 choropleth/scatter 因字体/渲染初始化超时。"""
    try:
        import io

        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(2, 2))
        ax.plot([0, 1], [0, 1])
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
    except Exception:
        pass


class EngineManager:
    """Gate 1：全局单引擎、懒加载；预留多会话扩展（未来按 session_id 维护引擎实例）

    Gate 8+/P3：增加会话级 HITL 审批门（ApprovalGate），危险工具（编辑/删除/覆盖）
    在 ask 模式下挂起为 pending_approval，由 gis_approve / gis_reject 人工确认后执行。
    """

    def __init__(
        self,
        out_root: str | None = None,
        allowed_roots: list[str] | None = None,
        permission_mode: str = "ask",
    ) -> None:
        self._out_root = out_root or DEFAULT_OUT_ROOT
        self._allowed_roots = allowed_roots or list(DEFAULT_ALLOWED_ROOTS)
        self._engine: GisEngine | None = None
        self.approval_gate = ApprovalGate(mode=permission_mode, ttl=MCP_APPROVAL_TTL_SECONDS)
        # 挂起的审批请求: approval_id -> (handler, kwargs)，approve 后重放执行
        self._pending: dict[str, tuple] = {}
        # 多会话扩展预留：self._engines: dict[str, GisEngine] = {}

    def get(self) -> GisEngine:
        """首次调用时创建引擎（懒加载），后续复用同一实例（Gate 1 单引擎）"""
        if self._engine is None:
            engine = create_gis_engine(
                out_dir=self._out_root,
                allowed_roots=self._allowed_roots,
            )
            _warmup_matplotlib()
            self._engine = engine
        return self._engine

    def remember_pending(self, approval_id: str, fn, kwargs: dict) -> None:
        """记录待审批执行（approval_id -> handler + 参数），供 approve 后重放"""
        self._pending[approval_id] = (fn, dict(kwargs))

    def pop_pending(self, approval_id: str) -> tuple | None:
        """取走并移除待审批执行记录；不存在返回 None"""
        return self._pending.pop(approval_id, None)


_manager: EngineManager | None = None


def init_engine_manager(
    out_root: str | None = None,
    allowed_roots: list[str] | None = None,
    permission_mode: str | None = None,
) -> None:
    """初始化（或重置）全局引擎管理器；不传参时使用默认 data/ 白名单与输出目录"""
    global _manager
    _manager = EngineManager(
        out_root=out_root,
        allowed_roots=allowed_roots,
        permission_mode=permission_mode or DEFAULT_PERMISSION_MODE,
    )


def _get_manager() -> EngineManager:
    if _manager is None:
        raise RuntimeError("EngineManager 未初始化，请先调用 init_engine_manager()")
    return _manager


def _guarded(name: str, fn):
    """危险工具守卫（P3 HITL 同步）：按权限模式放行 / 挂起 / 拒绝。

    - readonly：直接拒绝（不执行）；
    - auto：放行执行；
    - ask（默认）：挂起为 pending_approval，由 gis_approve / gis_reject 人工确认。

    functools.wraps 使 inspect.signature 跟随原 handler，FastMCP 仍能提取
    原工具的参数 schema（否则 wrapper 的 *args/**kwargs 会破坏参数校验）。
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        manager = _get_manager()
        res = manager.approval_gate.check(name, kwargs)
        if res is None:
            return fn(*args, **kwargs)
        if res["status"] == "pending_approval":
            manager.remember_pending(res["approval_id"], fn, kwargs)
        return res

    return wrapper


def _approve(approval_id: str, approve: bool = True) -> dict:
    """人工审批挂起的危险操作（approve=True 批准执行，False 拒绝）。

    Args:
        approval_id: 危险工具返回的审批请求 ID。
        approve: True 批准并执行，False 拒绝。
    """
    manager = _get_manager()
    action = "approve" if approve else "reject"
    result = manager.approval_gate.resolve(approval_id, action)
    if not result.get("ok"):
        return result
    if not approve:
        return {
            "ok": True,
            "approval_id": approval_id,
            "status": "rejected",
            "message": "已拒绝执行该操作",
        }
    pending = manager.pop_pending(approval_id)
    if pending is None:
        return {
            "ok": True,
            "approval_id": approval_id,
            "status": "approved",
            "message": "已批准，但执行记录已失效，操作未执行",
        }
    fn, kwargs = pending
    return fn(**kwargs)


def _permission_mode(mode: str | None = None) -> dict:
    """查看或切换权限模式（readonly 只读拒绝 / auto 自动放行 / ask 人工审批）。

    Args:
        mode: 可选。不传则返回当前模式；传 readonly/auto/ask 则切换会话级权限模式。
    """
    gate = _get_manager().approval_gate
    if mode is not None:
        gate.set_mode(mode)
    return {"status": "ok", "mode": gate.mode}


# ── 9 个工具 handler（签名即 MCP 参数 schema，与 TOOL_SCHEMAS 一致）───────────


def _load_data(path: str) -> dict:
    """加载数据文件为当前图层。

    Args:
        path: 数据文件路径（必须来自 data 白名单目录）。
    """
    return _get_manager().get().load_data(path)


def _inspect_data() -> dict:
    """查看当前图层：字段、行数、CRS、范围、样例行。"""
    return _get_manager().get().inspect_data()


def _buffer(distance: float) -> dict:
    """对当前图层所有要素做缓冲区。

    Args:
        distance: 缓冲区距离（单位随 CRS：度 / 米）。
    """
    return _get_manager().get().buffer(distance)


def _overlay(
    other_path: str,
    how: Literal["intersection", "union", "difference", "symmetric_difference"],
) -> dict:
    """与另一图层做空间叠加。

    Args:
        other_path: 第二个数据文件路径（CSV / GeoJSON / zip）。
        how: 叠加方式（intersection/union/difference/symmetric_difference）。
    """
    return _get_manager().get().overlay(other_path=other_path, how=how)


def _choropleth(
    column: str,
    scheme: Literal["NaturalBreaks", "Quantiles", "EqualInterval"] = "NaturalBreaks",
    k: int = 5,
    output: str = "choropleth.png",
) -> dict:
    """对数值列做分级设色图并保存 PNG。

    Args:
        column: 用于分级的数值列名。
        scheme: 分级方法（NaturalBreaks/Quantiles/EqualInterval）。
        k: 分级数量（默认 5）。
        output: 产物文件名，如 choropleth.png。
    """
    return _get_manager().get().choropleth(column=column, scheme=scheme, k=k, output=output)


def _scatter_plot(x: str, y: str, output: str = "scatter.png") -> dict:
    """对两个数值列画散点图并保存 PNG。

    Args:
        x: X 轴列名。
        y: Y 轴列名。
        output: 产物文件名，如 scatter.png。
    """
    return _get_manager().get().scatter_plot(x=x, y=y, output=output)


def _summarize(
    column: str,
    groupby: str | None = None,
    agg: Literal["sum", "mean", "count", "min", "max"] = "sum",
    output: str = "summary.csv",
    sort_by: str | None = None,
    desc: bool = False,
) -> dict:
    """对数值列聚合统计（可选按分组列分组），导出 CSV。

    Args:
        column: 被统计的数值列名。
        groupby: 分组列名（可选）。
        agg: 聚合方式（sum/mean/count/min/max）。
        output: 产物文件名，如 summary.csv。
        sort_by: 排序依据列（默认分组列或统计列）。
        desc: 降序排序（取 Top 名单时传 true）。
    """
    return (
        _get_manager()
        .get()
        .summarize(
            column=column,
            groupby=groupby,
            agg=agg,
            output=output,
            sort_by=sort_by,
            desc=desc,
        )
    )


def _export_geojson(output: str) -> dict:
    """把当前图层导出为 GeoJSON 文件。

    Args:
        output: 产物文件名，如 layer.geojson。
    """
    return _get_manager().get().export_geojson(output=output)


def _join_by_location(
    other_path: str,
    predicate: Literal["intersects", "within", "contains"] = "intersects",
) -> dict:
    """把另一图层按空间关系并入当前图层。

    Args:
        other_path: 第二个数据文件路径（CSV / GeoJSON / zip）。
        predicate: 空间关系（intersects/within/contains）。
    """
    return _get_manager().get().join_by_location(other_path=other_path, predicate=predicate)


def _voronoi() -> dict:
    """对当前点图层生成泰森多边形。"""
    return _get_manager().get().voronoi()


def _get_crs() -> dict:
    """查看当前图层坐标系。"""
    return _get_manager().get().get_crs()


def _set_crs(crs: str) -> dict:
    """重设当前图层坐标系（不重投影）。

    Args:
        crs: 坐标系，如 EPSG:4326 或 EPSG:3857。
    """
    return _get_manager().get().set_crs(crs=crs)


def _list_layers() -> dict:
    """查看当前会话状态快照。"""
    return _get_manager().get().list_layers()


def _field_statistics(column: str) -> dict:
    """对数值列做字段统计。

    Args:
        column: 数值列名。
    """
    return _get_manager().get().field_statistics(column=column)


def _unique_values(column: str) -> dict:
    """查看某列唯一取值（最多 50 个）。

    Args:
        column: 列名。
    """
    return _get_manager().get().unique_values(column=column)


def _transform_coords(target_crs: str) -> dict:
    """把当前图层重投影到目标坐标系。

    Args:
        target_crs: 目标坐标系，如 EPSG:3857。
    """
    return _get_manager().get().transform_coords(target_crs=target_crs)


def _render_map(output: str = "map.png") -> dict:
    """把当前图层渲染成 PNG 地图。

    Args:
        output: 产物文件名，如 map.png。
    """
    return _get_manager().get().render_map(output=output)


def _layout_map(
    title: str = "地图排版",
    legend_column: str | None = None,
    show_legend: bool = True,
    show_scalebar: bool = True,
    show_north_arrow: bool = True,
    output: str = "layout_map.png",
) -> dict:
    """地图排版出图（标题/图例/比例尺/指北针）。

    Args:
        title: 版面标题。
        legend_column: 生成图例的字段名（分类设色图例）。
        show_legend: 是否显示图例。
        show_scalebar: 是否显示比例尺。
        show_north_arrow: 是否显示指北针。
        output: 产物文件名，如 layout_map.png。
    """
    return (
        _get_manager()
        .get()
        .layout_map(
            title=title,
            legend_column=legend_column,
            show_legend=show_legend,
            show_scalebar=show_scalebar,
            show_north_arrow=show_north_arrow,
            output=output,
        )
    )


def _run_algorithm(
    algorithm: Literal["dissolve", "centroids", "convexhull"],
    params: dict | None = None,
) -> dict:
    """运行白名单 Processing 空间算法。

    Args:
        algorithm: 算法名（dissolve/centroids/convexhull）。
        params: 算法参数，如 {"field": "省份"}。
    """
    return _get_manager().get().run_algorithm(algorithm=algorithm, params=params or {})


def _load_raster(path: str) -> dict:
    """加载栅格文件（TIFF / GeoTIFF）。

    Args:
        path: 栅格文件路径。
    """
    return _get_manager().get().load_raster(path=path)


def _load_basemap(source: Literal["xyz", "wms", "local"], url: str, name: str = "底图") -> dict:
    """加载底图（xyz/wms 在线瓦片 / local 本地栅格）。

    Args:
        source: 底图来源（xyz/wms/local）。
        url: xyz/wms 服务地址或本地栅格路径。
        name: 底图名称。
    """
    return _get_manager().get().load_basemap(source=source, url=url, name=name)


def _start_editing() -> dict:
    """开始编辑会话。"""
    return _get_manager().get().start_editing()


def _add_features(geometry: str, attributes: dict | None = None) -> dict:
    """新增要素（WKT 几何 + 可选属性）。

    Args:
        geometry: 新要素几何（WKT）。
        attributes: 可选属性键值。
    """
    return _get_manager().get().add_features(geometry=geometry, attributes=attributes or {})


def _update_features(where: str, attributes: dict) -> dict:
    """按条件更新要素属性。

    Args:
        where: 筛选条件表达式。
        attributes: 要更新的属性键值。
    """
    return _get_manager().get().update_features(where=where, attributes=attributes)


def _update_geometry(feature_id: int, geometry: str) -> dict:
    """修改指定要素几何。

    Args:
        feature_id: 要素行号（0 起）。
        geometry: 新几何（WKT）。
    """
    return _get_manager().get().update_geometry(feature_id=feature_id, geometry=geometry)


def _delete_features(ids: list[int]) -> dict:
    """按要素行号删除。

    Args:
        ids: 要删除的要素行号列表。
    """
    return _get_manager().get().delete_features(ids=ids)


def _calculate_field(expression: str, field_name: str, where: str | None = None) -> dict:
    """按表达式生成新字段（列）。

    Args:
        expression: 计算表达式，如 'gdp / population'。
        field_name: 新字段名（不可与现有字段重名）。
        where: 可选条件表达式，只对满足条件的要素计算。
    """
    return (
        _get_manager()
        .get()
        .calculate_field(expression=expression, field_name=field_name, where=where)
    )


def _join_by_attribute(
    other_path: str,
    left_key: str,
    right_key: str,
    how: Literal["inner", "left"] = "inner",
) -> dict:
    """把 CSV/表按关键字段属性连接到当前图层。

    Args:
        other_path: 关联表文件路径（CSV / GeoJSON / zip）。
        left_key: 当前图层用于连接的字段名。
        right_key: 关联表中用于连接的字段名。
        how: inner 只保留匹配行 / left 保留当前图层全部行。
    """
    return (
        _get_manager()
        .get()
        .join_by_attribute(
            other_path=other_path,
            left_key=left_key,
            right_key=right_key,
            how=how,
        )
    )


def _commit_edits() -> dict:
    """提交编辑会话。"""
    return _get_manager().get().commit_edits()


def _rollback_edits() -> dict:
    """回滚编辑会话。"""
    return _get_manager().get().rollback_edits()


def _rename_layer(new_name: str) -> dict:
    """重命名当前图层（仅改图层名称，不影响底层数据文件）。"""
    return _get_manager().get().rename_layer(new_name=new_name)


def _remove_layer() -> dict:
    """移除当前图层（危险操作，需人工审批）。"""
    return _get_manager().get().remove_layer()


def _export_layer_inventory(output: str = "layer_inventory.json") -> dict:
    """导出当前图层清单到 JSON 文件。"""
    return _get_manager().get().export_layer_inventory(output=output)


def _duplicate_layer() -> dict:
    """复制当前图层。"""
    return _get_manager().get().duplicate_layer()


def _categorized(column: str, output: str = "categorized.png") -> dict:
    """对分类列做分类设色图并保存 PNG。

    Args:
        column: 分类列名（文本/枚举）。
        output: 产物文件名。
    """
    return _get_manager().get().categorized(column=column, output=output)


def _set_labeling(label_field: str, enabled: bool = True) -> dict:
    """设置当前图层字段标注。

    Args:
        label_field: 标注字段名。
        enabled: 是否启用标注。
    """
    return _get_manager().get().set_labeling(label_field=label_field, enabled=enabled)


def _get_project_info() -> dict:
    """获取当前工程信息。"""
    return _get_manager().get().get_project_info()


def _save_project(path: str = "gis_project.qgz") -> dict:
    """把当前会话保存为 QGIS 工程文件（.qgz）。

    Args:
        path: 工程文件名（默认 gis_project.qgz）。
    """
    return _get_manager().get().save_project(path=path)


def _download_osm_buildings(
    city: str, south: float, west: float, north: float, east: float
) -> dict:
    """从 OpenStreetMap Overpass 下载指定范围建筑轮廓并估算高度。

    Args:
        city: 城市名/区域标识，用于生成文件名（如 beijing_chaoyang）。
        south: 范围南纬（-90~90）。
        west: 范围西经（-180~180）。
        north: 范围北纬（-90~90）。
        east: 范围东经（-180~180）。
    """
    return (
        _get_manager()
        .get()
        .download_osm_buildings(city=city, south=south, west=west, north=north, east=east)
    )


def _render_3d(output: str | None = None) -> dict:
    """把当前图层导出为 3D 城市预览（写入静态目录并返回浏览器访问 URL）。

    Args:
        output: 预览文件名（不含扩展名），如 beijing_3d。
    """
    return _get_manager().get().render_3d(output=output)


def _finish(outputs: list[str], summary: str) -> dict:
    """任务完成：声明产出文件清单与结论。

    Args:
        outputs: 本次任务真实产出的文件名列表。
        summary: 任务结论说明。
    """
    return _get_manager().get().finish(outputs=outputs, summary=summary)


# 工具名（去掉 gis_ 前缀）→ handler，注册时遍历 TOOL_SCHEMAS 统一命名与描述
_HANDLERS = {
    "load_data": _load_data,
    "inspect_data": _inspect_data,
    "buffer": _buffer,
    "overlay": _overlay,
    "choropleth": _choropleth,
    "scatter_plot": _scatter_plot,
    "summarize": _summarize,
    "export_geojson": _export_geojson,
    "join_by_location": _join_by_location,
    "voronoi": _voronoi,
    "get_crs": _get_crs,
    "set_crs": _set_crs,
    "list_layers": _list_layers,
    "field_statistics": _field_statistics,
    "unique_values": _unique_values,
    "transform_coords": _transform_coords,
    "render_map": _render_map,
    "layout_map": _layout_map,
    "run_algorithm": _run_algorithm,
    "load_raster": _load_raster,
    "load_basemap": _load_basemap,
    "start_editing": _start_editing,
    "add_features": _add_features,
    "update_features": _update_features,
    "update_geometry": _update_geometry,
    "delete_features": _delete_features,
    "calculate_field": _calculate_field,
    "join_by_attribute": _join_by_attribute,
    "commit_edits": _commit_edits,
    "rollback_edits": _rollback_edits,
    "rename_layer": _rename_layer,
    "remove_layer": _remove_layer,
    "export_layer_inventory": _export_layer_inventory,
    "duplicate_layer": _duplicate_layer,
    "categorized": _categorized,
    "set_labeling": _set_labeling,
    "get_project_info": _get_project_info,
    "save_project": _save_project,
    "download_osm_buildings": _download_osm_buildings,
    "render_3d": _render_3d,
    "finish": _finish,
}


def register_tools(mcp: FastMCP) -> None:
    """表驱动注册：遍历 TOOL_SCHEMAS，映射为 gis_* MCP 工具（只暴露这 9 个）

    危险工具（编辑/删除/覆盖，见 DANGEROUS_TOOLS）自动套 HITL 审批守卫；
    另注册审批控制工具 gis_approve / gis_permission_mode（不入 TOOL_SCHEMAS）。
    """
    for schema in TOOL_SCHEMAS:
        fn = schema["function"]
        name = fn["name"]
        handler = _HANDLERS[name]
        if name in DANGEROUS_TOOLS:
            handler = _guarded(name, handler)
        mcp.add_tool(
            handler,
            name=f"gis_{name}",
            description=fn["description"],
        )
    # HITL 审批控制工具（独立于 TOOL_SCHEMAS，单独注册）
    mcp.add_tool(
        _approve,
        name="gis_approve",
        description="人工审批挂起的危险操作（approve=True 批准执行，False 拒绝）",
    )
    mcp.add_tool(
        _permission_mode,
        name="gis_permission_mode",
        description="查看或切换权限模式（readonly 只读拒绝 / auto 自动放行 / ask 人工审批）",
    )
