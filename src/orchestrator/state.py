"""共享状态定义"""

import operator
from enum import Enum
from typing import Annotated, TypedDict


def _latest_stage(a: "Stage", b: "Stage") -> "Stage":
    """Reducer: 取最新写入的 stage 值（用于并行分支）"""
    return b


class Stage(str, Enum):
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DONE = "done"
    ERROR = "error"


class ProjectState(TypedDict):
    """多 Agent 共享的全局状态"""

    user_idea: str
    prd: str | None
    tech_plan: str | None
    frontend_code: str | None
    backend_code: str | None
    test_report: str | None
    zip_path: str | None
    current_stage: Annotated[Stage, _latest_stage]
    error_message: str | None
    messages: Annotated[list[dict], operator.add]
    ask_user: str | None
