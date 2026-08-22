"""Gate 1: gis_mcp 工具注册与安全边界（FastMCP 实例级验证，无需 stdio 子进程）"""

from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP
from src.gis_mcp import tools
from src.gis_toolkit.schemas import TOOL_SCHEMAS

EXPECTED_TOOL_NAMES = [f"gis_{s['function']['name']}" for s in TOOL_SCHEMAS]
EXPECTED_TOOL_COUNT = 20


@pytest.fixture()
def mcp_server(tmp_path) -> FastMCP:
    tools.init_engine_manager(
        out_root=str(tmp_path / "out"),
        allowed_roots=[str(tmp_path / "data")],
    )
    mcp = FastMCP("test-gis-mcp")
    tools.register_tools(mcp)
    return mcp


def test_tool_schema_source_has_nine():
    """TOOL_SCHEMAS 来源必须恰好 9 个工具（防 schema 源变化导致漏注册）"""
    assert len(TOOL_SCHEMAS) == EXPECTED_TOOL_COUNT


async def test_registers_all_nine_gis_tools(mcp_server):
    """注册完整：只暴露 9 个 gis_* 工具，名称统一 gis_ 前缀"""
    listed = await mcp_server.list_tools()
    names = sorted(t.name for t in listed)
    assert len(names) == EXPECTED_TOOL_COUNT
    assert names == sorted(EXPECTED_TOOL_NAMES)
    assert all(n.startswith("gis_") for n in names)


async def test_only_gis_tools_exposed(mcp_server):
    """除 gis_* 9 个工具外无任何额外工具（工具白名单边界）"""
    listed = await mcp_server.list_tools()
    assert set(t.name for t in listed) == set(EXPECTED_TOOL_NAMES)


async def test_tool_schemas_match_tool_schemas(mcp_server):
    """MCP 工具的 inputSchema 与 TOOL_SCHEMAS 的参数定义一致（类型/必填/enum）"""
    listed = {t.name: t for t in await mcp_server.list_tools()}
    for schema in TOOL_SCHEMAS:
        fn = schema["function"]
        mcp_name = f"gis_{fn['name']}"
        assert mcp_name in listed
        params = fn["parameters"]
        schema_props = params.get("properties", {})
        mcp_props = listed[mcp_name].inputSchema.get("properties", {})
        mcp_required = set(listed[mcp_name].inputSchema.get("required", []))
        assert mcp_required == set(params.get("required", [])), f"{mcp_name} required 不一致"
        assert set(mcp_props) == set(schema_props), f"{mcp_name} 参数集合不一致"
        for pname, pinfo in schema_props.items():
            mcp_prop = mcp_props[pname]
            # 类型可能在顶层 type 或 anyOf 里（可选参数带 default）
            types = (
                [mcp_prop["type"]]
                if "type" in mcp_prop
                else [item["type"] for item in mcp_prop.get("anyOf", []) if "type" in item]
            )
            assert pinfo["type"] in types, f"{mcp_name}.{pname} 类型不一致"
            if "enum" in pinfo:
                enums = mcp_prop.get("enum") or next(
                    (item.get("enum") for item in mcp_prop.get("anyOf", []) if item.get("enum")),
                    None,
                )
                assert enums == pinfo["enum"], f"{mcp_name}.{pname} enum 不一致"


async def test_engine_lazy_init(tmp_path):
    """单引擎懒加载：初始化后不建引擎，首次 get() 才创建"""
    tools.init_engine_manager(
        out_root=str(tmp_path / "out"),
        allowed_roots=[str(tmp_path / "data")],
    )
    mgr = tools._get_manager()
    assert mgr._engine is None
    engine = mgr.get()
    assert engine is not None
    assert mgr.get() is engine  # 单例复用


async def test_engine_init_with_defaults(tmp_path):
    """未显式传参时默认 out_root 与 allowed_roots 取自工具包默认值"""
    tools.init_engine_manager()
    mgr = tools._get_manager()
    assert mgr._allowed_roots  # 默认 data 白名单非空
    assert mgr._out_root
    assert mgr.get() is not None


def test_resolve_out_root_run_dir(tmp_path, monkeypatch):
    """默认产物目录生成 run-<时间戳> 子目录（隔离各次运行）；显式路径原样使用"""
    monkeypatch.setattr(tools, "DEFAULT_OUT_ROOT", str(tmp_path / "base"))
    run_dir = tools.resolve_out_root()
    assert Path(run_dir).name.startswith("run-")
    assert Path(run_dir).is_dir()
    assert tools.resolve_out_root(str(tmp_path / "custom")) == str(tmp_path / "custom")
