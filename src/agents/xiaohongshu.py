"""小红书 Agent —— 撰写小红书种草笔记（500-1000 字）

使用 MiniMax 2.7，侧重场景化描述和轻松种草风格。
"""

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry


class XiaohongshuAgent(BaseAgent):
    """小红书内容创作者 — MiniMax 2.7"""

    def __init__(self) -> None:
        super().__init__(name="xiaohongshu", tools=["content_save"])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        ctx = PromptContext(
            agent_name="小红书内容创作者",
            tools=tool_registry.build_descriptions(self.tool_ids),
            product_name=state.get("product_name", ""),
            product_description=state.get("product_description", ""),
            target_users=state.get("target_users", ""),
            key_selling_points=state.get("key_selling_points", []),
            brand_tone=state.get("brand_tone", "轻松"),
            strategy=state.get("strategy"),
        )

        template = renderer.load_template("xhs.md")
        system_prompt = renderer.render(template, ctx.to_template_vars())

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"请基于以上策略，为产品「{state.get('product_name', '')}」撰写一篇小红书种草笔记。",
            },
        ]

        content = self.llm.chat(messages, agent_type="xiaohongshu")

        return {
            **state,
            "xhs_content": content,
            "messages": [
                {"from": "xiaohongshu", "type": "output", "content": content}
            ],
        }
