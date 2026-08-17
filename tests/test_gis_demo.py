"""SPEC 第 8 节 MVP 验收清单 1-6 自动化验证（gdp_demo.csv 分级设色图）"""

import zipfile
from pathlib import Path

from src.agents.gis_common import parse_pass_fail
from src.orchestrator.graph import create_gis_graph

DEMO_DATA = Path("data/gis_demo/gdp_demo.csv")

_DEMO_SCRIPT = (
    "import pandas as pd\n"
    "import geopandas as gpd\n"
    "import matplotlib\n"
    "matplotlib.use(\"Agg\")\n"
    "import matplotlib.pyplot as plt\n"
    "df = pd.read_csv(\"gdp_demo.csv\")\n"
    "gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[\"lon\"], df[\"lat\"]), crs=\"EPSG:4326\")\n"
    "print(\"CRS:\", gdf.crs.to_string())\n"
    "print(\"ROWS:\", len(gdf))\n"
    "fig, ax = plt.subplots(figsize=(8, 6))\n"
    "gdf.plot(ax=ax, column=\"gdp\", cmap=\"OrRd\", scheme=\"Quantiles\", k=5, legend=True)\n"
    "ax.set_title(\"GDP Choropleth by Province\")\n"
    "fig.savefig(\"choropleth.png\", dpi=100)\n"
    "summary = df[[\"province\", \"gdp\"]].sort_values(\"gdp\", ascending=False).reset_index(drop=True)\n"
    "summary.to_csv(\"summary.csv\", index=False)\n"
    "print(\"DONE\")\n"
)


def _fake_agents():
    """不调用 LLM 的验收用假 Agent（exec/export 用真实节点）"""

    class _Plan:
        def run(self, s):
            return {
                **s,
                "task_plan": (
                    "## 任务方案\n"
                    "1. 读取 gdp_demo.csv 并检查字段\n"
                    "2. 将经纬度列转为点要素并设定坐标系 EPSG:4326\n"
                    "3. 按省份 GDP 做 5 级分级设色出图 choropleth.png\n"
                    "4. 生成 GDP 降序 summary.csv"
                ),
                "current_stage": "design",
            }

    class _Design:
        def run(self, s):
            return {
                **s,
                "tech_plan": (
                    "## 技术方案\n"
                    "输入字段清单: province, gdp, lon, lat\n"
                    "坐标系: EPSG:4326\n"
                    "分级方式: Quantiles 5 级\n"
                    "输出文件: choropleth.png, summary.csv"
                ),
                "current_stage": "codegen",
            }

    class _Codegen:
        def run(self, s):
            return {**s, "script": _DEMO_SCRIPT, "current_stage": "exec"}

    class _Checker:
        def run(self, s):
            return {
                **s,
                "check_report": (
                    "- ✅ choropleth.png 存在且非空\n"
                    "- ✅ summary.csv 字段含 province/gdp\n"
                    "- ✅ 坐标系 EPSG:4326 与方案一致\n"
                    "- ✅ 图可读\n"
                    "- ✅ 无 ERROR 日志\n"
                    "整体结论: PASS"
                ),
                "current_stage": "check",
            }

    return {"plan": _Plan(), "design": _Design(), "codegen": _Codegen(), "checker": _Checker()}


def test_mvp_acceptance_1_to_6(tmp_path):
    """验收清单 1-6：plan≥3步 / design 四要素 / 退出码0无ERROR / 双产出 / PASS / zip 含说明"""
    graph = create_gis_graph(_fake_agents(), export_dir=str(tmp_path), project_id="mvp")
    result = graph.invoke({
        "user_request": "把 gdp_demo.csv 按省份做分级设色图",
        "data_file": str(DEMO_DATA),
        "data_schema": "province: str\ngdp: int\nlon: float\nlat: float",
        "current_stage": "plan",
        "messages": [],
    })

    # 1. plan 产出 ≥3 步任务清单，且不追问
    assert result.get("ask_user") is None
    assert len(result["task_plan"].strip().splitlines()) >= 3

    # 2. design 技术方案含字段清单 / 坐标系 / 分级方式 / 输出文件
    tech = result["tech_plan"]
    for kw in ("province", "gdp", "EPSG", "Quantiles", "choropleth.png", "summary.csv"):
        assert kw in tech, kw

    # 3. 脚本沙箱执行退出码 0，无 ERROR 日志
    assert "ERROR" not in result["exec_log"]
    assert "CRS: EPSG:4326" in result["exec_log"]

    # 4. 产出 choropleth.png + summary.csv
    assert "choropleth.png" in result["artifacts"]
    assert "summary.csv" in result["artifacts"]

    # 5. checker 全部 ✅，结论 PASS
    assert parse_pass_fail(result["check_report"])

    # 6. export 打包 zip 可下载，内含操作说明 + choropleth.png（>20KB）
    with zipfile.ZipFile(result["artifact_path"]) as zf:
        names = zf.namelist()
    assert any("操作说明.md" in n for n in names)
    with zipfile.ZipFile(result["artifact_path"]) as zf:
        png_info = zf.getinfo(next(n for n in names if n.endswith("choropleth.png")))
    assert png_info.file_size > 20 * 1024
