"""Agent 状态机核心 — 可复用于所有 Agent"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class AgentState(Enum):
    """Agent 生命周期状态"""

    IDLE = auto()  # 等待任务
    ANALYZING = auto()  # 调 LLM 分析
    CLARIFYING = auto()  # 需要追问，发给用户
    WAITING_USER = auto()  # 等待用户回答
    PLANNING = auto()  # 制定计划（Plan-and-Execute）
    EXECUTING = auto()  # 执行计划
    REVIEWING = auto()  # 审查执行结果
    COMPLETED = auto()  # 完成，转下一阶段
    ERROR = auto()  # 异常终止（可重试）
    FATAL = auto()  # 不可恢复错误


class AgentEvent(Enum):
    """Agent 生命周期事件"""

    TASK_ASSIGNED = auto()
    LLM_RESPONDED = auto()
    NEEDS_CLARIFICATION = auto()  # LLM 输出含追问标记
    PLAN_READY = auto()  # 计划制定完成
    PLAN_APPROVED = auto()  # 计划已批准
    EXECUTION_COMPLETE = auto()  # 执行完成
    NEEDS_REVISION = auto()  # 需要修改
    PRD_READY = auto()  # LLM 输出了 PRD 内容
    USER_REPLIED = auto()  # 用户回答了追问
    MAX_RETRIES_REACHED = auto()  # 重试超过上限
    MAX_CLARIFICATIONS_REACHED = auto()  # 追问超过上限
    WAITING_TIMEOUT = auto()  # 用户等待超时
    LLM_ERROR = auto()
    FATAL_ERROR = auto()


@dataclass
class StateMachine:
    """
    状态机上下文。
    每个 Agent 实例持有一个 StateMachine，跟 ProjectState（跨 Agent 共享状态）分开。
    """

    state: AgentState = AgentState.IDLE
    clarification_count: int = 0
    retry_count: int = 0
    max_clarifications: int = 3  # 最多追问 3 轮
    max_retries: int = 1  # LLM 调用最多重试 1 次
    timeout_minutes: int = 30  # 用户等待超时 30 分钟
    last_question: Optional[str] = None  # 最近一次追问内容
    context: dict = field(default_factory=dict)  # 状态机内部上下文

    # 迁移表：(当前状态, 事件) → 下一状态
    _TRANSITIONS: dict[tuple[AgentState, AgentEvent], AgentState] = field(
        default_factory=lambda: {
            # 正常流程
            (AgentState.IDLE, AgentEvent.TASK_ASSIGNED): AgentState.ANALYZING,
            (AgentState.ANALYZING, AgentEvent.LLM_RESPONDED): AgentState.ANALYZING,
            (AgentState.ANALYZING, AgentEvent.NEEDS_CLARIFICATION): AgentState.CLARIFYING,
            (AgentState.ANALYZING, AgentEvent.PRD_READY): AgentState.COMPLETED,
            (AgentState.ANALYZING, AgentEvent.LLM_ERROR): AgentState.ERROR,
            (AgentState.ANALYZING, AgentEvent.FATAL_ERROR): AgentState.FATAL,
            # Plan-and-Execute 流程
            (AgentState.ANALYZING, AgentEvent.PLAN_READY): AgentState.PLANNING,
            (AgentState.PLANNING, AgentEvent.PLAN_APPROVED): AgentState.EXECUTING,
            (AgentState.EXECUTING, AgentEvent.EXECUTION_COMPLETE): AgentState.REVIEWING,
            (AgentState.EXECUTING, AgentEvent.NEEDS_REVISION): AgentState.PLANNING,
            (AgentState.REVIEWING, AgentEvent.PRD_READY): AgentState.COMPLETED,
            (AgentState.REVIEWING, AgentEvent.NEEDS_REVISION): AgentState.PLANNING,
            (AgentState.REVIEWING, AgentEvent.LLM_ERROR): AgentState.ERROR,
            # 追问流程
            (AgentState.CLARIFYING, AgentEvent.MAX_CLARIFICATIONS_REACHED): AgentState.COMPLETED,
            (AgentState.CLARIFYING, AgentEvent.USER_REPLIED): AgentState.ANALYZING,
            (AgentState.WAITING_USER, AgentEvent.USER_REPLIED): AgentState.ANALYZING,
            (AgentState.WAITING_USER, AgentEvent.WAITING_TIMEOUT): AgentState.COMPLETED,
            # 错误恢复
            (AgentState.ERROR, AgentEvent.MAX_RETRIES_REACHED): AgentState.FATAL,
            (AgentState.ERROR, AgentEvent.LLM_RESPONDED): AgentState.ANALYZING,
        }
    )

    def transition(self, event: AgentEvent) -> AgentState:
        """执行状态迁移。未知迁移 → FATAL。"""
        key = (self.state, event)
        if key in self._TRANSITIONS:
            self.state = self._TRANSITIONS[key]
        else:
            self.state = AgentState.FATAL
        return self.state

    def can_handle(self, event: AgentEvent) -> bool:
        """当前状态 + 事件是否构成合法迁移"""
        return (self.state, event) in self._TRANSITIONS

    @property
    def is_terminal(self) -> bool:
        return self.state in (AgentState.COMPLETED, AgentState.FATAL)

    def reset(self):
        self.state = AgentState.IDLE
        self.clarification_count = 0
        self.retry_count = 0
        self.context.clear()
        self.last_question = None
