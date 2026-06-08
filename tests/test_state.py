"""共享状态单元测试"""

from src.orchestrator.state import ProjectState, Stage


def test_stage_enum_has_all_stages():
    """Stage 枚举包含所有阶段"""
    expected_stages = {
        "REQUIREMENT",
        "ARCHITECTURE",
        "FRONTEND",
        "BACKEND",
        "TESTING",
        "DEPLOYMENT",
        "DONE",
        "ERROR",
    }
    actual_stages = {s.name for s in Stage}
    assert actual_stages == expected_stages


def test_stage_values_are_strings():
    """Stage 枚举值为小写字符串"""
    assert Stage.REQUIREMENT.value == "requirement"
    assert Stage.ARCHITECTURE.value == "architecture"
    assert Stage.DONE.value == "done"


def test_project_state_structure():
    """ProjectState 包含所有必需字段"""
    state: ProjectState = {
        "user_idea": "test idea",
        "prd": None,
        "tech_plan": None,
        "frontend_code": None,
        "backend_code": None,
        "test_report": None,
        "zip_path": None,
        "current_stage": Stage.REQUIREMENT,
        "error_message": None,
        "messages": [],
        "ask_user": None,
    }
    assert state["user_idea"] == "test idea"
    assert state["current_stage"] == Stage.REQUIREMENT
    assert state["messages"] == []


def test_project_state_optional_fields_default_none():
    """可选字段默认为 None"""
    state: ProjectState = {
        "user_idea": "idea",
        "prd": None,
        "tech_plan": None,
        "frontend_code": None,
        "backend_code": None,
        "test_report": None,
        "zip_path": None,
        "current_stage": Stage.REQUIREMENT,
        "error_message": None,
        "messages": [],
        "ask_user": None,
    }
    assert state["prd"] is None
    assert state["tech_plan"] is None
    assert state["frontend_code"] is None


def test_messages_operator_add_concatenates():
    """messages 字段使用 operator.add 进行拼接"""
    state1: ProjectState = {
        "user_idea": "",
        "prd": None,
        "tech_plan": None,
        "frontend_code": None,
        "backend_code": None,
        "test_report": None,
        "zip_path": None,
        "current_stage": Stage.REQUIREMENT,
        "error_message": None,
        "messages": [{"role": "user", "content": "hello"}],
        "ask_user": None,
    }
    state2: ProjectState = {
        **state1,
        "messages": [{"role": "assistant", "content": "hi"}],
    }

    assert len(state1["messages"]) == 1
    assert len(state2["messages"]) == 1

    combined = state1["messages"] + state2["messages"]
    assert len(combined) == 2
    assert combined[0]["content"] == "hello"
    assert combined[1]["content"] == "hi"
