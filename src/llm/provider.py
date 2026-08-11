"""统一 LLM Provider — DeepSeek V4 全部文本 Agent

v2 增强:
- 所有 LLM 调用自动接入指数退避重试（网络抖动/5xx/限流自动恢复）
- 每次调用记录 Token 成本到 CostTracker（可观测性）
"""

import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.observability.cost_tracker import cost_tracker
from src.recovery.retry import is_retryable_openai_error, retry_call

_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)

# 重试配置（PRD FR3.1）
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 8.0


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
        content, _, _ = self._call_with_retry(messages, model, provider, agent_type)
        if not content:
            content, _, _ = self._call_with_retry(messages, model, provider, agent_type)
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

        t0 = time.time()
        response = retry_call(
            client.chat.completions.create,
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=4096,
            extra_body={"thinking": {"type": "disabled"}},
            max_retries=RETRY_MAX_ATTEMPTS,
            base_delay=RETRY_BASE_DELAY,
            max_delay=RETRY_MAX_DELAY,
            retryable=is_retryable_openai_error,
            on_retry=_on_retry(agent_type, model),
        )
        dur_ms = (time.time() - t0) * 1000

        usage = getattr(response, "usage", None)
        cost_tracker.record(
            agent_type=agent_type,
            model=f"{provider}:{model}",
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            duration_ms=dur_ms,
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

    def _call_with_retry(
        self,
        messages: list[dict],
        model: str,
        provider: str,
        agent_type: str,
    ) -> tuple[str | None, int, int]:
        """带重试的普通 LLM 调用，返回 (content, prompt_tokens, completion_tokens)"""
        t0 = time.time()
        content, prompt_tokens, completion_tokens = retry_call(
            self._call,
            messages,
            model,
            provider,
            max_retries=RETRY_MAX_ATTEMPTS,
            base_delay=RETRY_BASE_DELAY,
            max_delay=RETRY_MAX_DELAY,
            retryable=is_retryable_openai_error,
            on_retry=_on_retry(agent_type, f"{provider}:{model}"),
        )
        dur_ms = (time.time() - t0) * 1000
        cost_tracker.record(
            agent_type=agent_type,
            model=f"{provider}:{model}",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=dur_ms,
        )
        return content, prompt_tokens, completion_tokens

    def _call(self, messages, model, provider):
        client = self.deepseek_client if provider == "deepseek" else self.openai_client
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        return response.choices[0].message.content, prompt_tokens, completion_tokens


def _on_retry(agent_type: str, model: str):
    """构造重试回调：把重试事件记入成本统计（失败记录）"""

    def _cb(attempt: int, delay: float, exc: Exception) -> None:
        cost_tracker.record(
            agent_type=agent_type,
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            duration_ms=delay * 1000,
            success=False,
            error_type=f"retry_{attempt + 1}:{type(exc).__name__}",
        )

    return _cb
