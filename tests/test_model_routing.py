"""多模型接入与动态切换 单元测试（SPEC model-routing）

覆盖:
- AC1: 注册表加载 3 模型
- AC2/AC3: 路由（用户 model_id > Agent 默认）
- AC4: failover 自动切换
- AC5: 未知 model_id 回退默认
"""

import pytest
from src.llm.models import load_registry
from src.llm.provider import LLMProvider

# ── 注册表（AC1）──

def test_registry_loads_models():
    registry = load_registry()
    assert registry.get("deepseek-v4-pro") is not None
    assert registry.get("minimax-2.7") is not None
    assert registry.get("openrouter-auto") is not None


def test_registry_agent_defaults():
    registry = load_registry()
    assert registry.default_for("celve") == "deepseek-v4-pro"
    assert registry.default_for("unknown_agent") == "deepseek-v4-pro"


def test_registry_chain():
    registry = load_registry()
    chain = registry.chain_for("deepseek-v4-pro")
    assert chain[0] == "deepseek-v4-pro"
    assert "minimax-2.7" in chain  # 备用链存在


def test_registry_model_config_pricing():
    registry = load_registry()
    cfg = registry.get("deepseek-v4-pro")
    assert cfg.pricing["input"] > 0
    assert cfg.capabilities == ["chat", "tools"]


# ── 路由（AC2/AC3/AC5）──

def test_resolve_chain_default():
    p = LLMProvider()
    chain = p._resolve_chain(None, "celve")
    assert chain[0] == "deepseek-v4-pro"


def test_resolve_chain_user_preference():
    p = LLMProvider()
    chain = p._resolve_chain("minimax-2.7", "celve")
    assert chain[0] == "minimax-2.7"


def test_resolve_chain_unknown_falls_back():
    """AC5: 未知 model_id 回退默认，不崩溃"""
    p = LLMProvider()
    chain = p._resolve_chain("no-such-model", "celve")
    assert chain[0] == "deepseek-v4-pro"


# ── Failover（AC4）──

class _FakeLLM(LLMProvider):
    """模拟主模型失败、备用成功的 Provider"""

    def __init__(self, fail_first: int = 1):
        super().__init__()
        self.calls: list[str] = []
        self.fail_first = fail_first

    def _call_with_retry(self, messages, cfg, agent_type):
        self.calls.append(cfg.id)
        if len(self.calls) <= self.fail_first:
            raise ConnectionError(f"{cfg.id} 暂时不可用")
        return "备用模型返回的结果", 10, 20


def test_failover_switches_to_backup():
    """主模型失败 → 自动切备用，调用成功"""
    p = _FakeLLM(fail_first=1)
    result = p.chat([{"role": "user", "content": "hi"}], agent_type="celve")
    assert result == "备用模型返回的结果"
    assert p.calls[0] == "deepseek-v4-pro"   # 先试主模型
    assert len(p.calls) >= 2                 # 然后切了备用


def test_failover_all_fail_raises():
    """所有候选都失败 → 抛错"""
    p = _FakeLLM(fail_first=99)
    with pytest.raises(RuntimeError):
        p.chat([{"role": "user", "content": "hi"}], agent_type="celve")
    assert len(p.calls) >= 2  # 主 + 至少一个备用都试过


def test_failover_records_events():
    """failover 事件记入成本统计（可追溯）"""
    from src.observability.cost_tracker import cost_tracker
    cost_tracker.reset()
    p = _FakeLLM(fail_first=1)
    p.chat([{"role": "user", "content": "hi"}], agent_type="celve")
    error_types = [f.get("error_type") for f in cost_tracker.failures()]
    assert any("failover_to" in (e or "") for e in error_types)
