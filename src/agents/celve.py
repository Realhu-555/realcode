"""策略 Agent — ReAct 循环 + Tavily 真实搜索 + 轨迹追踪

设计模式：
1. 每轮 LLM 调用都可能触发工具调用（web_search）
2. 工具执行结果注入上下文，LLM 继续分析
3. 最多 3 轮（防止无限循环）
4. 全部轨迹记录到 TraceTracker
"""

import asyncio
import json
import re

from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry
from src.tools.protocol import ToolContext
from src.utils.trace import TraceTracker
from src.tools.tool_tracker import call_tool

# 匹配 LLM 输出的工具调用：<tool_call>{"name":"web_search","arguments":{"query":"..."}}</tool_call>
_TOOL_CALL_PATTERN = re.compile(
    r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL
)

# ASK_USER 检测
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
    """策略分析 Agent — ReAct + Tavily + Trace"""

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

        # 查品牌档案（记录工具调用轨迹）
        await call_tool("brand_lookup", "celve", state, product_name=state.get("product_name", ""))

        # 构建 context
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

        # ReAct 指令
        react_instruction = f"""
## 工具使用规则

你可以调用工具来搜索互联网信息。每次只能调用一个工具。

工具调用格式（严格 JSON）：
<tool_call>
{{"name": "web_search", "arguments": {{"query": "搜索关键词", "max_results": 3}}}}
</tool_call>

规则：
1. 先思考是否需要搜索，再决定是否调用工具
2. 最多 {self.MAX_REACT_ROUNDS} 轮工具调用
3. 搜索后，将结果融入策略分析，不要直接复制粘贴
4. 策略必须基于当前日期 {ctx.current_date} 的市场环境
5. 如果你已经掌握了足够信息，直接产出策略，不要再调用工具"""

        system_prompt += "\n" + react_instruction

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]

        user_content = self._build_user_message(state)
        messages.append({"role": "user", "content": user_content})

        # 历史对话
        self._inject_history(messages, state)

        # 强制产出模式
        force_output = prev_rounds >= 1
        if force_output:
            messages[0] = {
                "role": "system",
                "content": system_prompt
                + "\n\n【重要】用户已经补充了更多信息。现在必须直接输出完整的营销策略（Markdown），禁止追问。",
            }

        # === ReAct 循环 ===
        for round_idx in range(self.MAX_REACT_ROUNDS):
            response = self.llm.chat(messages, agent_type="celve")
            self.trace.llm_call(messages=messages, response=response, model="deepseek-v4-pro")

            # 解析最后一个 <tool_call> 块
            tool_calls = _TOOL_CALL_PATTERN.findall(response)
            if tool_calls and round_idx < self.MAX_REACT_ROUNDS - 1:
                for tc_json in tool_calls:
                    try:
                        tc = json.loads(tc_json.strip())
                        tool_name = tc.get("name", "")
                        tool_args = tc.get("arguments", {})

                        result = await call_tool(tool_name, "celve", state, **tool_args)
                        if result is None:
                            from src.tools.protocol import ToolResult
                            result = ToolResult(success=False, data=None, error=f"工具调用失败: {tool_name}")
                        self.trace.tool_call(
                            tool_id=tool_name,
                            params=tool_args,
                            result=result.data if result.success else None,
                            error=result.error if not result.success else None,
                        )

                        # 将工具结果注入对话
                        messages.append({"role": "assistant", "content": response})
                        messages.append({
                            "role": "user",
                            "content": f"[工具结果] {tool_name}:\n{json.dumps(result.data, ensure_ascii=False, indent=2)}\n\n请基于以上搜索结果继续分析，产出完整的营销策略。如果信息已足够，直接输出策略，不要再调用工具。",
                        })
                    except (json.JSONDecodeError, KeyError):
                        pass  # 格式错误，跳过该工具调用
            else:
                # 没有工具调用，或已达到最大轮数 → 结束循环
                break

        # === 解析最终输出 ===
        final_response = messages[-1]["content"] if messages[-1]["role"] == "assistant" else response

        self.trace.final(final_response)

        # 强制产出模式
        if force_output:
            return {
                **state,
                "strategy": final_response,
                "ask_user": None,
                "current_stage": "confirming",
                "messages": [{"from": "celve", "type": "output", "content": final_response}],
            }

        # ASK_USER 检测
        ask = _ASK_PATTERN.search(final_response)
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

        # 兜底追问
        qm = _QUESTION_PATTERN.search(final_response)
        if qm and len(final_response) < 500:
            return {
                **state,
                "ask_user": final_response.strip(),
                "current_stage": "strategy",
                "messages": [{"from": "celve", "type": "question", "content": final_response.strip()}],
            }

        return {
            **state,
            "strategy": final_response,
            "ask_user": None,
            "current_stage": "confirming",
            "messages": [{"from": "celve", "type": "output", "content": final_response}],
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
