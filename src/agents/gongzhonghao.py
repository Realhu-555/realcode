"""公众号 Agent — 深度长文 + 自动保存"""

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry
from src.tools.tool_tracker import call_tool_sync


class GongzhonghaoAgent(BaseAgent):
    """微信公众号内容创作者 — DeepSeek V4"""

    def __init__(self) -> None:
        super().__init__(name="gongzhonghao", tools=["content_save"])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        ctx = PromptContext(
            agent_name="公众号内容创作者",
            tools=tool_registry.build_descriptions(self.tool_ids),
            product_name=state.get("product_name", ""),
            product_description=state.get("product_description", ""),
            target_users=state.get("target_users", ""),
            key_selling_points=state.get("key_selling_points", []),
            brand_tone=state.get("brand_tone", "专业"),
            strategy=state.get("strategy"),
        )

        template = renderer.load_template("gzh.md")
        system_prompt = renderer.render(template, ctx.to_template_vars())

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请基于以上策略，为产品「{state.get('product_name', '')}」撰写一篇微信公众号深度长文。"},
        ]

        content = self.llm.chat(messages, agent_type="gongzhonghao")

        # 自动保存到草稿
        call_tool_sync("content_save", "gongzhonghao", state, channel="gongzhonghao", content=content)

        return {
            **state,
            "gzh_content": content,
            "messages": [{"from": "gongzhonghao", "type": "output", "content": content}],
        }
