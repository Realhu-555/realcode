"""状态机专项测试"""

import pytest

from src.agents.states import AgentEvent, AgentState, StateMachine


def test_state_machine_initial_state():
    """验证初始状态"""
    sm = StateMachine()
    assert sm.state == AgentState.IDLE
    assert sm.clarification_count == 0
    assert sm.retry_count == 0


def test_state_machine_transitions():
    """验证迁移表正确"""
    sm = StateMachine()
    assert sm.state == AgentState.IDLE

    sm.transition(AgentEvent.TASK_ASSIGNED)
    assert sm.state == AgentState.ANALYZING

    sm.transition(AgentEvent.PLAN_READY)
    assert sm.state == AgentState.PLANNING

    sm.transition(AgentEvent.PLAN_APPROVED)
    assert sm.state == AgentState.EXECUTING

    sm.transition(AgentEvent.EXECUTION_COMPLETE)
    assert sm.state == AgentState.REVIEWING

    sm.transition(AgentEvent.PRD_READY)
    assert sm.state == AgentState.COMPLETED


def test_clarification_limit():
    """追问超过 3 轮强制出 PRD"""
    sm = StateMachine(max_clarifications=3)
    sm.state = AgentState.ANALYZING

    for i in range(3):
        sm.clarification_count = i
        sm.transition(AgentEvent.NEEDS_CLARIFICATION)
        assert sm.state == AgentState.CLARIFYING
        sm.transition(AgentEvent.USER_REPLIED)
        assert sm.state == AgentState.ANALYZING

    # 第 3 轮结束
    sm.clarification_count = 3
    sm.transition(AgentEvent.NEEDS_CLARIFICATION)
    sm.transition(AgentEvent.MAX_CLARIFICATIONS_REACHED)
    assert sm.state == AgentState.COMPLETED


def test_timeout_triggers_prd():
    """等待超时强制出 PRD"""
    sm = StateMachine()
    sm.state = AgentState.WAITING_USER

    sm.transition(AgentEvent.WAITING_TIMEOUT)
    assert sm.state == AgentState.COMPLETED


def test_llm_retry_once():
    """LLM 报错重试 1 次"""
    sm = StateMachine(max_retries=1)
    sm.state = AgentState.ANALYZING
    sm.retry_count = 1  # Agent 自己管理 retry_count

    sm.transition(AgentEvent.LLM_ERROR)
    assert sm.state == AgentState.ERROR

    sm.transition(AgentEvent.MAX_RETRIES_REACHED)
    assert sm.state == AgentState.FATAL


def test_can_handle():
    """验证 can_handle 方法"""
    sm = StateMachine()
    assert sm.can_handle(AgentEvent.TASK_ASSIGNED)
    assert not sm.can_handle(AgentEvent.PRD_READY)


def test_is_terminal():
    """验证 is_terminal 属性"""
    sm = StateMachine()
    assert not sm.is_terminal

    sm.state = AgentState.COMPLETED
    assert sm.is_terminal

    sm.state = AgentState.FATAL
    assert sm.is_terminal


def test_reset():
    """验证 reset 方法"""
    sm = StateMachine()
    sm.state = AgentState.ANALYZING
    sm.clarification_count = 2
    sm.retry_count = 1
    sm.context["test"] = "value"

    sm.reset()

    assert sm.state == AgentState.IDLE
    assert sm.clarification_count == 0
    assert sm.retry_count == 0
    assert sm.context == {}


def test_unknown_transition_goes_fatal():
    """未知迁移进入 FATAL 状态"""
    sm = StateMachine()
    sm.state = AgentState.COMPLETED

    sm.transition(AgentEvent.TASK_ASSIGNED)
    assert sm.state == AgentState.FATAL
