"""BaseAgent 单元测试"""
import pytest
from src.agents.base import BaseAgent


class FakeAgent(BaseAgent):
    """实现抽象方法的测试子类"""
    def run(self, state: dict) -> dict:
        return {**state, "result": "done"}


def test_base_agent_requires_run_implementation():
    """不能直接实例化 BaseAgent"""
    with pytest.raises(TypeError):
        BaseAgent(name="test", system_prompt="you are a test agent")  # type: ignore


def test_subclass_can_be_instantiated():
    """实现了 run() 的子类可以实例化"""
    agent = FakeAgent(name="fake", system_prompt="you are a fake agent")
    assert agent.name == "fake"
    assert agent.system_prompt == "you are a fake agent"


def test_subclass_run_returns_updated_state():
    """run() 返回更新后的状态"""
    agent = FakeAgent(name="fake", system_prompt="test")
    state = {"key": "value"}
    result = agent.run(state)

    assert result["key"] == "value"
    assert result["result"] == "done"
    assert result is not state  # 不修改原状态
