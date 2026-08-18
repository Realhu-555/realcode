"""GIS 共享状态测试"""

from src.orchestrator.state import (
    GisProjectState,
    GisStage,
    _latest_gis_stage,
)


def test_gis_stage_values():
    """GisStage 枚举值覆盖流水线全阶段"""
    assert [s.value for s in GisStage] == [
        "plan", "design", "codegen", "exec", "check", "export", "done", "error",
    ]


def test_gis_state_accepts_user_input():
    """GisProjectState 可承载用户输入 + 预注入 schema"""
    state: GisProjectState = {
        "user_request": "把 GDP.csv 按省份做分级设色图",
        "data_file": "data/gdp.csv",
        "data_schema": "province: str\ngdp: int",
        "current_stage": GisStage.PLAN,
        "messages": [],
    }
    assert state["current_stage"] == GisStage.PLAN
    assert state["data_schema"] is not None


def test_gis_stage_reducer_keeps_latest():
    """current_stage reducer 取最新值"""
    assert _latest_gis_stage(GisStage.PLAN, GisStage.CODEGEN) == GisStage.CODEGEN
