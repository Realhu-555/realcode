"""审校 Agent — 五项检查清单 + content_read + project_save"""

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry
from src.tools.tool_tracker import call_tool_sync


class ShenjiaoAgent(BaseAgent):
    """品牌内容审核官 — DeepSeek V4"""

    def __init__(self) -> None:
        super().__init__(name="shenjiao", tools=["content_read"])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        # 通过 content_read 工具读取三篇内容（记录工具调用轨迹）
        for ch in ["gongzhonghao", "zhihu", "xiaohongshu"]:
            call_tool_sync("content_read", "shenjiao", state, channel=ch)

        # 收集三篇渠道内容（从 state 直接拿，content_read 已验证 key 映射）
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
            {"role": "user", "content": "请对以上三篇渠道内容进行全面的品牌一致性审校。"},
        ]

        report = self.llm.chat(messages, agent_type="shenjiao",
                               model_id=state.get("model_preference"))

        # 持久化到 SQLite
        call_tool_sync("project_save", "shenjiao", {**state, "review_report": report})

        return {
            **state,
            "review_report": report,
            "current_stage": "done",
            "messages": [{"from": "shenjiao", "type": "output", "content": report}],
        }
