"""LangGraph 状态图 — Agent 编排核心"""

from typing import Any

from langgraph.graph import END, StateGraph

from src.orchestrator.state import ProjectState, ContentProjectState, ContentStage


# ============================================================
# 原有研发流水线（向后兼容）
# ============================================================

def create_graph(agents: dict[str, Any]) -> Any:
    """创建 Agent 编排图（原有研发流水线）"""
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


# ============================================================
# 营销内容流水线（新增）
# ============================================================

def create_content_graph(agents: dict[str, Any]) -> Any:
    """创建营销内容 Agent 编排图

    编排流程：
    START → 策略 → [确认/追问] → 三路并行(公众号/知乎/小红书) → 审校 → END
    """
    graph = StateGraph(ContentProjectState)

    # 注册节点
    graph.add_node("celve", agents["celve"].run)
    graph.add_node("gongzhonghao", agents["gongzhonghao"].run)
    graph.add_node("zhihu", agents["zhihu"].run)
    graph.add_node("xiaohongshu", agents["xiaohongshu"].run)
    graph.add_node("shenjiao", agents["shenjiao"].run)

    graph.set_entry_point("celve")

    # 策略 → 确认还是追问
    graph.add_conditional_edges(
        "celve",
        _route_after_celve,
        {
            "ask_user": END,        # 暂停等待用户补充信息
            "continue": "gongzhonghao",
        },
    )

    # 三路并行生成（从策略确认后同时分发到三个渠道）
    graph.add_edge("celve", "zhihu")
    graph.add_edge("celve", "xiaohongshu")

    # 三个都完成后，汇聚到审校
    graph.add_edge("gongzhonghao", "shenjiao")
    graph.add_edge("zhihu", "shenjiao")
    graph.add_edge("xiaohongshu", "shenjiao")

    # 审校 → 结束
    graph.add_edge("shenjiao", END)

    return graph.compile()


def _route_after_celve(state: ContentProjectState) -> str:
    """判断策略 Agent 后往哪走"""
    if state.get("ask_user"):
        return "ask_user"
    return "continue"
