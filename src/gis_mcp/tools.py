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
from pathlib import Path
from typing import Literal

# 预热重库：mapclassify 由 geopandas.plot(scheme=...) 延迟导入，若在 MCP 工具
# handler 首次触发可耗时数百秒；模块级提前加载（主线程）可将其压缩到数秒。
import mapclassify  # noqa: F401  (prewarm)
from mcp.server.fastmcp import FastMCP

from src.gis_toolkit.engine import GisEngine, create_gis_engine
from src.gis_toolkit.schemas import TOOL_SCHEMAS

# 项目根 = <project>/src/gis_mcp/tools.py 的 3 级父目录
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALLOWED_ROOTS = [str(_PROJECT_ROOT / "data")]
DEFAULT_OUT_ROOT = str(_PROJECT_ROOT / "data" / "gis_toolkit_out")


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
    """Gate 1：全局单引擎、懒加载；预留多会话扩展（未来按 session_id 维护引擎实例）"""

    def __init__(
        self,
        out_root: str | None = None,
        allowed_roots: list[str] | None = None,
    ) -> None:
        self._out_root = out_root or DEFAULT_OUT_ROOT
        self._allowed_roots = allowed_roots or list(DEFAULT_ALLOWED_ROOTS)
        self._engine: GisEngine | None = None
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


_manager: EngineManager | None = None


def init_engine_manager(
    out_root: str | None = None,
    allowed_roots: list[str] | None = None,
) -> None:
    """初始化（或重置）全局引擎管理器；不传参时使用默认 data/ 白名单与输出目录"""
    global _manager
    _manager = EngineManager(out_root=out_root, allowed_roots=allowed_roots)


def _get_manager() -> EngineManager:
    if _manager is None:
        raise RuntimeError("EngineManager 未初始化，请先调用 init_engine_manager()")
    return _manager


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
) -> dict:
    """对数值列聚合统计（可选按分组列分组），导出 CSV。

    Args:
        column: 被统计的数值列名。
        groupby: 分组列名（可选）。
        agg: 聚合方式（sum/mean/count/min/max）。
        output: 产物文件名，如 summary.csv。
    """
    return _get_manager().get().summarize(column=column, groupby=groupby, agg=agg, output=output)


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
    return _get_manager().get().join_by_location(
        other_path=other_path, predicate=predicate
    )


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


def _run_algorithm(
    algorithm: Literal["dissolve", "centroids", "convexhull"],
    params: dict | None = None,
) -> dict:
    """运行白名单 Processing 空间算法。

    Args:
        algorithm: 算法名（dissolve/centroids/convexhull）。
        params: 算法参数，如 {"field": "省份"}。
    """
    return _get_manager().get().run_algorithm(
        algorithm=algorithm, params=params or {}
    )


def _load_raster(path: str) -> dict:
    """加载栅格文件（TIFF / GeoTIFF）。

    Args:
        path: 栅格文件路径。
    """
    return _get_manager().get().load_raster(path=path)


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
    "run_algorithm": _run_algorithm,
    "load_raster": _load_raster,
    "finish": _finish,
}


def register_tools(mcp: FastMCP) -> None:
    """表驱动注册：遍历 TOOL_SCHEMAS，映射为 gis_* MCP 工具（只暴露这 9 个）"""
    for schema in TOOL_SCHEMAS:
        fn = schema["function"]
        name = fn["name"]
        mcp.add_tool(
            _HANDLERS[name],
            name=f"gis_{name}",
            description=fn["description"],
        )
