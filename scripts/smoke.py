"""T15 冒烟：验证 GIS 工具链完整链路（不依赖 LLM，稳定快速）。

用法：
    python scripts/smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

GDP_CSV = PROJECT_ROOT / "data" / "gis_demo" / "gdp_demo.csv"
SMOKE_OUT = PROJECT_ROOT / "data" / "gis_toolkit_out" / "smoke"


def main() -> int:
    if not GDP_CSV.is_file():
        print(f"缺少演示数据: {GDP_CSV}", file=sys.stderr)
        return 1
    from src.gis_toolkit.engine import create_gis_engine

    engine = create_gis_engine(
        out_dir=str(SMOKE_OUT),
        allowed_roots=[str(PROJECT_ROOT / "data")],
    )

    # 链路：加载 → 查看 → 分级图 → 汇总 → 导出 → 完成
    res = engine.load_data(str(GDP_CSV))
    assert res["status"] == "ok" and res["layer"]["rows"] == 31

    res = engine.inspect_data()
    assert res["status"] == "ok" and len(res["bounds"]) == 4

    res = engine.choropleth("gdp", output="smoke_choropleth.png")
    assert res["status"] == "ok" and res["size_bytes"] > 0

    res = engine.summarize(
        "gdp", groupby="province", agg="sum", output="smoke_summary.csv"
    )
    assert res["status"] == "ok" and res["summary_rows"] == 31

    res = engine.export_geojson(output="smoke_layer.geojson")
    assert res["status"] == "ok"

    res = engine.finish(
        outputs=[
            "smoke_choropleth.png",
            "smoke_summary.csv",
            "smoke_layer.geojson",
        ],
        summary="smoke ok",
    )
    assert res["status"] == "finished"

    print("SMOKE PASSED")
    print("outputs:", res["outputs"])
    print("out_dir:", SMOKE_OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
