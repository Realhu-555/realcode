"""导出 Agent —— 收集所有内容，生成可导出格式

不需要 LLM，纯代码逻辑：
- 汇总策略 + 三篇内容 + 审校报告
- 生成格式化的 Markdown 导出文本
"""

from src.agents.base import BaseAgent


class ExportAgent(BaseAgent):
    """内容导出 —— 无需 LLM"""

    def __init__(self) -> None:
        super().__init__(name="export", tools=["content_list"])

    def run(self, state: dict) -> dict:
        sections = []

        product_name = state.get("product_name", "未命名产品")
        sections.append(f"# {product_name} — 营销内容包\n")

        # 策略
        if state.get("strategy"):
            sections.append("---\n\n## 📋 内容策略\n")
            sections.append(state["strategy"])
            sections.append("")

        # 公众号
        if state.get("gzh_content"):
            sections.append("---\n\n## 📰 微信公众号\n")
            sections.append(state["gzh_content"])
            sections.append("")

        # 知乎
        if state.get("zhihu_content"):
            sections.append("---\n\n## 💡 知乎\n")
            sections.append(state["zhihu_content"])
            sections.append("")

        # 小红书
        if state.get("xhs_content"):
            sections.append("---\n\n## ✨ 小红书\n")
            sections.append(state["xhs_content"])
            sections.append("")

        # 审校报告
        if state.get("review_report"):
            sections.append("---\n\n## 🔍 审校报告\n")
            sections.append(state["review_report"])
            sections.append("")

        sections.append("---\n\n*由 素宣·墨坊 生成*\n")

        export_text = "\n".join(sections)

        return {
            **state,
            "messages": [
                {
                    "from": "export",
                    "type": "output",
                    "content": export_text,
                }
            ],
        }
