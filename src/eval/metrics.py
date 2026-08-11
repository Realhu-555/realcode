"""评测指标计算

输入: list[RunResult]
输出: 聚合指标（成功率、工具调用正确率、延迟、成本、失败详情）
"""

from __future__ import annotations

from typing import Any

from src.eval.runner import RunResult


def _pct(values: list[float], q: float) -> float:
    """分位数（0-100）"""
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(len(s) * q / 100))
    return round(s[idx], 1)


def compute_metrics(results: list[RunResult]) -> dict[str, Any]:
    """聚合一次评测的所有运行结果"""
    total = len(results)
    if total == 0:
        return {"total_runs": 0}

    success_runs = [r for r in results if r.success]
    failed_runs = [r for r in results if not r.success]

    # ── 工具调用正确率（跨所有 run 聚合）──
    tool_total = 0
    tool_ok = 0
    for r in results:
        calls = (r.tool_stats or {}).get("calls", [])
        tool_total += len(calls)
        tool_ok += sum(1 for c in calls if c.get("success"))

    # ── 延迟 ──
    latencies = [r.latency_ms for r in results]

    # ── 成本 ──
    total_tokens = sum(r.cost_summary.get("total_tokens", 0) for r in results)
    total_cost = sum(r.cost_summary.get("estimated_cost_usd", 0) for r in results)

    # 按 Agent 聚合成本
    agent_cost: dict[str, dict[str, Any]] = {}
    for r in results:
        for agent, agg in (r.cost_summary.get("by_agent") or {}).items():
            entry = agent_cost.setdefault(agent, {"calls": 0, "total_tokens": 0, "failures": 0})
            entry["calls"] += agg.get("calls", 0)
            entry["total_tokens"] += agg.get("total_tokens", 0)
            entry["failures"] += agg.get("failures", 0)

    # ── 按场景拆分 ──
    per_scenario: dict[str, dict[str, Any]] = {}
    for r in results:
        s = per_scenario.setdefault(r.scenario, {"runs": 0, "success": 0, "latency_ms": []})
        s["runs"] += 1
        s["success"] += int(r.success)
        s["latency_ms"].append(r.latency_ms)

    return {
        "total_runs": total,
        "success_count": len(success_runs),
        "failed_count": len(failed_runs),
        "success_rate": round(len(success_runs) / total, 4),
        "tool_calls": tool_total,
        "tool_success": tool_ok,
        "tool_accuracy": round(tool_ok / tool_total, 4) if tool_total else 0.0,
        "latency_ms_avg": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
        "latency_ms_p50": _pct(latencies, 50),
        "latency_ms_p95": _pct(latencies, 95),
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(total_cost, 6),
        "cost_by_agent": agent_cost,
        "per_scenario": {
            name: {
                "runs": v["runs"],
                "success_rate": round(v["success"] / v["runs"], 4) if v["runs"] else 0.0,
                "latency_ms_avg": round(sum(v["latency_ms"]) / len(v["latency_ms"]), 1) if v["latency_ms"] else 0.0,
            }
            for name, v in per_scenario.items()
        },
        "failures": [
            {
                "scenario": r.scenario,
                "run_id": r.run_id,
                "error": r.error,
                "latency_ms": r.latency_ms,
            }
            for r in failed_runs if r.error
        ],
    }
