"""模型注册表加载器

从 config/models.yaml 加载模型配置，支持：
- 新增/修改模型只改 YAML 不改代码
- 按 Agent 类型取默认模型
- 取 failover 候选链
- 缺配置文件时回退内置默认（deepseek-v4-pro）

用法:
    from src.llm.models import load_registry
    registry = load_registry()
    cfg = registry.get("deepseek-v4-pro")
    chain = registry.chain_for("deepseek-v4-pro")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "models.yaml"

# 内置默认：YAML 缺失/损坏时兜底
BUILTIN_MODELS: dict[str, dict[str, Any]] = {
    "deepseek-v4-pro": {
        "label": "DeepSeek V4 Pro",
        "provider": "openai-compatible",
        "model": "deepseek-v4-pro",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "input_price_per_m": 0.27,
        "output_price_per_m": 1.10,
        "capabilities": ["chat", "tools"],
    },
}
BUILTIN_AGENT_DEFAULTS: dict[str, str] = {
    "celve": "deepseek-v4-pro",
    "gongzhonghao": "deepseek-v4-pro",
    "zhihu": "deepseek-v4-pro",
    "xiaohongshu": "deepseek-v4-pro",
    "shenjiao": "deepseek-v4-pro",
    "export": "deepseek-v4-pro",
    "plan": "deepseek-v4-pro",
    "design": "deepseek-v4-pro",
    "codegen": "deepseek-v4-pro",
    "checker": "deepseek-v4-pro",
}
BUILTIN_FALLBACK: dict[str, list[str]] = {}


@dataclass
class ModelConfig:
    """单个模型配置"""

    id: str
    label: str
    provider: str
    model: str
    base_url: str | None = None
    api_key_env: str | None = None
    input_price_per_m: float = 0.0
    output_price_per_m: float = 0.0
    capabilities: list[str] = field(default_factory=lambda: ["chat", "tools"])

    @property
    def api_key(self) -> str:
        return os.getenv(self.api_key_env or "", "") or "none"

    @property
    def pricing(self) -> dict[str, float]:
        return {"input": self.input_price_per_m, "output": self.output_price_per_m}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "capabilities": self.capabilities,
        }


class ModelRegistry:
    """模型注册表：模型配置 + Agent 默认路由 + failover 链"""

    def __init__(
        self,
        models: dict[str, ModelConfig],
        agent_defaults: dict[str, str],
        fallback_chains: dict[str, list[str]],
    ) -> None:
        self.models = models
        self.agent_defaults = agent_defaults
        self.fallback_chains = fallback_chains

    def get(self, model_id: str) -> ModelConfig | None:
        return self.models.get(model_id)

    def default_for(self, agent_type: str) -> str:
        return self.agent_defaults.get(agent_type, "deepseek-v4-pro")

    def chain_for(self, model_id: str) -> list[str]:
        """返回候选链 [model_id, backup...]，未知 model_id 时只有自己"""
        chain = self.fallback_chains.get(model_id, [])
        if model_id not in chain:
            chain = [model_id] + chain
        return chain

    def list_models(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.models.values()]

    def default_model_id(self) -> str:
        return "deepseek-v4-pro" if "deepseek-v4-pro" in self.models else next(iter(self.models))


def _parse_models(data: dict[str, Any]) -> tuple[dict[str, ModelConfig], dict[str, str], dict[str, list[str]]]:
    """从 YAML dict 解析出三件套"""
    models: dict[str, ModelConfig] = {}
    for mid, cfg in (data.get("models") or {}).items():
        models[mid] = ModelConfig(
            id=mid,
            label=cfg.get("label", mid),
            provider=cfg.get("provider", "openai-compatible"),
            model=cfg.get("model", mid),
            base_url=cfg.get("base_url"),
            api_key_env=cfg.get("api_key_env"),
            input_price_per_m=float(cfg.get("input_price_per_m", 0.0)),
            output_price_per_m=float(cfg.get("output_price_per_m", 0.0)),
            capabilities=list(cfg.get("capabilities", ["chat", "tools"])),
        )
    agent_defaults = dict(data.get("agent_defaults") or {})
    fallback = {k: list(v) for k, v in (data.get("fallback_chains") or {}).items()}
    return models, agent_defaults, fallback


def _builtin_registry() -> ModelRegistry:
    models, defaults, fallback = _parse_models({"models": BUILTIN_MODELS})
    defaults.update(BUILTIN_AGENT_DEFAULTS)
    fallback.update(BUILTIN_FALLBACK)
    return ModelRegistry(models, defaults, fallback)


@lru_cache(maxsize=1)
def load_registry() -> ModelRegistry:
    """加载模型注册表（带缓存）。YAML 缺失/损坏时回退内置默认。"""
    if yaml is None or not CONFIG_PATH.exists():
        return _builtin_registry()
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        models, defaults, fallback = _parse_models(data)
        if not models:
            return _builtin_registry()
        return ModelRegistry(models, defaults, fallback)
    except Exception:
        return _builtin_registry()


def reload_registry() -> ModelRegistry:
    """强制重新加载（测试/热更新用）"""
    load_registry.cache_clear()
    return load_registry()
