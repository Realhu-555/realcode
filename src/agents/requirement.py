"""需求分析 Agent"""

import re

from src.agents.base import BaseAgent
from src.llm.prompts.requirement import REQUIREMENT_PROMPT
from src.llm.provider import LLMProvider

# 匹配多种 ASK_USER 格式：---ASK_USER: / [ASK_USER]...[/ASK_USER] / ASK_USER: 等
_ASK_PATTERN = re.compile(
    r"\[ASK_USER\]\s*(.*?)\s*\[/ASK_USER\]|"  # [ASK_USER]...[/ASK_USER]
    r"-{0,3}\s*ASK_USER[\s:]*(.*?)(?=-{3}|$)",  # ---ASK_USER: ... 或 ASK_USER: ...
    re.IGNORECASE | re.DOTALL,
)
# 检测追问特征：输出是提问而非 PRD（兜底检测）
_QUESTION_PATTERN = re.compile(
    r"([\?？])|"  # 任何位置有问号 → 很可能在提问
    r"(你是想|请[问选]|你[觉得认]|你希望|你打算|"  # 明确提问词
    r"还有其他|需要确认|需要.*[?？]|"  # 确认类/需要类
    r"^\s*(1\.|2\.|①|②|或者|还是|比如))",  # 列表选项
    re.MULTILINE | re.IGNORECASE,
)
_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """移除 MiniMax 的 <think> 推理块"""
    return _THINK_PATTERN.sub("", text).strip()


class RequirementAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="requirement", system_prompt=REQUIREMENT_PROMPT)
        self.llm = LLMProvider()
        self.round = 0

    def run(self, state: dict) -> dict:
        # 从历史消息中统计追问轮次
        prev_rounds = sum(
            1
            for m in state.get("messages", [])
            if m.get("from") == "requirement" and m.get("type") == "question"
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"用户想法：{state['user_idea']}"},
        ]

        if state.get("messages"):
            for msg in state["messages"]:
                if msg.get("from") == "requirement":
                    messages.append({"role": "assistant", "content": msg["content"]})
                elif msg.get("to") == "requirement":
                    messages.append({"role": "user", "content": msg["content"]})

        # 第1轮追问后强制产出 PRD，不允许继续追问
        # （MiniMax 不跟进对话，已回答过还重复问同一问题）
        if prev_rounds >= 1:
            messages[0] = {
                "role": "system",
                "content": self.system_prompt
                + "\n\n【重要】你已经追问了多轮，用户已经给出了充分的信息。现在必须直接产出 PRD 文档（用 ---PRD_START--- 格式），禁止再输出任何 ASK_USER 追问。如果你再追问，用户会不满意。",
            }

        response = self.llm.chat(messages, agent_type="requirement")
        clean_response = _strip_thinking(response)

        # 如果已有历史追问，强制作为 PRD 产出（即使 LLM 不听话输出 ASK_USER 也忽略）
        if prev_rounds >= 1:
            return {
                **state,
                "prd": clean_response,
                "ask_user": None,
                "current_stage": "architecture",
                "messages": [
                    {
                        "from": "requirement",
                        "to": "architect",
                        "type": "output",
                        "content": clean_response,
                    }
                ],
            }

        m = _ASK_PATTERN.search(clean_response)
        if m:
            # group(1): [ASK_USER]...[/ASK_USER] 格式
            # group(2): ---ASK_USER: 或 ASK_USER: 格式
            question = (m.group(1) or m.group(2) or clean_response[m.end() :]).strip()
            # 移除追问文本中残留的 ASK_USER 标记
            question = _ASK_PATTERN.sub("", question).strip()
            question = question.lstrip("- \t\n\r").strip()
            if len(question) > 5:  # 有效追问
                return {
                    **state,
                    "ask_user": question,
                    "current_stage": "requirement",
                    "messages": [
                        {
                            "from": "requirement",
                            "type": "question",
                            "content": question,
                        }
                    ],
                }

        # 兜底：检测没有标记但实际是追问的输出
        qm = _QUESTION_PATTERN.search(clean_response)
        if qm and len(clean_response) < 500:
            # 短文本 + 追问特征 → 很可能是提问而非 PRD
            return {
                **state,
                "ask_user": clean_response.strip(),
                "current_stage": "requirement",
                "messages": [
                    {
                        "from": "requirement",
                        "type": "question",
                        "content": clean_response.strip(),
                    }
                ],
            }

        return {
            **state,
            "prd": clean_response,
            "ask_user": None,
            "current_stage": "architecture",
            "messages": [
                {
                    "from": "requirement",
                    "to": "architect",
                    "type": "output",
                    "content": clean_response,
                }
            ],
        }
