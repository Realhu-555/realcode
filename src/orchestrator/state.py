"""共享状态定义"""

import operator
from enum import Enum
from typing import Annotated, TypedDict


def _latest_stage(a: "Stage", b: "Stage") -> "Stage":
    """Reducer: 取最新写入的 stage 值（用于并行分支）"""
    return b


class Stage(str, Enum):
    """原有研发流水线阶段（向后兼容）"""
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DONE = "done"
    ERROR = "error"


class ProjectState(TypedDict):
    """多 Agent 共享的全局状态（原有，向后兼容）"""

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


# ============================================================
# 营销内容平台状态（新增）
# ============================================================

class ContentStage(str, Enum):
    """营销内容流水线阶段"""
    STRATEGY = "strategy"       # 策略生成中
    CONFIRMING = "confirming"   # 等待用户确认策略
    GENERATING = "generating"   # 三渠道并行生成中
    REVIEW = "review"           # 审校中
    DONE = "done"               # 完成
    ERROR = "error"             # 出错


class ContentProjectState(TypedDict, total=False):
    """营销内容项目的共享状态

    从四个来源汇聚数据：
    - 用户输入（表单/自由模式）
    - 上游 Agent 产出（策略 → 渠道内容 → 审校报告）
    - 状态管理（阶段、错误、追问）
    - 记忆（品牌档案 ID）
    """

    # === 用户输入 ===
    input_mode: str                    # "form" | "free"
    product_name: str
    product_description: str
    target_users: str
    key_selling_points: list[str]      # 核心卖点
    brand_tone: str                    # 专业 / 轻松 / 极客
    competitors: list[str]             # 竞品
    user_idea: str                     # 自由模式下用户直接输入的完整描述

    # === Agent 产出 ===
    strategy: str | None               # 策略 Agent 输出
    gzh_content: str | None            # 公众号内容
    zhihu_content: str | None          # 知乎内容
    xhs_content: str | None            # 小红书内容
    review_report: str | None          # 审校报告

    # === 状态管理 ===
    current_stage: Annotated[ContentStage, _latest_stage]
    error_message: str | None
    ask_user: str | None               # 策略 Agent 追问用户的问题
    messages: Annotated[list[dict], operator.add]  # WebSocket 推送消息

    # === 记忆 ===
    brand_profile_id: str | None       # 关联的品牌档案 ID
