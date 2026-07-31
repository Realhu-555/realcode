"""策略 Agent — 原生 function calling + Tavily 真实搜索 + 轨迹追踪

使用 DeepSeek 原生 tools 参数，不再用 XML 标签解析。
轨迹格式: OpenAI 标准 tool_calls 数组，可直接在工具中可视化。
"""

import asyncio
import json

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry
from src.tools.protocol import ToolContext
from src.utils.trace import TraceTracker
from src.tools.tool_tracker import call_tool

# ASK_USER 检测（追问逻辑不变）
import re
_ASK_PATTERN = re.compile(
    r"\[ASK_USER\]\s*(.*?)\s*\[/ASK_USER\]|"
    r"-{0,3}\s*ASK_USER[\s:]*(.*?)(?=-{3}|$)",
    re.IGNORECASE | re.DOTALL,
)
_QUESTION_PATTERN = re.compile(
    r"([?？])|(你是想|请[问选]|你[觉得认]|你希望|你打算|还有其他|需要确认|"
    r"需要.*[?？]|^\s*(1\.|2\.|①|②|或者|还是|比如))",
    re.MULTILINE | re.IGNORECASE,
)


class CelveAgent(BaseAgent):
    """策略分析 Agent — 原生 function calling"""

    MAX_REACT_ROUNDS = 3

    def __init__(self, trace: TraceTracker | None = None) -> None:
        super().__init__(name="celve", tools=["web_search", "brand_lookup"])
        self.llm = LLMProvider()
        self.trace = trace or TraceTracker()

    def run(self, state: dict) -> dict:
        return asyncio.run(self._run_async(state))

    async def _run_async(self, state: dict) -> dict:
        prev_rounds = sum(
            1 for m in state.get("messages", [])
            if m.get("from") == "celve" and m.get("type") == "question"
        )

        # 查品牌档案
        await call_tool("brand_lookup", "celve", state, product_name=state.get("product_name", ""))

        # 构建 system prompt（纯文本，不含工具使用规则——原生 function calling 不需要）
        ctx = PromptContext(
            agent_name="营销策略专家",
            tools=tool_registry.build_descriptions(self.tool_ids),
            product_name=state.get("product_name", ""),
            product_description=state.get("product_description", ""),
            target_users=state.get("target_users", ""),
            key_selling_points=state.get("key_selling_points", []),
            brand_tone=state.get("brand_tone", "专业"),
            competitors=state.get("competitors", []),
        )

        template = renderer.load_template("celve.md")
        system_prompt = renderer.render(template, ctx.to_template_vars())

        # 原生 function calling tools schema
        openai_tools = tool_registry.build_openai_tools(self.tool_ids)

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": self._build_user_message(state)})
        self._inject_history(messages, state)

        # 强制产出模式
        force_output = prev_rounds >= 1
        if force_output:
            messages[0] = {
                "role": "system",
                "content": system_prompt
                + "\n\n【重要】用户已经补充了更多信息。现在必须直接输出完整的营销策略（Markdown），禁止追问。",
            }

        # ===== 原生 function calling ReAct 循环 =====
        for round_idx in range(self.MAX_REACT_ROUNDS):
            if force_output and round_idx > 0:
                break  # 强制产出模式只调一次，不循环

            resp = self.llm.chat_with_tools(messages, tools=openai_tools, agent_type="celve")

            content = resp.get("content", "")
            tool_calls = resp.get("tool_calls") or []

            self.trace.llm_call(
                messages=messages,
                tools=openai_tools,
                content=content,
                tool_calls=tool_calls,
                model="deepseek-v4-pro",
            )

            if not tool_calls or round_idx >= self.MAX_REACT_ROUNDS - 1:
                # LLM 直接回答 → 结束
                messages.append({"role": "assistant", "content": content})
                break

            # 执行所有 tool_calls，收集结果
            results = []
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                try:
                    func_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                result = await call_tool(func_name, "celve", state, **func_args)

                results.append({
                    "id": tc["id"],
                    "name": func_name,
                    "arguments": func_args,
                    "result": result.data if result and result.success else None,
                    "error": result.error if result and not result.success else None,
                })

                # 注入工具结果到对话（OpenAI 标准格式）
                messages.append({
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": [tc],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(
                        result.data if result and result.success else {"error": result.error if result else "unknown"},
                        ensure_ascii=False,
                    ),
                })

            self.trace.tool_results(results)

        # ===== 解析最终输出 =====
        final_messages = [m for m in messages if m["role"] == "assistant" and m.get("content")]
        final_response = final_messages[-1]["content"] if final_messages else content

        self.trace.final(final_response)

        return self._build_result(state, final_response, force_output)

    def _build_result(self, state: dict, response: str, force_output: bool) -> dict:
        if force_output:
            return {
                **state,
                "strategy": response,
                "ask_user": None,
                "current_stage": "confirming",
                "messages": [{"from": "celve", "type": "output", "content": response}],
            }

        ask = _ASK_PATTERN.search(response)
        if ask:
            question = (ask.group(1) or ask.group(2) or "").strip()
            question = _ASK_PATTERN.sub("", question).strip().lstrip("- \t\n\r")
            if len(question) > 5:
                return {
                    **state,
                    "ask_user": question,
                    "current_stage": "strategy",
                    "messages": [{"from": "celve", "type": "question", "content": question}],
                }

        qm = _QUESTION_PATTERN.search(response)
        if qm and len(response) < 500:
            return {
                **state,
                "ask_user": response.strip(),
                "current_stage": "strategy",
                "messages": [{"from": "celve", "type": "question", "content": response.strip()}],
            }

        return {
            **state,
            "strategy": response,
            "ask_user": None,
            "current_stage": "confirming",
            "messages": [{"from": "celve", "type": "output", "content": response}],
        }

    def _build_user_message(self, state: dict) -> str:
        if state.get("input_mode") == "free":
            return f"用户需求：{state.get('user_idea', '')}"
        return f"请为以下产品制定营销内容策略：{state.get('product_name', '')}"

    def _inject_history(self, messages: list, state: dict):
        if state.get("messages"):
            for msg in state["messages"]:
                if msg.get("from") == "celve":
                    messages.append({"role": "assistant", "content": msg["content"]})
                elif msg.get("to") == "celve":
                    messages.append({"role": "user", "content": msg["content"]})
