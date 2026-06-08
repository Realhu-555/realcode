"""LangGraph 状态图 — Agent 编排核心"""

from typing import Any

from langgraph.graph import END, StateGraph

from src.orchestrator.state import ProjectState


def create_graph(agents: dict[str, Any]) -> Any:
    """创建 Agent 编排图"""
    graph = StateGraph(ProjectState)

    graph.add_node("requirement", agents["requirement"].run)
    graph.add_node("architect", agents["architect"].run)
    graph.add_node("backend", agents["backend"].run)
    graph.add_node("frontend", agents["frontend"].run)
    graph.add_node("tester", agents["tester"].run)
    graph.add_node("deployer", agents["deployer"].run)

    graph.set_entry_point("requirement")

    graph.add_conditional_edges(
        "requirement",
        _route_after_requirement,
        {
            "ask_user": END,
            "continue": "architect",
        },
    )

    graph.add_edge("architect", "backend")
    graph.add_edge("architect", "frontend")
    graph.add_edge("backend", "tester")
    graph.add_edge("frontend", "tester")
    graph.add_edge("tester", "deployer")
    graph.add_edge("deployer", END)

    return graph.compile()


def _route_after_requirement(state: ProjectState) -> str:
    """判断需求分析后往哪走"""
    if state.get("ask_user"):
        return "ask_user"
    return "continue"
