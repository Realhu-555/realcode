"""评测报告生成

输出:
- summary.json: 全部指标（机器可读）
- report.md:   人类可读报告
"""

from __future__ import annotations

import json
from pathlib import Path

from src.eval.metrics import compute_metrics
from src.eval.runner import RunResult


def write_report(output_dir: Path, results: list[RunResult], meta: dict | None = None) -> Path:
    """生成评测报告，返回报告目录路径

    Args:
        output_dir: 输出目录（时间戳子目录会在外部创建）
        results: 本次评测的所有运行结果
        meta: 附加元信息（scenarios 列表、repeat 次数、时间等）
    """
    summary = compute_metrics(results)
    if meta:
        summary["meta"] = meta
    summary["per_run"] = [
        {
            "scenario": r.scenario,
            "run_id": r.run_id,
            "success": r.success,
            "latency_ms": r.latency_ms,
            "error": r.error,
            "stages": r.stages,
        }
        for r in results
    ]

    # summary.json
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # report.md
    lines = []
    lines.append("# 素宣 Agent 评测报告")
    lines.append("")
    if meta:
        lines.append(f"- 时间: {meta.get('time', '')}")
        lines.append(f"- 场景: {', '.join(meta.get('scenarios', []))}")
        lines.append(f"- 重复次数: {meta.get('repeat', 1)}")
        lines.append("")
    lines.append("## 总体指标")
    lines.append("")
    lines.append(f"- 运行总数: {summary['total_runs']}")
    lines.append(f"- 成功率: {summary['success_rate'] * 100:.1f}% ({summary['success_count']}/{summary['total_runs']})")
    lines.append(f"- 工具调用正确率: {summary['tool_accuracy'] * 100:.1f}% ({summary['tool_success']}/{summary['tool_calls']})")
    lines.append(f"- 平均耗时: {summary['latency_ms_avg']} ms | P50: {summary['latency_ms_p50']} ms | P95: {summary['latency_ms_p95']} ms")
    lines.append(f"- 总 Token: {summary['total_tokens']} | 估算成本: ${summary['estimated_cost_usd']}")
    lines.append("")
    lines.append("## 成本按 Agent 拆分")
    lines.append("")
    for agent, agg in summary.get("cost_by_agent", {}).items():
        lines.append(f"- {agent}: {agg['calls']} 次调用, {agg['total_tokens']} tokens, {agg['failures']} 次失败")
    lines.append("")
    lines.append("## 按场景")
    lines.append("")
    lines.append("| 场景 | 运行数 | 成功率 | 平均耗时(ms) |")
    lines.append("|------|-------:|-------:|------------:|")
    for name, v in summary.get("per_scenario", {}).items():
        lines.append(f"| {name} | {v['runs']} | {v['success_rate'] * 100:.1f}% | {v['latency_ms_avg']} |")
    lines.append("")
    lines.append("## 失败详情")
    lines.append("")
    failures = summary.get("failures", [])
    if not failures:
        lines.append("无失败运行。")
    else:
        for f in failures:
            lines.append(f"### {f['scenario']} ({f['run_id']})")
            lines.append("")
            err = f.get("error") or {}
            lines.append(f"- 阶段: {err.get('stage', '?')} | 节点: {err.get('node', '?')} | 类型: {err.get('error_type', '?')}")
            lines.append(f"- 消息: {err.get('message', '?')}")
            lines.append("")
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")

    return output_dir
