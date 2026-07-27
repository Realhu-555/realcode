"""策略 Agent —— 分析产品信息，输出内容营销策略

设计模式（参考 RequirementAgent）：
- 使用 PromptContext + Jinja2 模板渲染 system prompt
- 支持 ASK_USER 追问（信息不足时暂停等待用户补充）
- 追问一轮后强制产出策略
"""

import re

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry
from src.vision import describe_images

# 匹配 ASK_USER 格式
_ASK_PATTERN = re.compile(
    r"\[ASK_USER\]\s*(.*?)\s*\[/ASK_USER\]|"
    r"-{0,3}\s*ASK_USER[\s:]*(.*?)(?=-{3}|$)",
    re.IGNORECASE | re.DOTALL,
)

# 兜底：检测短文本 + 提问特征 → 可能是在追问而非产出策略
_QUESTION_PATTERN = re.compile(
    r"([?？])|"
    r"(你是想|请[问选]|你[觉得认]|你希望|你打算|"
    r"还有其他|需要确认|需要.*[?？]|"
    r"^\s*(1\.|2\.|①|②|或者|还是|比如))",
    re.MULTILINE | re.IGNORECASE,
)


import asyncio

class CelveAgent(BaseAgent):
    """策略分析 Agent — DeepSeek V4"""

    def __init__(self) -> None:
        super().__init__(name="celve", tools=["web_search"])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        return asyncio.run(self._run_async(state))

    async def _run_async(self, state: dict) -> dict:
        # 统计历史追问轮次
        prev_rounds = sum(
            1
            for m in state.get("messages", [])
            if m.get("from") == "celve" and m.get("type") == "question"
        )

        # 图片视觉理解（MiMo V2.5）
        image_descriptions = ""
        image_urls = state.get("image_urls", [])
        if image_urls:
            image_descriptions = await describe_images(
                image_urls,
                state.get("product_name", ""),
            )

        # 构建 PromptContext
        ctx = PromptContext(
            agent_name="营销策略专家",
            tools=tool_registry.build_descriptions(self.tool_ids),
            product_name=state.get("product_name", ""),
            product_description=state.get("product_description", ""),
            target_users=state.get("target_users", ""),
            key_selling_points=state.get("key_selling_points", []),
            brand_tone=state.get("brand_tone", "专业"),
            competitors=state.get("competitors", []),
            image_descriptions=image_descriptions,
        )

        template = renderer.load_template("celve.md")
        system_prompt = renderer.render(template, ctx.to_template_vars())

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]

        if state.get("input_mode") == "free":
            messages.append(
                {"role": "user", "content": f"用户需求：{state.get('user_idea', '')}"}
            )
        else:
            messages.append(
                {
                    "role": "user",
                    "content": f"请为以下产品制定营销内容策略：{state.get('product_name', '')}",
                }
            )

        # 历史对话注入
        if state.get("messages"):
            for msg in state["messages"]:
                if msg.get("from") == "celve":
                    messages.append({"role": "assistant", "content": msg["content"]})
                elif msg.get("to") == "celve":
                    messages.append({"role": "user", "content": msg["content"]})

        # 追问超过 1 轮，强制产出策略
        if prev_rounds >= 1:
            messages[0] = {
                "role": "system",
                "content": system_prompt
                + "\n\n【重要】用户已经补充了更多信息。现在必须直接输出完整的营销策略（用 Markdown 格式），禁止再问任何问题。",
            }

        response = self.llm.chat(messages, agent_type="celve")

        # 强制产出模式
        if prev_rounds >= 1:
            return {
                **state,
                "strategy": response,
                "ask_user": None,
                "current_stage": "confirming",
                "messages": [{"from": "celve", "type": "output", "content": response}],
            }

        # ASK_USER 检测
        m = _ASK_PATTERN.search(response)
        if m:
            question = (m.group(1) or m.group(2) or "").strip()
            question = _ASK_PATTERN.sub("", question).strip().lstrip("- \t\n\r")
            if len(question) > 5:
                return {
                    **state,
                    "ask_user": question,
                    "current_stage": "strategy",
                    "messages": [
                        {"from": "celve", "type": "question", "content": question}
                    ],
                }

        # 兜底追问检测
        qm = _QUESTION_PATTERN.search(response)
        if qm and len(response) < 500:
            return {
                **state,
                "ask_user": response.strip(),
                "current_stage": "strategy",
                "messages": [
                    {"from": "celve", "type": "question", "content": response.strip()}
                ],
            }

        # 正常产出策略
        return {
            **state,
            "strategy": response,
            "ask_user": None,
            "current_stage": "confirming",
            "messages": [{"from": "celve", "type": "output", "content": response}],
        }
