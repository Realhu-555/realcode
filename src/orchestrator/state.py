"""营销内容平台共享状态定义"""

import operator
from enum import Enum
from typing import Annotated, TypedDict


def _latest_stage(a: "ContentStage", b: "ContentStage") -> "ContentStage":
    """Reducer: 取最新写入的 stage 值"""
    return b


class ContentStage(str, Enum):
    """营销内容流水线阶段"""
    STRATEGY = "strategy"       # 策略生成中
    CONFIRMING = "confirming"   # 等待用户确认策略
    GENERATING = "generating"   # 三渠道并行生成中
    REVIEW = "review"           # 审校中
    DONE = "done"               # 完成
    ERROR = "error"             # 出错


class ContentProjectState(TypedDict, total=False):
    """营销内容项目的共享状态"""

    # === 用户输入 ===
    input_mode: str                    # "form" | "free"
    product_name: str
    product_description: str
    target_users: str
    key_selling_points: list[str]
    brand_tone: str
    competitors: list[str]
    user_idea: str
    image_urls: list[str]              # 上传图片（base64 data URLs）

    # === Agent 产出 ===
    strategy: str | None
    gzh_content: str | None
    zhihu_content: str | None
    xhs_content: str | None
    review_report: str | None

    # === 状态管理 ===
    current_stage: Annotated[ContentStage, _latest_stage]
    error_message: str | None
    ask_user: str | None
    messages: Annotated[list[dict], operator.add]

    # === 记忆 ===
    brand_profile_id: str | None


class OutputArtifact(TypedDict, total=False):
    """Agent 产出物（供 ApprovalGate 使用）"""
    full_content: str
    summary: str
    version: int
