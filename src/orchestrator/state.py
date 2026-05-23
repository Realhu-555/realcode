"""共享状态定义"""
from typing import TypedDict, Optional, Annotated
from enum import Enum
import operator


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
    prd: Optional[str]
    tech_plan: Optional[str]
    frontend_code: Optional[str]
    backend_code: Optional[str]
    test_report: Optional[str]
    zip_path: Optional[str]
    current_stage: Annotated[Stage, _latest_stage]
    error_message: Optional[str]
    messages: Annotated[list[dict], operator.add]
    ask_user: Optional[str]
