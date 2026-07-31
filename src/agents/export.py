"""导出 Agent — content_list + project_save + Markdown 组装"""

from src.agents.base import BaseAgent
from src.tools.tool_tracker import call_tool_sync


class ExportAgent(BaseAgent):
    """内容导出 — 无需 LLM"""

    def __init__(self) -> None:
        super().__init__(name="export", tools=["content_list", "project_save"])

    def run(self, state: dict) -> dict:
        # 列出所有产出（记录工具调用轨迹）
        call_tool_sync("content_list", "export", state)

        sections = []
        product_name = state.get("product_name", "未命名产品")
        sections.append(f"# {product_name} — 营销内容包\n")

        if state.get("strategy"):
            sections.append("---\n\n## 📋 内容策略\n")
            sections.append(state["strategy"])
            sections.append("")

        if state.get("gzh_content"):
            sections.append("---\n\n## 📰 微信公众号\n")
            sections.append(state["gzh_content"])
            sections.append("")

        if state.get("zhihu_content"):
            sections.append("---\n\n## 💡 知乎\n")
            sections.append(state["zhihu_content"])
            sections.append("")

        if state.get("xhs_content"):
            sections.append("---\n\n## ✨ 小红书\n")
            sections.append(state["xhs_content"])
            sections.append("")

        if state.get("review_report"):
            sections.append("---\n\n## 🔍 审校报告\n")
            sections.append(state["review_report"])
            sections.append("")

        sections.append("---\n\n*由 素宣·墨坊 生成*\n")
        export_text = "\n".join(sections)

        # 持久化到 SQLite
        call_tool_sync("project_save", "export", {**state, "messages": []})

        return {
            **state,
            "messages": [{"from": "export", "type": "output", "content": export_text}],
        }
