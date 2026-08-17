"""营销内容平台共享状态定义"""

import operator
from enum import StrEnum
from typing import Annotated, TypedDict


def _latest_stage(a: "ContentStage", b: "ContentStage") -> "ContentStage":
    """Reducer: 取最新写入的 stage 值"""
    return b


class ContentStage(StrEnum):
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
    model_preference: str | None       # 用户选择的模型 ID（None = Agent 默认）

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


class GisStage(StrEnum):
    """GIS 智能操作流水线阶段"""
    PLAN = "plan"           # 任务规划（信息不足可追问）
    DESIGN = "design"       # 技术方案
    CODEGEN = "codegen"     # 脚本生成
    EXEC = "exec"           # 沙箱执行
    CHECK = "check"         # 结果校验
    EXPORT = "export"       # 成果打包
    DONE = "done"           # 完成
    ERROR = "error"         # 出错


def _latest_gis_stage(a: "GisStage", b: "GisStage") -> "GisStage":
    """Reducer: 取最新写入的 GIS stage 值"""
    return b


class GisProjectState(TypedDict, total=False):
    """GIS 智能操作项目的共享状态（SPEC v1.2 第 5 节）"""

    # === 用户输入 ===
    user_request: str                # 用户一句话需求
    data_file: str | None            # 上传/指定的数据文件路径
    data_schema: str | None          # data_inspect 预注入（字段清单+前5行样例+坐标列识别）
    model_preference: str | None     # 用户选择的模型 ID（None = Agent 默认）

    # === Agent 产出 ===
    task_plan: str | None            # plan 输出
    tech_plan: str | None            # design 输出
    script: str | None               # codegen 输出
    exec_log: str | None             # 沙箱 stdout/stderr
    artifacts: list[str]            # 沙箱产出文件列表（exec 节点写入，checker 用）
    check_report: str | None         # checker 输出
    artifact_path: str | None        # export 输出（zip 路径）

    # === 状态管理 ===
    current_stage: Annotated[GisStage, _latest_gis_stage]
    error_message: str | None
    ask_user: str | None
    messages: Annotated[list[dict], operator.add]
    rewrite_round: int | None        # 校验失败重写轮次（上限 2）

    # === 沙箱 ===
    workdir: str | None              # 当前沙箱目录（checker/export 需要）
