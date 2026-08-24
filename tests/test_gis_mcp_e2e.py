"""Gate 1: 用 mcp SDK 客户端（stdio 子进程）实际调用 gis_mcp server

跑通 gdp_demo.csv 的 加载→inspect→choropleth→summarize→export_geojson 完整链路，
并验证安全边界：白名单外路径 / 非法产物文件名被拒。

注意：stdio_client 内部的 anyio cancel scope 与 pytest-asyncio 的 async generator
fixture 在 teardown 阶段存在兼容问题（RuntimeError: Attempted to exit cancel scope
in a different task），因此这里不使用 async fixture，而是每个用例内部用
asyncio.run() 建立独立的子进程会话，天然满足 Gate 1“每会话独立引擎”的语义。
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GDP_CSV = PROJECT_ROOT / "data" / "gis_demo" / "gdp_demo.csv"


def _server_params(out_root: Path) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "src.gis_mcp.server",
            "--out-root",
            str(out_root),
            "--allowed-roots",
            str(PROJECT_ROOT / "data"),
        ],
        cwd=str(PROJECT_ROOT),
    )


def _with_session(coro, out_root: Path):
    """在独立 asyncio 事件循环中启动 stdio 子进程会话并执行 coro(session)"""

    async def _run():
        params = _server_params(out_root)
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as sess,
        ):
            await sess.initialize()
            return await coro(sess)

    return asyncio.run(_run())


def _payload(result) -> dict:
    """从 CallToolResult 提取 JSON 负载"""
    assert not result.isError, f"工具调用失败: {result.content}"
    return json.loads(result.content[0].text)


def _error_text(result) -> str:
    return "".join(c.text for c in result.content if hasattr(c, "text"))


def test_list_tools_has_thirty_two(tmp_path):
    """stdio 客户端 list_tools 返回 34 个 gis_* 工具"""

    async def _run(sess):
        tools = await sess.list_tools()
        return sorted(t.name for t in tools.tools)

    names = _with_session(_run, tmp_path / "out")
    assert len(names) == 37
    assert all(n.startswith("gis_") for n in names)


def test_full_chain_load_to_geojson(tmp_path):
    """完整链路：load → inspect → choropleth → summarize → export_geojson → finish"""
    out_root = tmp_path / "out"

    async def _run(sess):
        # 1. load_data
        r = await sess.call_tool("gis_load_data", {"path": str(GDP_CSV)})
        payload = _payload(r)
        assert payload["status"] == "ok"
        assert payload["layer"]["rows"] == 31
        assert payload["layer"]["crs"] == "EPSG:4326"

        # 2. inspect_data
        r = await sess.call_tool("gis_inspect_data", {})
        payload = _payload(r)
        assert payload["rows"] == 31
        assert "province" in payload["columns"]
        assert len(payload["bounds"]) == 4

        # 3. choropleth
        r = await sess.call_tool(
            "gis_choropleth",
            {"column": "gdp", "scheme": "Quantiles", "k": 5, "output": "gdp_choropleth.png"},
        )
        payload = _payload(r)
        assert payload["status"] == "ok"
        assert (out_root / "gdp_choropleth.png").is_file()
        assert any(p.endswith("gdp_choropleth.png") for p in payload["output_paths"])
        assert all(Path(p).is_file() for p in payload["output_paths"])

        # 4. summarize
        r = await sess.call_tool(
            "gis_summarize",
            {"column": "gdp", "groupby": "province", "agg": "sum", "output": "gdp_summary.csv"},
        )
        payload = _payload(r)
        assert payload["summary_rows"] == 31
        assert (out_root / "gdp_summary.csv").is_file()

        # 5. export_geojson
        r = await sess.call_tool("gis_export_geojson", {"output": "gdp_layer.geojson"})
        payload = _payload(r)
        assert payload["status"] == "ok"
        assert (out_root / "gdp_layer.geojson").is_file()

        # 6. finish：声明真实产物，谎报文件被剔除
        r = await sess.call_tool(
            "gis_finish",
            {
                "outputs": [
                    "gdp_choropleth.png",
                    "gdp_summary.csv",
                    "gdp_layer.geojson",
                    "fake.png",
                ],
                "summary": "完成 gdp_demo 分级设色与汇总",
            },
        )
        payload = _payload(r)
        assert payload["status"] == "finished"
        assert "fake.png" not in payload["outputs"]
        assert "fake.png" not in "|".join(payload["output_paths"])
        assert all(Path(p).is_file() for p in payload["output_paths"])

    _with_session(_run, out_root)


def test_whitelist_rejects_outside_root(tmp_path):
    """白名单外路径被拒：加载 data/ 之外的文件必须报错"""

    async def _run(sess):
        outside = PROJECT_ROOT / "pyproject.toml"
        assert outside.is_file()
        r = await sess.call_tool("gis_load_data", {"path": str(outside)})
        assert r.isError
        assert "白名单" in _error_text(r)

    _with_session(_run, tmp_path / "out")


def test_whitelist_rejects_missing_file(tmp_path):
    """白名单内但不存在的文件被拒"""

    async def _run(sess):
        r = await sess.call_tool("gis_load_data", {"path": str(PROJECT_ROOT / "data" / "nope.csv")})
        assert r.isError
        assert "文件不存在" in _error_text(r)

    _with_session(_run, tmp_path / "out")


def test_invalid_output_filename_rejected(tmp_path):
    """非法产物文件名被拒：路径穿越 / 子路径 / 空名不允许"""
    out_root = tmp_path / "out"

    async def _run(sess):
        # 先加载合法图层，保证报错来自文件名净化而非“没有图层”
        r = await sess.call_tool("gis_load_data", {"path": str(GDP_CSV)})
        _payload(r)
        for bad in ("../evil.geojson", "a/b.geojson", ""):
            r = await sess.call_tool("gis_export_geojson", {"output": bad})
            assert r.isError, f"产物文件名 {bad!r} 应被拒绝"
            assert "非法产物文件名" in _error_text(r)

    _with_session(_run, out_root)


def test_inspect_without_layer_fails(tmp_path):
    """未加载图层时 inspect 报错（新会话初始无图层，状态不串扰）"""

    async def _run(sess):
        r = await sess.call_tool("gis_inspect_data", {})
        assert r.isError
        assert "没有图层" in _error_text(r)

    _with_session(_run, tmp_path / "out")
