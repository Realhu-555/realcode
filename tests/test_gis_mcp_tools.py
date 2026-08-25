"""Gate 1: gis_mcp 工具注册与安全边界（FastMCP 实例级验证，无需 stdio 子进程）"""

from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP
from src.gis_mcp import tools
from src.gis_toolkit.schemas import TOOL_SCHEMAS

EXPECTED_SCHEMA_COUNT = 41
HITL_TOOL_NAMES = ["gis_approve", "gis_permission_mode"]
EXPECTED_TOOL_NAMES = [f"gis_{s['function']['name']}" for s in TOOL_SCHEMAS] + HITL_TOOL_NAMES
EXPECTED_TOOL_COUNT = len(EXPECTED_TOOL_NAMES)  # 41 schema 工具 + 2 审批控制 = 43


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
    """TOOL_SCHEMAS 来源必须恰好 39 个工具（防 schema 源变化导致漏注册）"""
    assert len(TOOL_SCHEMAS) == EXPECTED_SCHEMA_COUNT


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


# ── P3：MCP 入口 HITL 审批同步（危险工具进人工审批）──────────


def _htil_gdf(tmp_path):
    """生成可编辑 GeoJSON 点图层并返回路径（放进白名单 data/）"""
    import geopandas as gpd
    from shapely.geometry import box

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    gdf = gpd.GeoDataFrame(
        {"name": ["A"], "val": [1]}, geometry=[box(0, 0, 10, 10)], crs="EPSG:4326"
    )
    src = data_dir / "poly.geojson"
    gdf.to_file(src, driver="GeoJSON")
    return str(src)


async def _htil_call(mcp, name, args):
    """调用 FastMCP 工具并解析 JSON 文本返回"""
    result = await mcp.call_tool(name, args)
    items = result if isinstance(result, list) else getattr(result, "content", [result])
    text = "".join(getattr(c, "text", "") for c in items)
    import json as _json

    return _json.loads(text)


def _htil_server(tmp_path, mode: str):
    """独立 FastMCP + 指定权限模式"""
    tools.init_engine_manager(
        out_root=str(tmp_path / "out"),
        allowed_roots=[str(tmp_path / "data")],
        permission_mode=mode,
    )
    mcp = FastMCP("htil")
    tools.register_tools(mcp)
    return mcp


async def test_mcp_htil_ask_pending_then_approve(tmp_path):
    """ask 模式：危险工具挂起 pending_approval 不执行，gis_approve(True) 后执行"""
    mcp = _htil_server(tmp_path, "ask")
    r = await _htil_call(mcp, "gis_load_data", {"path": _htil_gdf(tmp_path)})
    assert r["status"] == "ok"

    r = await _htil_call(mcp, "gis_remove_layer", {})
    assert r["status"] == "pending_approval"
    assert r["approval_id"]

    # 未批准前图层仍在
    snap = await _htil_call(mcp, "gis_list_layers", {})
    assert snap["has_layer"] is True

    # 批准后执行移除
    r2 = await _htil_call(mcp, "gis_approve", {"approval_id": r["approval_id"], "approve": True})
    assert r2["status"] == "ok"
    snap2 = await _htil_call(mcp, "gis_list_layers", {})
    assert snap2["has_layer"] is False


async def test_mcp_htil_ask_reject(tmp_path):
    """ask 模式：gis_approve(False) 拒绝，危险操作不执行"""
    mcp = _htil_server(tmp_path, "ask")
    await _htil_call(mcp, "gis_load_data", {"path": _htil_gdf(tmp_path)})

    r = await _htil_call(mcp, "gis_remove_layer", {})
    assert r["status"] == "pending_approval"

    r2 = await _htil_call(mcp, "gis_approve", {"approval_id": r["approval_id"], "approve": False})
    assert r2["status"] == "rejected"

    snap = await _htil_call(mcp, "gis_list_layers", {})
    assert snap["has_layer"] is True  # 未被移除


async def test_mcp_htil_readonly_rejects(tmp_path):
    """readonly 模式：危险工具直接拒绝，不生成审批"""
    mcp = _htil_server(tmp_path, "readonly")
    await _htil_call(mcp, "gis_load_data", {"path": _htil_gdf(tmp_path)})

    r = await _htil_call(mcp, "gis_remove_layer", {})
    assert r["status"] == "rejected"
    assert r["approval_id"] is None
    snap = await _htil_call(mcp, "gis_list_layers", {})
    assert snap["has_layer"] is True


async def test_mcp_htil_auto_executes(tmp_path):
    """auto 模式：危险工具直接执行，无需审批"""
    mcp = _htil_server(tmp_path, "auto")
    await _htil_call(mcp, "gis_load_data", {"path": _htil_gdf(tmp_path)})

    r = await _htil_call(mcp, "gis_remove_layer", {})
    assert r["status"] == "ok"
    snap = await _htil_call(mcp, "gis_list_layers", {})
    assert snap["has_layer"] is False


async def test_mcp_htil_permission_mode_switch(tmp_path):
    """gis_permission_mode：查询与切换权限模式"""
    mcp = _htil_server(tmp_path, "ask")
    r = await _htil_call(mcp, "gis_permission_mode", {})
    assert r["mode"] == "ask"

    r = await _htil_call(mcp, "gis_permission_mode", {"mode": "auto"})
    assert r["mode"] == "auto"

    r = await _htil_call(mcp, "gis_permission_mode", {})
    assert r["mode"] == "auto"


async def test_mcp_htil_non_dangerous_untouched(tmp_path):
    """非危险工具不受审批影响（ask 模式下直接执行）"""
    mcp = _htil_server(tmp_path, "ask")
    r = await _htil_call(mcp, "gis_load_data", {"path": _htil_gdf(tmp_path)})
    assert r["status"] == "ok"
    r = await _htil_call(mcp, "gis_inspect_data", {})
    assert r["status"] == "ok"
