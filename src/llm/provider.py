"""统一 LLM Provider — 多模型接入 + 路由 + Failover

v3 增强（SPEC model-routing）:
- 模型来自 config/models.yaml 注册表（改配置不改代码）
- 支持用户级 model_id 路由（用户选择 > Agent 默认）
- 主模型失败自动切换备用链（failover），事件记入成本统计
- 所有调用带指数退避重试（保留 v2 能力）

用法:
    provider = LLMProvider()
    text = provider.chat(messages, agent_type="celve")
    text = provider.chat(messages, agent_type="celve", model_id="minimax-2.7")
    result = provider.chat_with_tools(messages, tools, agent_type="celve")
"""

import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.llm.models import ModelConfig, load_registry
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
    """统一的 LLM 调用接口 — 注册表驱动 + 路由 + failover"""

    def __init__(self, registry=None) -> None:
        self.registry = registry or load_registry()
        self._clients: dict[str, OpenAI] = {}
        self._sync_pricing()

    def _sync_pricing(self) -> None:
        """把注册表价格同步给 cost_tracker（保留 default 兜底）"""
        pricing = {mid: cfg.pricing for mid, cfg in self.registry.models.items()}
        if pricing:
            pricing.setdefault("default", pricing.get("deepseek-v4-pro", {"input": 0.27, "output": 1.10}))
            cost_tracker.pricing = pricing

    # ── 客户端工厂 ──
    def _client_for(self, cfg: ModelConfig) -> OpenAI:
        """按配置创建/复用 OpenAI 兼容客户端（懒加载 + 缓存）"""
        if cfg.id not in self._clients:
            kwargs: dict = {"api_key": cfg.api_key}
            if cfg.base_url:
                kwargs["base_url"] = cfg.base_url
            self._clients[cfg.id] = OpenAI(**kwargs)
        return self._clients[cfg.id]

    # ── 路由 ──
    def _resolve_chain(self, model_id: str | None, agent_type: str) -> list[str]:
        """解析候选链：用户指定 > Agent 默认；再按 fallback 展开"""
        mid = model_id or self.registry.default_for(agent_type)
        if self.registry.get(mid) is None:
            # 未知 model_id：回退默认（SPEC AC5）
            mid = self.registry.default_for(agent_type)
        return self.registry.chain_for(mid)

    # ── 对外接口 ──
    def chat(
        self,
        messages: list[dict],
        agent_type: str = "requirement",
        model_id: str | None = None,
    ) -> str:
        """发消息给 LLM，返回文本。自动路由 + failover。空响应重试一次。"""
        chain = self._resolve_chain(model_id, agent_type)
        for mid in chain:
            cfg = self.registry.get(mid)
            if cfg is None:
                continue
            try:
                content, _, _ = self._call_with_retry(messages, cfg, agent_type)
                if not content:
                    content, _, _ = self._call_with_retry(messages, cfg, agent_type)
                return _strip_thinking(content)
            except Exception:
                _record_failover(agent_type, mid, chain)
                continue
        raise RuntimeError(f"所有候选模型调用失败: {chain}")

    def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        agent_type: str = "celve",
        model_id: str | None = None,
    ) -> dict:
        """原生 function calling — 返回 DeepSeek 标准格式

        Returns:
            {"content": str | None, "tool_calls": [{"id":..., "function": {"name":..., "arguments":...}}]}
        """
        chain = self._resolve_chain(model_id, agent_type)
        for mid in chain:
            cfg = self.registry.get(mid)
            if cfg is None:
                continue
            try:
                return self._call_tools_with_retry(messages, tools, cfg, agent_type)
            except Exception:
                _record_failover(agent_type, mid, chain)
                continue
        raise RuntimeError(f"所有候选模型调用失败: {chain}")

    # ── 内部调用（带重试 + 成本记录）──
    def _call_with_retry(
        self,
        messages: list[dict],
        cfg: ModelConfig,
        agent_type: str,
    ) -> tuple[str | None, int, int]:
        """普通文本调用，返回 (content, prompt_tokens, completion_tokens)"""
        t0 = time.time()
        content, prompt_tokens, completion_tokens = retry_call(
            self._call,
            messages,
            cfg,
            max_retries=RETRY_MAX_ATTEMPTS,
            base_delay=RETRY_BASE_DELAY,
            max_delay=RETRY_MAX_DELAY,
            retryable=is_retryable_openai_error,
            on_retry=_on_retry(agent_type, cfg.id),
        )
        cost_tracker.record(
            agent_type=agent_type,
            model=cfg.id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=(time.time() - t0) * 1000,
        )
        return content, prompt_tokens, completion_tokens

    def _call_tools_with_retry(
        self,
        messages: list[dict],
        tools: list[dict],
        cfg: ModelConfig,
        agent_type: str,
    ) -> dict:
        """工具调用（原生 function calling），带重试 + 成本记录"""
        client = self._client_for(cfg)
        t0 = time.time()
        response = retry_call(
            client.chat.completions.create,
            model=cfg.model,
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
            on_retry=_on_retry(agent_type, cfg.id),
        )
        usage = getattr(response, "usage", None)
        cost_tracker.record(
            agent_type=agent_type,
            model=cfg.id,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            duration_ms=(time.time() - t0) * 1000,
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

    def _call(self, messages: list[dict], cfg: ModelConfig):
        client = self._client_for(cfg)
        response = client.chat.completions.create(
            model=cfg.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            extra_body={"thinking": {"type": "disabled"}},
        )
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        return response.choices[0].message.content, prompt_tokens, completion_tokens


def _on_retry(agent_type: str, model_id: str):
    """构造重试回调：把重试事件记入成本统计（失败记录）"""

    def _cb(attempt: int, delay: float, exc: Exception) -> None:
        cost_tracker.record(
            agent_type=agent_type,
            model=model_id,
            prompt_tokens=0,
            completion_tokens=0,
            duration_ms=delay * 1000,
            success=False,
            error_type=f"retry_{attempt + 1}:{type(exc).__name__}",
        )

    return _cb


def _record_failover(agent_type: str, failed_model: str, chain: list[str]) -> None:
    """记录 failover 事件（切到下一个候选）"""
    idx = chain.index(failed_model) if failed_model in chain else 0
    next_model = chain[idx + 1] if idx + 1 < len(chain) else "None"
    cost_tracker.record(
        agent_type=agent_type,
        model=failed_model,
        prompt_tokens=0,
        completion_tokens=0,
        duration_ms=0,
        success=False,
        error_type=f"failover_to:{next_model}",
    )
