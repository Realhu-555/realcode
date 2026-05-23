"""LangGraph 状态图单元测试"""
import pytest
from src.orchestrator.state import ProjectState, Stage
from src.orchestrator.graph import create_graph, _route_after_requirement
from src.agents.base import BaseAgent


class DummyAgent(BaseAgent):
    """不调用 LLM 的桩 Agent"""

    def __init__(self, name: str, next_stage: Stage, output_key: str, output_value: str):
        super().__init__(name=name, system_prompt="test")
        self.next_stage = next_stage
        self.output_key = output_key
        self.output_value = output_value

    def run(self, state: dict) -> dict:
        return {
            self.output_key: self.output_value,
            "current_stage": self.next_stage,
            "messages": [{
                "from": self.name,
                "type": "output",
                "content": self.output_value,
            }],
        }


def make_state(**overrides) -> ProjectState:
    base: ProjectState = {
        "user_idea": "",
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
    base.update(overrides)  # type: ignore
    return base


def test_route_after_requirement_asks_user():
    """有 ask_user 时返回 'ask_user'"""
    state = make_state(ask_user="请详细描述一下你的需求")
    result = _route_after_requirement(state)
    assert result == "ask_user"


def test_route_after_requirement_continues():
    """无 ask_user 时返回 'continue'"""
    state = make_state(ask_user=None)
    result = _route_after_requirement(state)
    assert result == "continue"


def test_create_graph_has_all_nodes():
    """创建的状态图包含所有 Agent 节点"""
    agents = {
        "requirement": DummyAgent("requirement", Stage.ARCHITECTURE, "prd", "PRD内容"),
        "architect": DummyAgent("architect", Stage.BACKEND, "tech_plan", "方案"),
        "backend": DummyAgent("backend", Stage.TESTING, "backend_code", "代码"),
        "frontend": DummyAgent("frontend", Stage.TESTING, "frontend_code", "代码"),
        "tester": DummyAgent("tester", Stage.DEPLOYMENT, "test_report", "通过"),
        "deployer": DummyAgent("deployer", Stage.DONE, "zip_path", "/tmp/test.zip"),
    }
    graph = create_graph(agents)
    assert graph is not None


def test_graph_invoke_runs_requirement_produces_prd():
    """不含 ask_user 时，requirement 返回结果包含 PRD"""
    agents = {
        "requirement": DummyAgent("requirement", Stage.ARCHITECTURE, "prd", "PRD内容"),
        "architect": DummyAgent("architect", Stage.BACKEND, "tech_plan", "方案"),
        "backend": DummyAgent("backend", Stage.TESTING, "backend_code", "code"),
        "frontend": DummyAgent("frontend", Stage.TESTING, "frontend_code", "code"),
        "tester": DummyAgent("tester", Stage.DEPLOYMENT, "test_report", "pass"),
        "deployer": DummyAgent("deployer", Stage.DONE, "zip_path", "/tmp/x.zip"),
    }
    graph = create_graph(agents)

    initial_state: ProjectState = {
        "user_idea": "博客系统",
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

    result = graph.invoke(initial_state)
    assert result["prd"] == "PRD内容"
    assert result["tech_plan"] == "方案"
    assert result["backend_code"] == "code"
    assert result["frontend_code"] == "code"
    assert result["test_report"] == "pass"
    assert result["zip_path"] == "/tmp/x.zip"
    assert result["current_stage"] == Stage.DONE
