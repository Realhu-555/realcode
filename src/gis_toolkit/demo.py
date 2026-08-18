"""GIS 智能助手 CLI 演示（设计文档 Task C）

用法：
    python -m src.gis_toolkit.demo "把 gdp_demo.csv 按省份做分级设色图" --data data/gis_demo/gdp_demo.csv
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from src.gis_toolkit.agent import GisToolAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="GIS 智能助手（工具调用版）")
    parser.add_argument(
        "request",
        nargs="?",
        default="把 gdp_demo.csv 按省份做分级设色图（choropleth），并导出分级统计 summary.csv",
    )
    parser.add_argument("--data", default="data/gis_demo/gdp_demo.csv", help="数据文件路径")
    parser.add_argument("--max-steps", type=int, default=12)
    args = parser.parse_args()

    agent = GisToolAgent(max_steps=args.max_steps)
    result = agent.run(args.request, data_file=args.data)

    print("\n===== 工具轨迹 =====")
    for t in result["trajectory"]:
        st = t["result"].get("status")
        detail = t["result"].get("message") or t["result"].get("error") or ""
        print(f"  step {t['step']:>2}  {t['tool']:<15} {json.dumps(t['args'], ensure_ascii=False)}  ->  {st}  {detail}")
    print("\n===== 结果 =====")
    print(f"  steps     = {result['steps']}")
    print(f"  timed_out = {result['timed_out']}")
    print(f"  outputs   = {result['outputs']}")
    if result["final"]:
        print(f"  final     = {result['final'][:300]}")

    # 轨迹落盘（可回放 / 评测）
    trace_dir = Path("data/gis_traces")
    trace_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_path = trace_dir / f"trace_{stamp}.json"
    trace_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  轨迹已保存: {trace_path}")


if __name__ == "__main__":
    main()
