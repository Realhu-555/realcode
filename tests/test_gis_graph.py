"""GIS 编排图测试 — 完整流程 / 追问 / 校验回环 / 危险脚本"""

import zipfile

from src.orchestrator.graph import create_gis_graph


def _as_agent(fn):
    """把裸函数包装成带 .run 的 Agent 对象（测试用）"""

    class _FakeAgent:
        def run(self, state):
            return fn(state)

    return _FakeAgent()


def _fake_plan(state):
    return {
        **state,
        "task_plan": "1. 读取数据\n2. 按省份分级\n3. 出图",
        "current_stage": "design",
    }


def _fake_plan_ask(state):
    return {**state, "ask_user": "数据里哪一列是省份？", "current_stage": "plan"}


def _fake_design(state):
    return {
        **state,
        "tech_plan": "坐标系 EPSG:4326\n输出文件: choropleth.png",
        "current_stage": "codegen",
    }


_GOOD_SCRIPT = (
    "import pandas as pd\n"
    "import geopandas as gpd\n"
    "import matplotlib.pyplot as plt\n"
    "df = pd.DataFrame({\"province\": [\"A\", \"B\"], \"gdp\": [1, 2],"
    " \"lon\": [116.4, 121.5], \"lat\": [39.9, 31.2]})\n"
    "gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[\"lon\"], df[\"lat\"]), crs=\"EPSG:4326\")\n"
    "print(\"CRS:\", gdf.crs.to_string())\n"
    "fig, ax = plt.subplots()\n"
    "gdf.plot(ax=ax, column=\"gdp\")\n"
    "fig.savefig(\"choropleth.png\")\n"
    "print(\"ROWS:\", len(gdf))\n"
)


def _fake_codegen_good(state):
    return {**state, "script": _GOOD_SCRIPT, "current_stage": "exec"}


def _fake_codegen_evil(state):
    evil = "import os\nos.remove(\"data.csv\")"
    return {**state, "script": evil, "current_stage": "exec"}


def _fake_checker_pass(state):
    return {**state, "check_report": "- ✅ choropleth.png 存在\n整体结论: PASS", "current_stage": "check"}


def _fake_checker_fail(state):
    return {**state, "check_report": "- ❌ 图不可读\n整体结论: FAIL", "current_stage": "check"}


def _initial_state():
    return {
        "user_request": "把 GDP.csv 按省份做分级设色图",
        "data_file": None,
        "data_schema": "province: str\ngdp: int",
        "current_stage": "plan",
        "messages": [],
    }


def test_gis_pipeline_pass_flow(tmp_path):
    """完整流程：plan→design→codegen→exec→checker(PASS)→export→done"""
    agents = {
        "plan": _as_agent(_fake_plan),
        "design": _as_agent(_fake_design),
        "codegen": _as_agent(_fake_codegen_good),
        "checker": _as_agent(_fake_checker_pass),
    }
    graph = create_gis_graph(agents, export_dir=str(tmp_path), project_id="t1")
    result = graph.invoke(_initial_state())

    assert result["current_stage"] == "done"
    assert result.get("rewrite_round") is None
    assert "CRS: EPSG:4326" in result["exec_log"]
    assert "choropleth.png" in result["artifacts"]
    assert result["artifact_path"] and __import__("pathlib").Path(result["artifact_path"]).is_file()
    with zipfile.ZipFile(result["artifact_path"]) as zf:
        names = zf.namelist()
    assert any("choropleth.png" in n for n in names)
    assert any("操作说明.md" in n for n in names)


def test_gis_pipeline_ask_user_stops(tmp_path):
    """plan 信息不足 → 追问，流水线停在 plan"""
    agents = {
        "plan": _as_agent(_fake_plan_ask),
        "design": _as_agent(_fake_design),
        "codegen": _as_agent(_fake_codegen_good),
        "checker": _as_agent(_fake_checker_pass),
    }
    graph = create_gis_graph(agents, export_dir=str(tmp_path), project_id="t2")
    result = graph.invoke(_initial_state())

    assert result["ask_user"] == "数据里哪一列是省份？"
    assert result["current_stage"] == "plan"
    assert result.get("task_plan") is None


def test_gis_pipeline_checker_rewrite_twice(tmp_path):
    """校验 FAIL → 回 codegen 重写，最多 2 轮后仍 FAIL → export"""
    agents = {
        "plan": _as_agent(_fake_plan),
        "design": _as_agent(_fake_design),
        "codegen": _as_agent(_fake_codegen_good),
        "checker": _as_agent(_fake_checker_fail),
    }
    graph = create_gis_graph(agents, export_dir=str(tmp_path), project_id="t3")
    result = graph.invoke(_initial_state())

    assert result["rewrite_round"] == 2
    assert result["current_stage"] == "done"
    assert result["check_report"] == "- ❌ 图不可读\n整体结论: FAIL"


def test_gis_pipeline_rejects_os_remove(tmp_path):
    """AST 扫描拒绝 os.remove → exec_log 含拒绝信息，仍走重写闭环"""
    agents = {
        "plan": _as_agent(_fake_plan),
        "design": _as_agent(_fake_design),
        "codegen": _as_agent(_fake_codegen_evil),
        "checker": _as_agent(_fake_checker_fail),
    }
    graph = create_gis_graph(agents, export_dir=str(tmp_path), project_id="t4")
    result = graph.invoke(_initial_state())

    assert "安全扫描拒绝" in result["exec_log"]
    assert "os.remove" in result["exec_log"]
    assert result["rewrite_round"] == 2
