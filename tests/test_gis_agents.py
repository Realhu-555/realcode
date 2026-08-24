"""GIS Agent 单元测试 — plan / design / codegen / checker"""

from unittest.mock import MagicMock, patch

from src.agents.gis_common import (
    SCRIPT_PATTERN,
    extract_block,
    parse_ask_user,
    parse_pass_fail,
)

GIS_STATE = {
    "user_request": "把 GDP.csv 按省份做分级设色图",
    "data_file": "data/gdp.csv",
    "data_schema": "province: str\ngdp: int",
    "current_stage": "plan",
    "messages": [],
}


# ── gis_common 解析工具 ────────────────────────────────


def test_parse_ask_user():
    assert parse_ask_user("[ASK_USER]请提供省份字段名[/ASK_USER]") == "请提供省份字段名"
    assert parse_ask_user("没有追问，直接输出方案") is None


def test_extract_block_with_and_without_marker():
    assert (
        extract_block("a\n---SCRIPT_START---\ncode\n---SCRIPT_END---\nb", SCRIPT_PATTERN) == "code"
    )
    assert extract_block("裸文本", SCRIPT_PATTERN) == "裸文本"


def test_extract_block_start_without_end():
    """LLM 只输出 START 不输出 END 时，取 START 之后到结尾"""
    content = "说明文字\n---SCRIPT_START---\nimport pandas as pd\nprint(1)"
    assert extract_block(content, SCRIPT_PATTERN) == "import pandas as pd\nprint(1)"


def test_parse_pass_fail():
    assert parse_pass_fail("整体结论: PASS") is True
    assert parse_pass_fail("整体结论：FAIL\n建议修复") is False
    assert parse_pass_fail("没有结论关键字") is True  # 宽容降级


# ── PlanAgent ─────────────────────────────────────────


class TestPlanAgent:
    @patch("src.agents.gis_plan.LLMProvider")
    def test_run_returns_task_plan(self, mock_llm_cls: MagicMock):
        from src.agents.gis_plan import PlanAgent

        mock_llm_cls.return_value.chat.return_value = (
            "## 任务方案\n1. 读取 GDP.csv\n2. 按省份聚合\n3. 分级设色出图"
        )
        result = PlanAgent().run(dict(GIS_STATE))
        assert result["task_plan"] is not None
        assert result["ask_user"] is None
        assert result["current_stage"] == "design"

    @patch("src.agents.gis_plan.LLMProvider")
    def test_run_asks_when_vague(self, mock_llm_cls: MagicMock):
        from src.agents.gis_plan import PlanAgent

        mock_llm_cls.return_value.chat.return_value = "[ASK_USER]数据里哪一列是省份？[/ASK_USER]"
        result = PlanAgent().run(dict(GIS_STATE))
        assert result["ask_user"] == "数据里哪一列是省份？"
        assert result["current_stage"] == "plan"
        assert "task_plan" not in result or result["task_plan"] is None


# ── DesignAgent ───────────────────────────────────────


class TestDesignAgent:
    @patch("src.agents.gis_design.LLMProvider")
    def test_run_returns_tech_plan(self, mock_llm_cls: MagicMock):
        from src.agents.gis_design import DesignAgent

        mock_llm_cls.return_value.chat.return_value = (
            "---TECH_PLAN_START---\n坐标系: EPSG:4326\n输出: choropleth.png\n---TECH_PLAN_END---"
        )
        result = DesignAgent().run(dict(GIS_STATE))
        assert result["tech_plan"] == "坐标系: EPSG:4326\n输出: choropleth.png"
        assert result["current_stage"] == "codegen"


# ── CodegenAgent ──────────────────────────────────────


class TestCodegenAgent:
    @patch("src.agents.gis_codegen.LLMProvider")
    def test_run_extracts_script(self, mock_llm_cls: MagicMock):
        from src.agents.gis_codegen import CodegenAgent

        mock_llm_cls.return_value.chat.return_value = (
            "---SCRIPT_START---\nimport geopandas as gpd\nprint(1)\n---SCRIPT_END---"
        )
        result = CodegenAgent().run(dict(GIS_STATE))
        assert result["script"] == "import geopandas as gpd\nprint(1)"
        assert result["current_stage"] == "exec"


# ── CheckerAgent ──────────────────────────────────────


class TestCheckerAgent:
    @patch("src.agents.gis_checker.LLMProvider")
    def test_run_returns_report(self, mock_llm_cls: MagicMock):
        from src.agents.gis_checker import CheckerAgent

        mock_llm_cls.return_value.chat.return_value = "---CHECK_REPORT_START---\n- ✅ choropleth.png 存在\n整体结论: PASS\n---CHECK_REPORT_END---"
        state = {
            **GIS_STATE,
            "exec_log": "CRS: EPSG:4326\nROWS: 31",
            "artifacts": ["choropleth.png"],
        }
        result = CheckerAgent().run(state)
        assert "整体结论: PASS" in result["check_report"]
        assert result["current_stage"] == "check"
