"""表驱动 MCP 工具注册：把 gis_toolkit 的 9 个工具映射为 gis_* MCP 工具。

- 工具集合 / 命名 / 描述取自 src.gis_toolkit.schemas.TOOL_SCHEMAS（表驱动，新增工具自动暴露）；
- handler 复用 create_gis_engine 创建引擎并调用对应方法，安全边界（输入白名单 / 产物文件名净化）
  由引擎内建的 _check_input_path / _sanitize_filename 承担，本层只负责工具映射；
- Gate 1 阶段：全局单引擎、首次工具调用时懒加载；EngineManager 结构上预留多会话扩展。

注：handler 参数使用纯类型注解（配合 docstring 参数说明生成 MCP schema），
不使用 Annotated[pydantic.Field]，以兼容 mcp SDK 1.12.x 的 issubclass 校验。
"""

from __future__ import annotations

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
            self._engine = create_gis_engine(
                out_dir=self._out_root,
                allowed_roots=self._allowed_roots,
            )
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
