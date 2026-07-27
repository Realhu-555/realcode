"""审校 Agent —— 检查三篇渠道内容的品牌一致性和质量

使用 MiniMax 2.7，执行五项检查清单，给出整体评级。
"""

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry


class ShenjiaoAgent(BaseAgent):
    """品牌内容审核官 — MiniMax 2.7"""

    def __init__(self) -> None:
        super().__init__(name="shenjiao", tools=["content_read"])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        # 收集三篇渠道内容
        other_channel_contents = {}
        if state.get("gzh_content"):
            other_channel_contents["公众号"] = state["gzh_content"]
        if state.get("zhihu_content"):
            other_channel_contents["知乎"] = state["zhihu_content"]
        if state.get("xhs_content"):
            other_channel_contents["小红书"] = state["xhs_content"]

        ctx = PromptContext(
            agent_name="品牌内容审核官",
            tools=tool_registry.build_descriptions(self.tool_ids),
            product_name=state.get("product_name", ""),
            target_users=state.get("target_users", ""),
            key_selling_points=state.get("key_selling_points", []),
            brand_tone=state.get("brand_tone", "专业"),
            other_channel_contents=other_channel_contents,
        )

        template = renderer.load_template("shenjiao.md")
        system_prompt = renderer.render(template, ctx.to_template_vars())

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "请对以上三篇渠道内容进行全面的品牌一致性审校。",
            },
        ]

        report = self.llm.chat(messages, agent_type="shenjiao")

        return {
            **state,
            "review_report": report,
            "current_stage": "done",
            "messages": [{"from": "shenjiao", "type": "output", "content": report}],
        }
