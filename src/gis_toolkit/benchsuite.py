"""评测套件 v2 — 面向 100 级任务集的 runner 与声明式断言。

设计（docs/GIS-Agent基准评测集扩展方案.md 口径扩展）：
- 任务 = request + data + 维度 + checks（声明式 DSL）；
- 断言覆盖：工具被调用、产物存在与内容合格、CSV 数值/行列、几何/行数、finish 收尾；
- 支持：多轮会话（dialog，测记忆/上下文）、审批模式（auto/readonly）、并发 worker、
  维度/数量过滤、JSON + Markdown 报告（任务通过率 / 审核通过率 / 维度汇总）。

用法：
    python -m src.gis_toolkit.benchsuite --limit 10              # 前 10 条（冒烟）
    python -m src.gis_toolkit.benchsuite --category chain        # 组合链路维度
    python -m src.gis_toolkit.benchsuite --workers 2             # 并发全量
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.approval import ApprovalGate
from src.gis_toolkit.engine import GisEngine
from src.gis_toolkit.session import GisSession

# ── 断言 DSL 编译 ────────────────────────────────────────


def _tools(result: dict) -> list[str]:
    return [t["tool"] for t in result.get("trajectory", [])]


def _tool_result_ok(result: dict) -> bool:
    """任务内不应有最终失败的工具步骤（允许中途失败后重试成功）。"""
    failed = [
        t for t in result.get("trajectory", []) if (t.get("result") or {}).get("status") == "error"
    ]
    return not failed


def _check_tool_in(result, tool) -> tuple[bool, str]:
    called = tool in _tools(result)
    return (called, f"轨迹含 {tool}: {called}")


def _check_tool_set(result, tools) -> tuple[bool, str]:
    got = set(_tools(result))
    missing = sorted(set(tools) - got)
    return (not missing, f"工具集合包含 {tools}：缺 {missing or '无'}")


def _check_output(result, suffix) -> tuple[bool, str]:
    outs = [o for o in result.get("outputs", []) if o.endswith(suffix)]
    return (bool(outs), f"产物含 {suffix}: {outs}")


def _check_finish_last(result) -> tuple[bool, str]:
    tools = _tools(result)
    ok = bool(tools) and tools[-1] == "finish"
    return (ok, f"最后一步是 finish: {tools[-1] if tools else '无'}")


def _check_png(engine, name, min_bytes) -> tuple[bool, str]:
    p = engine.out_dir / name
    size = p.stat().st_size if p.is_file() else 0
    return (size >= min_bytes, f"{name} 大小 {size}B >= {min_bytes}B")


def _check_file(engine, name) -> tuple[bool, str]:
    p = engine.out_dir / name
    return (p.is_file(), f"{name} 存在")


def _check_csv_rows(engine, name, expected) -> tuple[bool, str]:
    p = engine.out_dir / name
    if not p.is_file():
        return (False, f"{name} 不存在")
    rows = len(pd.read_csv(p))
    return (rows == expected, f"{name} 行数 {rows} == {expected}")


def _check_csv_rows_min(engine, name, expected) -> tuple[bool, str]:
    p = engine.out_dir / name
    if not p.is_file():
        return (False, f"{name} 不存在")
    rows = len(pd.read_csv(p))
    return (rows >= expected, f"{name} 行数 {rows} >= {expected}")


def _check_csv_total(engine, name, col, expected) -> tuple[bool, str]:
    p = engine.out_dir / name
    if not p.is_file():
        return (False, f"{name} 不存在")
    total = float(pd.read_csv(p)[col].sum())
    return (abs(total - expected) < 1e-6, f"{name} {col} 总和 {total:.3f} == {expected:.3f}")


def _check_csv_cols(engine, name, cols) -> tuple[bool, str]:
    p = engine.out_dir / name
    if not p.is_file():
        return (False, f"{name} 不存在")
    got = list(pd.read_csv(p).columns)
    ok = all(c in got for c in cols)
    return (ok, f"{name} 列 {got} 含 {cols}")


def compile_checks(task: dict) -> list[dict]:
    """把声明式 checks 编译为 [{"name","fn"}...]；默认追加 finish 收尾检查。"""
    compiled: list[dict] = []
    for c in task.get("checks", []):
        kind = c["kind"]
        name = c.get("name", kind)
        if kind == "tool_in":
            compiled.append(
                {"name": name, "fn": lambda r, e, t, _tool=c["tool"]: _check_tool_in(r, _tool)}
            )
        elif kind == "tool_set":
            compiled.append(
                {"name": name, "fn": lambda r, e, t, _tools=c["tools"]: _check_tool_set(r, _tools)}
            )
        elif kind == "output":
            compiled.append(
                {"name": name, "fn": lambda r, e, t, _s=c["suffix"]: _check_output(r, _s)}
            )
        elif kind == "final_nonempty":
            compiled.append(
                {
                    "name": name,
                    "fn": lambda r, e, t: (
                        bool((r.get("final") or "").strip()),
                        f"final 非空: {bool((r.get('final') or '').strip())}",
                    ),
                }
            )
        elif kind == "png_exists":

            def _png_fn(r, e, t, _task=c):
                return _check_png(e, _task["file"], int(_task.get("min", 8000)))

            compiled.append({"name": name, "fn": _png_fn})
        elif kind == "file_exists":
            compiled.append({"name": name, "fn": lambda r, e, t, _f=c["file"]: _check_file(e, _f)})
        elif kind == "csv_rows":
            compiled.append(
                {
                    "name": name,
                    "fn": lambda r, e, t, _f=c["file"], _n=c["value"]: _check_csv_rows(e, _f, _n),
                }
            )
        elif kind == "csv_rows_min":
            compiled.append(
                {
                    "name": name,
                    "fn": lambda r, e, t, _f=c["file"], _n=c["value"]: _check_csv_rows_min(
                        e, _f, _n
                    ),
                }
            )
        elif kind == "csv_total":
            compiled.append(
                {
                    "name": name,
                    "fn": lambda r, e, t, _f=c["file"], _c=c["col"], _v=c["value"]: (
                        _check_csv_total(e, _f, _c, _v)
                    ),
                }
            )
        elif kind == "csv_cols":
            compiled.append(
                {
                    "name": name,
                    "fn": lambda r, e, t, _f=c["file"], _c=c["cols"]: _check_csv_cols(e, _f, _c),
                }
            )
        else:
            raise ValueError(f"未知 check kind: {kind} (task={task.get('id')})")
    if task.get("require_finish", True):
        compiled.append({"name": "finish_last", "fn": lambda r, e, t: _check_finish_last(r)})
    return compiled


# ── 单任务执行 ────────────────────────────────────────


def _make_agent(task: dict, engine: GisEngine):
    mode = task.get("approval", "auto")
    gate = ApprovalGate(mode=mode) if task.get("dangerous", True) else None
    return GisToolAgent(
        engine=engine,
        max_steps=task.get("max_steps", 12),
        approval_gate=gate,
    )


def run_dialog(task: dict, engine: GisEngine):
    """多轮会话任务：逐轮 agent.run(session=...)，返回最后轮 result + 全轮轨迹合并。"""
    session = GisSession(
        task.get("id", "bench"),
        out_dir=engine.out_dir,
        permission_mode=task.get("approval", "auto"),
    )
    last = None
    merged_trajectory: list[dict] = []
    merged_outputs: list[str] = []
    for idx, turn in enumerate(task["dialog"]):
        last = _make_agent(task, session.engine).run(turn["user"], data_file=None, session=session)
        merged_trajectory.extend(last.get("trajectory", []))
        merged_outputs.extend(last.get("outputs", []))
        if idx == len(task["dialog"]) - 1:
            last["trajectory"] = merged_trajectory
            last["outputs"] = list(dict.fromkeys(merged_outputs))
    return last


def run_one(task: dict, out_root: Path) -> dict:
    out_dir = out_root / task["id"]
    engine = GisEngine(out_dir=str(out_dir), allowed_roots=["data"])
    started = time.time()
    if task.get("dialog"):
        result = run_dialog(task, engine)
    else:
        agent = _make_agent(task, engine)
        data_file = task.get("data") or (task.get("data_files") or [None])[0]
        result = agent.run(task["request"], data_file=data_file)
    duration_s = round(time.time() - started, 1)

    checks = []
    all_pass = True
    for c in compile_checks(task):
        try:
            ok, detail = c["fn"](result, engine, task)
        except Exception as exc:
            ok, detail = False, f"检查异常: {exc}"
        all_pass = all_pass and ok
        checks.append({"name": c["name"], "pass": ok, "detail": str(detail)})

    audit = result.get("audit_report")
    if audit is None:
        audit_pass, audit_verdict = True, "PASS"
        audit_reasons: list[str] = []
    else:
        audit_verdict = str(audit.get("verdict", "FAIL")).upper()
        audit_pass = audit_verdict == "PASS"
        audit_reasons = [str(x) for x in (audit.get("reasons") or [])]
    return {
        "task": task["id"],
        "category": task.get("category", ""),
        "dimension": task.get("dimension", ""),
        "pass": all_pass,
        "steps": result.get("steps", 0),
        "duration_s": duration_s,
        "timed_out": result.get("timed_out", False),
        "tools": [t["tool"] for t in result.get("trajectory", [])],
        "outputs": result.get("outputs", []),
        "checks": checks,
        "audit_pass": audit_pass,
        "audit_verdict": audit_verdict,
        "audit_reasons": audit_reasons,
        "error": result.get("error"),
    }


# ── 批量执行与报告 ──────────────────────────────────────


def run_suite(tasks: list[dict], out_root: Path, workers: int = 1) -> list[dict]:
    if workers <= 1:
        return [run_one(t, out_root) for t in tasks]
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(run_one, t, out_root): t for t in tasks}
        for future in as_completed(future_map):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append(
                    {
                        "task": future_map[future]["id"],
                        "category": future_map[future].get("category", ""),
                        "dimension": future_map[future].get("dimension", ""),
                        "pass": False,
                        "error": f"runner 异常: {exc}",
                    }
                )
    order = {t["id"]: i for i, t in enumerate(tasks)}
    results.sort(key=lambda r: order.get(r["task"], 0))
    return results


def _agg(results: list[dict]) -> dict:
    by_dim: dict[str, dict] = {}
    for r in results:
        dim = r.get("dimension") or r.get("category") or "other"
        d = by_dim.setdefault(dim, {"total": 0, "passed": 0, "audit": 0})
        d["total"] += 1
        d["passed"] += 1 if r.get("pass") else 0
        d["audit"] += 1 if r.get("audit_pass") else 0
    return by_dim


def write_reports(results: list[dict], out_dir: Path) -> dict:
    summary = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "total": len(results),
        "passed": sum(1 for r in results if r.get("pass")),
        "audit_passed": sum(1 for r in results if r.get("audit_pass")),
        "avg_steps": round(sum(r.get("steps", 0) for r in results) / max(1, len(results)), 1),
        "total_duration_s": round(sum(r.get("duration_s", 0) for r in results), 1),
        "dimensions": _agg(results),
        "results": results,
    }
    (out_dir / "report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        f"# GIS Agent 评测报告 {summary['timestamp']}",
        "",
        f"- 任务通过：**{summary['passed']}/{summary['total']}**",
        f"- 审核通过：**{summary['audit_passed']}/{summary['total']}**",
        f"- 平均步数：{summary['avg_steps']} ｜ 总耗时：{summary['total_duration_s']}s",
        "",
        "## 分维度",
        "",
        "| 维度 | 通过 | 审核 | 总数 |",
        "|---|---|---|---|",
    ]
    for dim, v in summary["dimensions"].items():
        lines.append(
            f"| {dim} | {v['passed']}/{v['total']} | {v['audit']}/{v['total']} | {v['total']} |"
        )
    lines += [
        "",
        "## 明细",
        "",
        "| 任务 | 维度 | 结果 | 审核 | 步数 | 耗时 | 工具 | 失败 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        mark = "PASS" if r.get("pass") else "FAIL"
        amark = "PASS" if r.get("audit_pass") else "FAIL"
        fail = ";".join(c["detail"] for c in r.get("checks", []) if not c["pass"]) or (
            r.get("error") or ""
        )
        lines.append(
            f"| {r['task']} | {r.get('dimension', '')} | {mark} | {amark} | "
            f"{r.get('steps', 0)} | {r.get('duration_s', '')} | {','.join(r.get('tools', []))[:60]} | {str(fail)[:120]} |"
        )
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def select_tasks(category: str | None, limit: int | None) -> list[dict]:
    from src.gis_toolkit.eval_tasks import build_tasks

    tasks = build_tasks()
    if category:
        tasks = [t for t in tasks if t.get("category") == category]
    if limit:
        tasks = tasks[:limit]
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="GIS Agent 评测套件 v2")
    parser.add_argument("--category", help="只跑某维度(category)")
    parser.add_argument("--limit", type=int, help="只跑前 N 条（冒烟）")
    parser.add_argument("--workers", type=int, default=1, help="并发 worker（出图类慎用>1）")
    parser.add_argument("--out", default="data/gis_bench_results")
    args = parser.parse_args()
    tasks = select_tasks(args.category, args.limit)
    print(f"评测任务 {len(tasks)} 条（workers={args.workers}）")
    out_root = Path(args.out) / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root.mkdir(parents=True, exist_ok=True)
    results = run_suite(tasks, out_root, workers=args.workers)
    summary = write_reports(results, out_root)
    print(
        f"通过 {summary['passed']}/{summary['total']}，审核 {summary['audit_passed']}/{summary['total']}"
    )
    for r in results:
        mark = "PASS" if r.get("pass") else "FAIL"
        print(
            f"  [{mark}] {r['task']:<28} dim={r.get('dimension', '')} steps={r.get('steps', 0)} "
            f"audit={r.get('audit_verdict', '')}"
        )
    print(f"报告: {out_root}/report.md")


if __name__ == "__main__":
    main()
