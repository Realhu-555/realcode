"""知乎 Agent —— 撰写知乎专业回答（1000-2000 字）

使用 DeepSeek V4，侧重技术原理和实践案例。
"""

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry
from src.tools.tool_tracker import call_tool_sync


class ZhihuAgent(BaseAgent):
    """知乎专业领域回答者 — DeepSeek V4"""

    def __init__(self) -> None:
        super().__init__(name="zhihu", tools=["content_save"])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        ctx = PromptContext(
            agent_name="知乎专业回答者",
            tools=tool_registry.build_descriptions(self.tool_ids),
            product_name=state.get("product_name", ""),
            product_description=state.get("product_description", ""),
            target_users=state.get("target_users", ""),
            key_selling_points=state.get("key_selling_points", []),
            brand_tone=state.get("brand_tone", "专业"),
            strategy=state.get("strategy"),
        )

        template = renderer.load_template("zhihu.md")
        system_prompt = renderer.render(template, ctx.to_template_vars())

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请基于以上策略，为产品「{state.get('product_name', '')}」撰写一篇知乎专业回答。"},
        ]

        content = self.llm.chat(messages, agent_type="zhihu")

        call_tool_sync("content_save", "zhihu", state, channel="zhihu", content=content)

        return {
            **state,
            "zhihu_content": content,
            "messages": [{"from": "zhihu", "type": "output", "content": content}],
        }
