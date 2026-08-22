"""失败定位：从 State 和轨迹中提取结构化失败信息

评测/可观测性的核心能力之一：失败时能指出"哪个阶段、哪个节点、
哪个工具、什么类型的错误"，而不是只有一句 error_message。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FailureInfo:
    """结构化失败信息"""

    stage: str                       # ContentStage 字符串：strategy/generating/review...
    node: str                        # 出错的 Agent 节点：celve/gongzhonghao/zhihu/...
    error_type: str                  # llm_call / tool_call / timeout / unknown
    message: str                     # 错误消息
    tool_name: str | None = None     # 涉及的工具（tool_call 时）
    trace_snippet: str | None = None  # 轨迹片段（关键上下文）

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "node": self.node,
            "error_type": self.error_type,
            "message": self.message[:500],
            "tool_name": self.tool_name,
            "trace_snippet": (self.trace_snippet or "")[:1000],
        }


def classify_error(exc: Exception) -> str:
    """按异常类型粗分类错误"""
    name = type(exc).__name__
    msg = str(exc).lower()
    if "timeout" in name.lower() or "timeout" in msg:
        return "timeout"
    if "tool" in name.lower() or "tool_call" in msg:
        return "tool_call"
    if "api" in name.lower() or "connection" in msg or "network" in msg:
        return "llm_call"
    if "authentication" in msg or "401" in msg or "403" in msg:
        return "auth"
    if "rate" in msg or "429" in msg:
        return "rate_limit"
    return "unknown"


def extract_failure(
    state: dict[str, Any],
    node: str,
    exc: Exception,
    stage: str = "",
) -> FailureInfo:
    """从异常提取 FailureInfo

    Args:
        state: 失败时的共享状态
        node: 出错的节点（Agent 名）
        exc: 捕获的异常
        stage: 阶段名（未传时从 state 推断）
    """
    stage = stage or str(state.get("current_stage", ""))
    return FailureInfo(
        stage=stage,
        node=node,
        error_type=classify_error(exc),
        message=str(exc),
    )
