"""统一 LLM Provider — DeepSeek V4 全部文本 Agent"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    if not text:
        return text
    return _THINK_PATTERN.sub("", text).strip()


class LLMProvider:
    """统一的 LLM 调用接口 — 全部 Agent 使用 DeepSeek V4"""

    MODEL_MAP = {
        "requirement": "deepseek:deepseek-v4-pro",
        "architect": "deepseek:deepseek-v4-pro",
        "backend": "deepseek:deepseek-v4-pro",
        "frontend": "deepseek:deepseek-v4-pro",
        "tester": "deepseek:deepseek-v4-pro",
        "deployer": "deepseek:deepseek-v4-pro",
        "documenter": "deepseek:deepseek-v4-pro",
        "celve": "deepseek:deepseek-v4-pro",
        "gongzhonghao": "deepseek:deepseek-v4-pro",
        "zhihu": "deepseek:deepseek-v4-pro",
        "xiaohongshu": "deepseek:deepseek-v4-pro",
        "shenjiao": "deepseek:deepseek-v4-pro",
        "export": "deepseek:deepseek-v4-pro",
    }

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "none")
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY") or "none",
            base_url="https://api.deepseek.com",
        )

    def chat(self, messages: list[dict], agent_type: str = "requirement") -> str:
        """发消息给 LLM，返回文本。空响应时重试一次。"""
        model_key = self.MODEL_MAP.get(agent_type, "deepseek:deepseek-v4-pro")
        provider, model = model_key.split(":", 1)
        content = self._call(messages, model, provider)
        if not content:
            content = self._call(messages, model, provider)
        return _strip_thinking(content)

    def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        agent_type: str = "celve",
    ) -> dict:
        """原生 function calling — 返回 DeepSeek 标准格式

        Returns:
            {"content": str | None, "tool_calls": [{"id":..., "function": {"name":..., "arguments":...}}]}
        """
        model_key = self.MODEL_MAP.get(agent_type, "deepseek:deepseek-v4-pro")
        provider, model = model_key.split(":", 1)
        client = self.deepseek_client if provider == "deepseek" else self.openai_client

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=4096,
            extra_body={"thinking": {"type": "disabled"}},
        )

        msg = response.choices[0].message
        result = {"content": _strip_thinking(msg.content or "")}

        if msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        return result

    def _call(self, messages, model, provider):
        client = self.deepseek_client if provider == "deepseek" else self.openai_client
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content
