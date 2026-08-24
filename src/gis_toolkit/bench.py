"""GIS 助手基准任务集评测（设计文档 8 节级别 3）

每个任务 = 用户请求 + 数据文件 + 一组规则检查；评测器跑真实 GisToolAgent，
对轨迹与产物做断言，输出 pass/fail 报告。

用法：
    python -m src.gis_toolkit.bench                # 跑全部任务（真实 LLM）
    python -m src.gis_toolkit.bench --task choropleth
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.engine import GisEngine

DATA_ROOT = Path("data")
BENCH_DATA = DATA_ROOT / "gis_bench_data"
GDP_CSV = "data/gis_demo/gdp_demo.csv"
CITIES_GEOJSON = str(BENCH_DATA / "cities.geojson")


# ── 检查函数：fn(result, engine, task) -> (bool, detail) ────────────────


def _tool_called(result: dict, tool: str) -> tuple[bool, str]:
    called = [t["tool"] for t in result["trajectory"]]
    return (tool in called, f"轨迹含 {tool}: {tool in called}")


def _finish_called(result: dict) -> tuple[bool, str]:
    tools = [t["tool"] for t in result["trajectory"]]
    return (
        bool(tools) and tools[-1] == "finish",
        f"最后一步是 finish: {tools[-1] if tools else None}",
    )


def _has_output(result: dict, suffix: str) -> tuple[bool, str]:
    outs = [o for o in result["outputs"] if o.endswith(suffix)]
    return (bool(outs), f"outputs 含 {suffix}: {outs}")


def _file_exists(engine: GisEngine, name: str) -> tuple[bool, str]:
    p = engine.out_dir / name
    return (p.is_file(), f"{name} 存在: {p.is_file()}")


def _png_size_ok(engine: GisEngine, name: str, min_bytes: int) -> tuple[bool, str]:
    p = engine.out_dir / name
    size = p.stat().st_size if p.is_file() else 0
    return (size >= min_bytes, f"{name} 大小 {size}B >= {min_bytes}B")


def _csv_rows(engine: GisEngine, name: str, expected: int) -> tuple[bool, str]:
    p = engine.out_dir / name
    if not p.is_file():
        return (False, f"{name} 不存在")
    rows = len(pd.read_csv(p))
    return (rows == expected, f"{name} 行数 {rows} == {expected}")


def _csv_columns(engine: GisEngine, name: str, cols: list[str]) -> tuple[bool, str]:
    p = engine.out_dir / name
    if not p.is_file():
        return (False, f"{name} 不存在")
    got = list(pd.read_csv(p).columns)
    ok = all(c in got for c in cols)
    return (ok, f"{name} 列 {got} 包含 {cols}")


def _csv_sum_total(engine: GisEngine, name: str, col: str, expected: float) -> tuple[bool, str]:
    p = engine.out_dir / name
    if not p.is_file():
        return (False, f"{name} 不存在")
    total = float(pd.read_csv(p)[col].sum())
    return (abs(total - expected) < 1e-6, f"{name} {col} 总和 {total:.2f} == {expected:.2f}")


def _buffer_area_grew(engine: GisEngine) -> tuple[bool, str]:
    if engine._layer is None:
        return (False, "无图层")
    g = engine._layer.geometry
    area = float(g.area.sum())
    return (area > 0, f"缓冲区后总面积 {area:.2f} > 0（点→圆）")


# ── 任务定义 ─────────────────────────────────────────


def _gdp_total() -> float:
    df = pd.read_csv(GDP_CSV)
    return float(df["gdp"].sum())


TASKS: list[dict] = [
    {
        "id": "choropleth",
        "request": "把 gdp_demo.csv 按 gdp 字段做分级设色图，保存为 choropleth.png",
        "data": GDP_CSV,
        "checks": [
            {"name": "tool_called_choropleth", "fn": lambda r, e, t: _tool_called(r, "choropleth")},
            {"name": "output_png", "fn": lambda r, e, t: _has_output(r, ".png")},
            {"name": "png_size", "fn": lambda r, e, t: _png_size_ok(e, "choropleth.png", 10_000)},
            {"name": "finish_called", "fn": lambda r, e, t: _finish_called(r)},
        ],
    },
    {
        "id": "summarize",
        "request": "按省份分组统计 gdp 总和，导出 summary.csv",
        "data": GDP_CSV,
        "checks": [
            {"name": "tool_called_summarize", "fn": lambda r, e, t: _tool_called(r, "summarize")},
            {"name": "output_csv", "fn": lambda r, e, t: _has_output(r, ".csv")},
            {"name": "csv_rows_31", "fn": lambda r, e, t: _csv_rows(e, "summary.csv", 31)},
            {
                "name": "csv_columns",
                "fn": lambda r, e, t: _csv_columns(e, "summary.csv", ["province", "gdp"]),
            },
            {
                "name": "gdp_total",
                "fn": lambda r, e, t: _csv_sum_total(e, "summary.csv", "gdp", _gdp_total()),
            },
            {"name": "finish_called", "fn": lambda r, e, t: _finish_called(r)},
        ],
    },
    {
        "id": "buffer",
        "request": "对 cities.geojson 的所有城市点做 1 度缓冲区，并导出 buffered.geojson",
        "data": CITIES_GEOJSON,
        "checks": [
            {"name": "tool_called_buffer", "fn": lambda r, e, t: _tool_called(r, "buffer")},
            {"name": "area_grew", "fn": lambda r, e, t: _buffer_area_grew(e)},
            {"name": "output_geojson", "fn": lambda r, e, t: _has_output(r, ".geojson")},
            {"name": "finish_called", "fn": lambda r, e, t: _finish_called(r)},
        ],
    },
    {
        "id": "scatter",
        "request": "对 gdp_demo.csv 的 lon 和 lat 两个字段画散点图，保存为 scatter.png",
        "data": GDP_CSV,
        "checks": [
            {"name": "tool_called_scatter", "fn": lambda r, e, t: _tool_called(r, "scatter_plot")},
            {"name": "output_png", "fn": lambda r, e, t: _has_output(r, ".png")},
            {"name": "png_size", "fn": lambda r, e, t: _png_size_ok(e, "scatter.png", 5_000)},
            {"name": "finish_called", "fn": lambda r, e, t: _finish_called(r)},
        ],
    },
]


# ── 评测运行器 ───────────────────────────────────────


def run_one(task: dict, out_dir: Path) -> dict:
    engine = GisEngine(out_dir=str(out_dir / task["id"]), allowed_roots=["data"])
    agent = GisToolAgent(engine=engine, max_steps=12)
    result = agent.run(task["request"], data_file=task["data"])
    checks = []
    all_pass = True
    for c in task["checks"]:
        try:
            ok, detail = c["fn"](result, engine, task)
        except Exception as exc:  # 检查函数自身异常按失败计
            ok, detail = False, f"检查异常: {exc}"
        all_pass = all_pass and ok
        checks.append({"name": c["name"], "pass": ok, "detail": detail})
    return {
        "task": task["id"],
        "pass": all_pass,
        "steps": result["steps"],
        "timed_out": result["timed_out"],
        "tools": [t["tool"] for t in result["trajectory"]],
        "outputs": result["outputs"],
        "checks": checks,
    }


def run_bench(task_ids: list[str] | None = None) -> dict:
    tasks = TASKS if not task_ids else [t for t in TASKS if t["id"] in task_ids]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("data/gis_bench_results") / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    results = [run_one(t, out_dir) for t in tasks]
    summary = {
        "timestamp": stamp,
        "total": len(results),
        "passed": sum(1 for r in results if r["pass"]),
        "results": results,
    }
    report = out_dir / "report.json"
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _print_report(summary: dict) -> None:
    print(f"\n基准任务集结果: {summary['passed']}/{summary['total']} 通过\n")
    for r in summary["results"]:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"  [{mark}] {r['task']:<12} steps={r['steps']} tools={r['tools']}")
        if not r["pass"]:
            for c in r["checks"]:
                if not c["pass"]:
                    print(f"        - {c['name']}: {c['detail']}")
    print(f"\n完整报告: data/gis_bench_results/{summary['timestamp']}/report.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="GIS 助手基准任务集评测")
    parser.add_argument(
        "--task", action="append", choices=[t["id"] for t in TASKS], help="只跑指定任务（可多次）"
    )
    args = parser.parse_args()
    summary = run_bench(args.task)
    _print_report(summary)
    sys.exit(0 if summary["passed"] == summary["total"] else 1)


if __name__ == "__main__":
    main()
