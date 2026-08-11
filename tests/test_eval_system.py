"""评测系统 + 错误恢复 单元测试

覆盖 PRD P0 验收：
- AC3: LLM 调用失败自动重试（网络抖动/5xx 重试，4xx 不重试）
- AC1: 评测场景加载、状态构建、指标计算
"""

import pytest

from src.eval.metrics import compute_metrics
from src.eval.runner import RunResult, build_state, load_scenarios
from src.recovery.retry import retry_call


# ── 错误恢复（AC3）──

class _BadRequest(Exception):
    status_code = 400


class _ServerError(Exception):
    status_code = 500


def test_retry_success_after_transient_errors():
    """网络抖动 2 次后成功 → 自动重试"""
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("connection reset")
        return "ok"

    result = retry_call(flaky, max_retries=3, base_delay=0.01, max_delay=0.05)
    assert result == "ok"
    assert len(calls) == 3


def test_retry_never_retries_4xx():
    """4xx 业务错误 → 不重试"""
    calls = []

    def bad():
        calls.append(1)
        raise _BadRequest("bad params")

    with pytest.raises(_BadRequest):
        retry_call(bad, max_retries=3, base_delay=0.01,
                   max_delay=0.05, retryable=lambda e: False)
    assert len(calls) == 1


def test_retry_on_5xx():
    """5xx 服务端错误 → 重试后成功"""
    calls = []

    def srv():
        calls.append(1)
        if len(calls) < 2:
            raise _ServerError("internal error")
        return "ok"

    result = retry_call(srv, max_retries=3, base_delay=0.01, max_delay=0.05)
    assert result == "ok"
    assert len(calls) == 2


def test_retry_exhausts_and_raises():
    """重试耗尽后抛出最后一次异常"""
    calls = []

    def always_fail():
        calls.append(1)
        raise ConnectionError("still down")

    with pytest.raises(ConnectionError):
        retry_call(always_fail, max_retries=2, base_delay=0.01, max_delay=0.05)
    assert len(calls) == 3  # 1 次原始调用 + 2 次重试


# ── 评测系统（AC1）──

def test_load_scenarios_all():
    scenarios = load_scenarios()
    assert len(scenarios) >= 5
    names = [s["name"] for s in scenarios]
    assert "devgate_form" in names
    assert "zhuazhua_free" in names


def test_load_scenarios_filter():
    scenarios = load_scenarios(["devgate_form"])
    assert len(scenarios) == 1
    assert scenarios[0]["name"] == "devgate_form"


def test_build_state():
    sc = load_scenarios(["mianmian_form"])[0]
    state = build_state(sc)
    assert state["product_name"] == "眠眠"
    assert state["current_stage"] == "strategy"
    assert state["strategy"] is None
    assert state["messages"] == []


def _fake_result(scenario, success, latency, tool_ok, tool_total, tokens, error=None):
    return RunResult(
        scenario=scenario,
        run_id="test",
        success=success,
        latency_ms=latency,
        tool_stats={"calls": [{"success": True}] * tool_ok + [{"success": False}] * (tool_total - tool_ok)},
        cost_summary={"total_tokens": tokens, "estimated_cost_usd": tokens / 1e6,
                      "by_agent": {"celve": {"calls": 1, "total_tokens": tokens, "failures": 0}}},
        error=error,
    )


def test_compute_metrics_basic():
    results = [
        _fake_result("a", True, 100.0, 2, 2, 1000),
        _fake_result("b", False, 200.0, 1, 2, 2000,
                     error={"stage": "strategy", "node": "celve",
                            "error_type": "unknown", "message": "boom"}),
    ]
    m = compute_metrics(results)
    assert m["total_runs"] == 2
    assert m["success_rate"] == 0.5
    assert m["tool_accuracy"] == 0.75
    assert m["latency_ms_avg"] == 150.0
    assert m["total_tokens"] == 3000
    assert len(m["failures"]) == 1
    assert m["failures"][0]["error"]["node"] == "celve"
    assert m["per_scenario"]["a"]["success_rate"] == 1.0
