"""共享 fixtures"""

import pytest
from src.orchestrator.state import Stage
from src.sandbox.executor import SandboxExecutor


@pytest.fixture
def sandbox():
    """创建已初始化的沙箱"""
    sb = SandboxExecutor()
    sb.create("test_project")
    yield sb
    sb.cleanup()


@pytest.fixture
def base_state():
    """基础 ProjectState"""
    return {
        "user_idea": "测试想法",
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
