"""LangGraph 状态图 — Agent 编排

编排流程：
  START → 策略 → [追问] → 三路并行生成 → 审校 → 导出 → END
"""

from typing import Any

from langgraph.graph import END, StateGraph

from src.orchestrator.state import ContentProjectState, ContentStage


def create_graph(agents: dict[str, Any]) -> Any:
    """创建营销内容 Agent 编排图

    节点：
    - celve: 策略分析（可追问）
    - gongzhonghao: 公众号长文
    - zhihu: 知乎回答
    - xiaohongshu: 小红书笔记
    - shenjiao: 审校报告
    - export: 导出（纯代码，无 LLM）
    """
    graph = StateGraph(ContentProjectState)

    graph.add_node("celve", agents["celve"].run)
    graph.add_node("gongzhonghao", agents["gongzhonghao"].run)
    graph.add_node("zhihu", agents["zhihu"].run)
    graph.add_node("xiaohongshu", agents["xiaohongshu"].run)
    graph.add_node("shenjiao", agents["shenjiao"].run)
    graph.add_node("export", agents["export"].run)

    graph.set_entry_point("celve")

    graph.add_conditional_edges(
        "celve",
        _route_after_celve,
        {"ask_user": END, "continue": "gongzhonghao"},
    )

    # 三路并行 fan-out
    graph.add_edge("celve", "zhihu")
    graph.add_edge("celve", "xiaohongshu")

    # 汇聚 → 审校
    graph.add_edge("gongzhonghao", "shenjiao")
    graph.add_edge("zhihu", "shenjiao")
    graph.add_edge("xiaohongshu", "shenjiao")

    # 审校 → 导出 → 结束
    graph.add_edge("shenjiao", "export")
    graph.add_edge("export", END)

    return graph.compile()


def _route_after_celve(state: ContentProjectState) -> str:
    if state.get("ask_user"):
        return "ask_user"
    return "continue"


CONTENT_STAGE_LABELS = {
    "strategy":   "策略分析中…",
    "confirming": "等待确认策略",
    "generating": "正在生成内容…",
    "review":     "审校中…",
    "done":       "完成！",
    "error":      "出错了",
}

CONTENT_STAGE_ORDER = ["strategy", "confirming", "generating", "review", "done"]
