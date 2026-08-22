"""Gate 1: GIS MCP Server（FastMCP / stdio）— 接入 DeepSeek Harness（dsh）。

把现有 GIS 引擎（GisEngine/QgsEngine 双引擎、9 个 gis_* 工具）封装为 Python MCP Server，
供 dsh 通过内置 MCP 客户端调用。安全边界复用：输入白名单（allowed_roots，默认 data/）、
产物文件名净化、工具白名单（只暴露 gis_* 9 个工具）。

运行方式（两种等价）：
    python -m src.gis_mcp.server --out-root <DIR> --allowed-roots <DIR> [DIR ...]
    python src/gis_mcp/server.py --out-root <DIR> --allowed-roots <DIR> [DIR ...]

默认（不传参）：out-root = <项目根>/data/gis_toolkit_out，allowed-roots = <项目根>/data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 支持直接运行 python src/gis_mcp/server.py（此时项目根不在 sys.path）
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mcp.server.fastmcp import FastMCP

from src.gis_mcp import tools
from src.utils.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def default_allowed_roots() -> list[str]:
    """默认输入白名单：settings.gis_allowed_roots（.env 可覆盖）"""
    roots = list(settings.gis_allowed_roots)
    return roots or [str(_PROJECT_ROOT / "data")]


def default_out_root() -> str:
    """默认产物输出目录：settings.gis_out_root（.env 可覆盖）"""
    return settings.gis_out_root


def build_server(out_root: str | None = None, allowed_roots: list[str] | None = None) -> FastMCP:
    """构建并注册 9 个 gis_* 工具的 FastMCP 实例（引擎懒加载）"""
    tools.init_engine_manager(
        out_root=out_root or default_out_root(),
        allowed_roots=allowed_roots or default_allowed_roots(),
    )
    mcp = FastMCP("gis-mcp")
    tools.register_tools(mcp)
    return mcp


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="GIS MCP Server（FastMCP/stdio，供 DeepSeek Harness 调用）"
    )
    parser.add_argument(
        "--out-root",
        default=None,
        help="产物输出目录（默认 <项目根>/data/gis_toolkit_out/run-<时间戳>）",
    )
    parser.add_argument(
        "--allowed-roots",
        nargs="+",
        default=None,
        help="输入路径白名单（可多个，默认 <项目根>/data）",
    )
    args = parser.parse_args(argv)
    if args.out_root is None:
        args.out_root = tools.resolve_out_root()
    mcp = build_server(out_root=args.out_root, allowed_roots=args.allowed_roots)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
