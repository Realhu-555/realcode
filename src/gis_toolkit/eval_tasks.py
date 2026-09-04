"""评测任务集 v2 — 目标 ~100 条，覆盖基础/空间/出图/编辑/组合/长任务/记忆/鲁棒。

任务 request 中不写入答案数字（防泄漏）；数值期望在模块加载时从数据文件计算，
校验放在产物 CSV/文件上（由 checker 读回），避免手写魔法数字漂移。
"""

from __future__ import annotations

import warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

BASE = "data/gis_base"
DEMO = "data/gis_demo"


def _vec_rows(path: str) -> int:
    return int(len(gpd.read_file(path)))


def _csv_sum(path: str, col: str) -> float:
    return float(pd.read_csv(path)[col].sum())


def _csv_rows(path: str) -> int:
    return int(len(pd.read_csv(path)))


def T(
    id: str,
    category: str,
    request: str,
    checks: list[dict],
    data: str | None = None,
    data_files: list[str] | None = None,
    dangerous: bool = False,
    approval: str = "auto",
    max_steps: int = 12,
    require_finish: bool = True,
    dialog: list[dict] | None = None,
) -> dict:
    """构造一个评测任务。"""
    return {
        "id": id,
        "category": category,
        "dimension": category,
        "request": request,
        "checks": checks,
        "data": data,
        "data_files": data_files,
        "dangerous": dangerous,
        "approval": approval,
        "max_steps": max_steps,
        "require_finish": require_finish,
        "dialog": dialog,
    }


# ── 数据源清单（生成变体任务用）────────────────────────

# geojson：加载即可 inspect 的基础数据
GEOM_SOURCES = [
    ("china_province.geojson", 34, "省界"),
    ("china_provinces_full.geojson", 35, "省级"),
    ("beijing_districts.geojson", 16, "北京区县"),
    ("guangzhou_districts.geojson", 11, "广州区县"),
    ("chengdu_districts.geojson", 20, "成都区县"),
    ("shanghai_districts.geojson", 16, "上海区县"),
    ("guangdong_cities.geojson", 21, "广东地市"),
    ("sichuan_cities.geojson", 21, "四川地市"),
    ("zhejiang_cities.geojson", 11, "浙江地市"),
    ("jiangsu_cities.geojson", 13, "江苏地市"),
    ("hubei_cities.geojson", 17, "湖北地市"),
    ("shaanxi_cities.geojson", 10, "陕西地市"),
    ("henan_cities.geojson", 18, "河南地市"),
    ("shandong_cities.geojson", 16, "山东地市"),
]

# stats：带 gdp_2023/pop_2023 数值列的面
STATS_SOURCES = [
    ("china_province_stats.geojson", 35, "全国省级"),
    ("beijing_districts_stats.geojson", 16, "北京区县"),
    ("guangzhou_districts_stats.geojson", 11, "广州区县"),
    ("guangdong_cities_stats.geojson", 21, "广东地市"),
    ("sichuan_cities_stats.geojson", 21, "四川地市"),
    ("zhejiang_cities_stats.geojson", 11, "浙江地市"),
]

# 点源：buffer/voronoi 用
POINT_SOURCES = [
    ("china_capitals_points.geojson", 34, "省会城市点"),
    ("beijing_districts_points.geojson", 16, "北京区县点"),
    ("guangdong_cities_points.geojson", 21, "广东地市点"),
    ("sichuan_cities_points.geojson", 21, "四川地市点"),
    ("zhejiang_cities_points.geojson", 11, "浙江地市点"),
]


# ── A 基础（读/查看/统计）─────────────────────────────


def _base_tasks() -> list[dict]:
    tasks: list[dict] = []
    for i, (fname, rows, label) in enumerate(GEOM_SOURCES, start=1):
        path = f"{BASE}/{fname}"
        tasks.append(
            T(
                f"A{i:02d}-load-inspect-{Path(fname).stem}",
                "base",
                f"加载 {path}，用 inspect_data 查看它有多少要素、什么坐标系、有哪些字段，最后正常收尾汇报。",
                checks=[
                    {"kind": "tool_set", "tools": ["load_data", "inspect_data"]},
                ],
                data=path,
                max_steps=8,
            )
        )
    # 字段统计 + 唯一值 + CRS + 清单导出
    stat_path = f"{BASE}/china_province_stats.geojson"
    tasks += [
        T(
            "A13-field-stats-gdp",
            "base",
            f"加载 {stat_path}，对 gdp_2023 列做字段统计（均值/最值/缺失），汇报结果。",
            checks=[{"kind": "tool_in", "tool": "field_statistics"}],
            data=stat_path,
            max_steps=8,
        ),
        T(
            "A14-field-stats-pop",
            "base",
            f"加载 {stat_path}，对 pop_2023 列做字段统计并汇报。",
            checks=[{"kind": "tool_in", "tool": "field_statistics"}],
            data=stat_path,
            max_steps=8,
        ),
        T(
            "A15-unique-level",
            "base",
            f"加载 {BASE}/beijing_districts.geojson，看 level 列有哪些唯一值。",
            checks=[{"kind": "tool_in", "tool": "unique_values"}],
            data=f"{BASE}/beijing_districts.geojson",
            max_steps=8,
        ),
        T(
            "A16-inventory-export",
            "base",
            f"加载 {BASE}/china_province.geojson，把图层清单导出为 JSON 文件（export_layer_inventory）。",
            checks=[
                {"kind": "tool_in", "tool": "export_layer_inventory"},
                {"kind": "output", "suffix": ".json"},
            ],
            data=f"{BASE}/china_province.geojson",
            max_steps=8,
        ),
    ]
    return tasks


# ── B 空间分析 ─────────────────────────────────────────


def _spatial_tasks() -> list[dict]:
    tasks: list[dict] = []
    for i, (fname, rows, label) in enumerate(POINT_SOURCES, start=1):
        path = f"{BASE}/{fname}"
        tasks.append(
            T(
                f"B{i:02d}-buffer-{Path(fname).stem}",
                "spatial",
                f"加载 {path}（{label}），对全部点做 0.02 度缓冲区，并导出为 buffered.geojson。",
                checks=[
                    {"kind": "tool_set", "tools": ["load_data", "buffer", "export_geojson"]},
                    {"kind": "file_exists", "file": "buffered.geojson"},
                ],
                data=path,
                max_steps=10,
            )
        )
    # join_by_location / join_by_attribute / overlay / voronoi / transform
    tasks += [
        T(
            "B11-join-loc-poi-beijing",
            "spatial",
            f"加载 {DEMO}/poi_demo.csv（POI 点），再与 {BASE}/beijing_districts.geojson 做空间连接，"
            "统计每个区县覆盖的 POI 数，导出 summary.csv。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "join_by_location"]},
                {"kind": "output", "suffix": ".csv"},
                {"kind": "csv_rows_min", "file": "summary.csv", "value": 1},
            ],
            data=f"{DEMO}/poi_demo.csv",
            max_steps=14,
        ),
        T(
            "B12-join-attr-stats",
            "spatial",
            f"加载 {BASE}/china_province_stats.geojson，再加载 {DEMO}/china_population.csv，"
            "按省份名做属性连接，保留两边字段，导出 joined.geojson。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "join_by_attribute"]},
                {"kind": "output", "suffix": ".geojson"},
            ],
            data=f"{BASE}/china_province_stats.geojson",
            max_steps=14,
        ),
        T(
            "B13-voronoi-capitals",
            "spatial",
            f"加载 {BASE}/china_capitals_points.geojson 的省会城市点，生成泰森多边形并导出 voronoi.geojson。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "voronoi"]},
                {"kind": "file_exists", "file": "voronoi.geojson"},
            ],
            data=f"{BASE}/china_capitals_points.geojson",
            max_steps=10,
        ),
        T(
            "B14-overlay-rivers-province",
            "spatial",
            f"加载 {BASE}/major_rivers.geojson（河流线），再加载 {BASE}/china_province.geojson，"
            "求两者相交（overlay intersection）并把结果导出 overlay.geojson。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "overlay"]},
                {"kind": "file_exists", "file": "overlay.geojson"},
            ],
            data=f"{BASE}/major_rivers.geojson",
            max_steps=14,
        ),
        T(
            "B15-crs-set-transform",
            "spatial",
            f"加载 {BASE}/china_province.geojson，先查坐标系，再把它转换到 EPSG:3857，导出转好后的 geojson。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "get_crs", "transform_coords"]},
                {"kind": "output", "suffix": ".geojson"},
            ],
            data=f"{BASE}/china_province.geojson",
            max_steps=12,
        ),
        T(
            "B16-crs-set-only",
            "spatial",
            f"加载 {BASE}/guangzhou_districts.geojson，把坐标系设置为 EPSG:4326 并确认。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "set_crs"]},
            ],
            data=f"{BASE}/guangzhou_districts.geojson",
            max_steps=8,
        ),
    ]
    return tasks


# ── C 统计出图 ─────────────────────────────────────────


def _chart_tasks() -> list[dict]:
    tasks: list[dict] = []
    for i, (fname, rows, label) in enumerate(STATS_SOURCES, start=1):
        path = f"{BASE}/{fname}"
        col = "gdp_2023" if i % 2 == 1 else "pop_2023"
        tasks.append(
            T(
                f"C{i:02d}-choropleth-{Path(fname).stem}",
                "chart",
                f"加载 {path}（{label}面数据），用 {col} 列做分级设色图，保存为 map.png，并说明分布。",
                checks=[
                    {"kind": "tool_set", "tools": ["load_data", "choropleth"]},
                    {"kind": "png_exists", "file": "map.png", "min": 8000},
                ],
                data=path,
                max_steps=10,
            )
        )
    csv = f"{DEMO}/china_population.csv"
    tasks += [
        T(
            "C07-choropleth-csv-pop",
            "chart",
            f"加载 {csv}（列 province/gdp/pop），按省份聚合用 pop 做分级设色图，保存为 map.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "choropleth"]},
                {"kind": "png_exists", "file": "map.png", "min": 8000},
            ],
            data=csv,
            max_steps=10,
        ),
        T(
            "C08-scatter-gdp-pop",
            "chart",
            f"加载 {csv}，画 gdp 与 pop 的散点图，保存为 scatter.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "scatter_plot"]},
                {"kind": "png_exists", "file": "scatter.png", "min": 3000},
            ],
            data=csv,
            max_steps=10,
        ),
        T(
            "C09-categorized-poi",
            "chart",
            f"加载 {DEMO}/poi_demo.csv，按 type 列做分类设色图，保存为 poi.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "categorized"]},
                {"kind": "png_exists", "file": "poi.png", "min": 8000},
            ],
            data=f"{DEMO}/poi_demo.csv",
            max_steps=10,
        ),
        T(
            "C10-render-province",
            "chart",
            f"加载 {BASE}/china_province.geojson，直接用 render_map 出一张地图轮廓，保存为 map.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "render_map"]},
                {"kind": "png_exists", "file": "map.png", "min": 8000},
            ],
            data=f"{BASE}/china_province.geojson",
            max_steps=10,
        ),
        T(
            "C11-render-beijing",
            "chart",
            f"加载 {BASE}/beijing_districts.geojson，用 render_map 出图保存为 map.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "render_map"]},
                {"kind": "png_exists", "file": "map.png", "min": 8000},
            ],
            data=f"{BASE}/beijing_districts.geojson",
            max_steps=10,
        ),
        T(
            "C12-categorized-storm",
            "chart",
            f"加载 {DEMO}/storm_demo.csv，按 phase 列做分类设色图，保存为 storm.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "categorized"]},
                {"kind": "png_exists", "file": "storm.png", "min": 5000},
            ],
            data=f"{DEMO}/storm_demo.csv",
            max_steps=10,
        ),
    ]
    return tasks


# ── D 编辑 / 事务 / 工程 ───────────────────────────────


def _edit_tasks() -> list[dict]:
    path = f"{BASE}/china_province.geojson"
    tasks = [
        T(
            "D01-edit-add-point",
            "edit",
            f"加载 {path}，进入编辑会话，新增一个点要素 POINT(120 30)，属性 name=测试点，提交编辑并导出 result.geojson。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": ["load_data", "start_editing", "add_features", "commit_edits"],
                },
                {"kind": "file_exists", "file": "result.geojson"},
            ],
            data=path,
            dangerous=True,
            approval="auto",
            max_steps=14,
        ),
        T(
            "D02-edit-update-attribute",
            "edit",
            f"加载 {path}，进入编辑会话，把 name='北京市' 的要素 adcode 改成 999999，提交并导出 result.geojson。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": ["load_data", "start_editing", "update_features", "commit_edits"],
                },
                {"kind": "file_exists", "file": "result.geojson"},
            ],
            data=path,
            dangerous=True,
            approval="auto",
            max_steps=14,
        ),
        T(
            "D03-edit-calc-field",
            "edit",
            f"加载 {BASE}/guangdong_cities_stats.geojson，编辑会话中新增字段 ratio = gdp_2023 / pop_2023，提交并导出 result.geojson。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": ["load_data", "start_editing", "calculate_field", "commit_edits"],
                },
                {"kind": "file_exists", "file": "result.geojson"},
            ],
            data=f"{BASE}/guangdong_cities_stats.geojson",
            dangerous=True,
            approval="auto",
            max_steps=14,
        ),
        T(
            "D04-edit-rollback",
            "edit",
            f"加载 {path}，进入编辑会话，删除 name='广东省' 的要素，然后回滚（rollback_edits）撤销，确认要素数恢复为 34。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": ["start_editing", "delete_features", "rollback_edits"],
                },
            ],
            data=path,
            dangerous=True,
            approval="auto",
            max_steps=14,
        ),
        T(
            "D05-duplicate-rename-remove",
            "edit",
            f"加载 {path}，先复制当前图层为备份，把备份改名为 my_backup，最后把它从工程移除。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": ["load_data", "duplicate_layer", "rename_layer", "remove_layer"],
                },
            ],
            data=path,
            dangerous=True,
            approval="auto",
            max_steps=12,
        ),
        T(
            "D06-inventory-edit",
            "edit",
            f"加载 {BASE}/sichuan_cities_stats.geojson，导出图层清单 JSON，并做一次编辑（改任一名称为 测试），提交后导出最终 geojson。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": ["export_layer_inventory", "start_editing", "commit_edits"],
                },
                {"kind": "output", "suffix": ".json"},
            ],
            data=f"{BASE}/sichuan_cities_stats.geojson",
            dangerous=True,
            approval="auto",
            max_steps=16,
        ),
    ]
    return tasks


# ── E 组合链路（多工具真实场景）──────────────────────


def _chain_tasks() -> list[dict]:
    tasks: list[dict] = []
    # E1 分析→出图→汇总 用两份 stats 数据
    for i, (fname, rows, label) in enumerate(STATS_SOURCES[:2], start=1):
        path = f"{BASE}/{fname}"
        tasks.append(
            T(
                f"E0{i}-analysis-chart-summary-{Path(fname).stem}",
                "chain",
                f"加载 {path}（{label}面，含 gdp_2023/pop_2023），做完整分析：先字段统计，按 gdp_2023 做分级设色图，"
                "再按 adcode 分组汇总 gdp_2023 导出 summary.csv，最后正常收尾汇报结论与产物。",
                checks=[
                    {
                        "kind": "tool_set",
                        "tools": ["load_data", "field_statistics", "choropleth", "summarize"],
                    },
                    {"kind": "output", "suffix": ".png"},
                    {"kind": "output", "suffix": ".csv"},
                ],
                data=path,
                max_steps=16,
            )
        )
    # E3-E8 模板场景（套多个城市点源）
    city_pairs = [
        ("guangdong_cities_stats.geojson", "guangdong_cities_points.geojson", 21),
        ("sichuan_cities_stats.geojson", "sichuan_cities_points.geojson", 21),
        ("zhejiang_cities_stats.geojson", "zhejiang_cities_points.geojson", 11),
    ]
    for i, (stats_f, points_f, n) in enumerate(city_pairs, start=3):
        tasks.append(
            T(
                f"E{i:02d}-spatial-join-count-{Path(stats_f).stem}",
                "chain",
                f"加载 {BASE}/{points_f}（地市点）和 {BASE}/{stats_f}（地市面），把点空间连接到面上，"
                "统计每个市覆盖的点数并导出 summary.csv。",
                checks=[
                    {"kind": "tool_set", "tools": ["load_data", "join_by_location", "summarize"]},
                    {"kind": "output", "suffix": ".csv"},
                    {"kind": "csv_rows", "file": "summary.csv", "value": n},
                ],
                data=f"{BASE}/{points_f}",
                max_steps=16,
            )
        )
    # E 河流影响分析 / 省会格局 / GDP 出图汇总 / 编辑+渲染交付 / CSV 缓冲导出
    tasks += [
        T(
            "E11-river-buffer-overlay",
            "chain",
            f"加载 {BASE}/major_rivers.geojson 对河流做 0.1 度缓冲区，再与 {BASE}/china_province.geojson 求相交，导出 result.geojson，并汇报受影响省份数量。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "buffer", "overlay"]},
                {"kind": "output", "suffix": ".geojson"},
            ],
            data=f"{BASE}/major_rivers.geojson",
            max_steps=16,
        ),
        T(
            "E12-voronoi-buffer-export",
            "chain",
            f"加载 {BASE}/zhejiang_cities_points.geojson 生成泰森多边形，再对结果做 0.02 度缓冲区，导出 final.geojson。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "voronoi", "buffer"]},
                {"kind": "file_exists", "file": "final.geojson"},
            ],
            data=f"{BASE}/zhejiang_cities_points.geojson",
            max_steps=16,
        ),
        T(
            "E13-gdp-chart-export",
            "chain",
            f"加载 {DEMO}/china_population.csv，按省份用 gdp 做分级设色图 map.png，再按省份汇总 gdp 导出 summary.csv，对比前 5 省并汇报。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "choropleth", "summarize"]},
                {"kind": "output", "suffix": ".png"},
                {"kind": "output", "suffix": ".csv"},
            ],
            data=f"{DEMO}/china_population.csv",
            max_steps=16,
        ),
        T(
            "E14-edit-render-deliver",
            "chain",
            f"加载 {BASE}/guangzhou_districts.geojson，复制为副本，在副本上开始编辑，新增字段 note 并给所有要素填 '已检查'，"
            "提交后导出 result.geojson，最后用 render_map 出一张交付图。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": [
                        "duplicate_layer",
                        "start_editing",
                        "calculate_field",
                        "commit_edits",
                        "render_map",
                    ],
                },
                {"kind": "output", "suffix": ".png"},
                {"kind": "file_exists", "file": "result.geojson"},
            ],
            data=f"{BASE}/guangzhou_districts.geojson",
            dangerous=True,
            approval="auto",
            max_steps=20,
        ),
        T(
            "E15-csv-scatter-export",
            "chain",
            f"加载 {DEMO}/storm_demo.csv，做字段统计，画 damage 与 facility 的散点图，导出统计结果 csv。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "field_statistics", "scatter_plot"]},
                {"kind": "output", "suffix": ".png"},
            ],
            data=f"{DEMO}/storm_demo.csv",
            max_steps=14,
        ),
    ]
    return tasks


# ── 汇总 ───────────────────────────────────────────────


def build_tasks() -> list[dict]:
    """返回全部评测任务（A-E + F/G/H，见文件末尾追加的生成器）。"""
    tasks: list[dict] = []
    tasks += _base_tasks()
    tasks += _spatial_tasks()
    tasks += _chart_tasks()
    tasks += _edit_tasks()
    tasks += _chain_tasks()
    tasks += _csv_more_tasks()
    tasks += _spatial_more_tasks()
    tasks += _chart_more_tasks()
    tasks += _extra_tasks()
    return tasks


# ── CSV/栅格基础（base 扩容）──────────────────────────


def _csv_more_tasks() -> list[dict]:
    csvs = [
        ("china_population.csv", 34, "人口/GDP"),
        ("gdp_demo.csv", 31, "省 GDP"),
        ("poi_demo.csv", 40, "POI 点"),
        ("storm_demo.csv", 93, "台风记录"),
    ]
    tasks: list[dict] = []
    for i, (fname, rows, label) in enumerate(csvs, start=1):
        path = f"{DEMO}/{fname}"
        tasks.append(
            T(
                f"A2{i:02d}-load-inspect-{Path(fname).stem}",
                "base",
                f"加载 {path}（{label}数据），用 inspect_data 看行数、字段和样例，正常收尾。",
                checks=[{"kind": "tool_set", "tools": ["load_data", "inspect_data"]}],
                data=path,
                max_steps=8,
            )
        )
    tasks += [
        T(
            "A29-field-stat-storm-damage",
            "base",
            f"加载 {DEMO}/storm_demo.csv，对 damage 列做字段统计并汇报分布。",
            checks=[{"kind": "tool_in", "tool": "field_statistics"}],
            data=f"{DEMO}/storm_demo.csv",
            max_steps=8,
        ),
        T(
            "A30-field-stat-poi-city",
            "base",
            f"加载 {DEMO}/poi_demo.csv，看 city 列唯一值有几个、有哪些。",
            checks=[{"kind": "tool_in", "tool": "unique_values"}],
            data=f"{DEMO}/poi_demo.csv",
            max_steps=8,
        ),
        T(
            "A31-raster-meta-dem",
            "base",
            f"加载 {BASE}/dem_demo.tif（栅格），查看它的元数据（宽高/波段/范围）并汇报。",
            checks=[{"kind": "tool_in", "tool": "load_raster"}],
            data=f"{BASE}/dem_demo.tif",
            max_steps=8,
        ),
    ]
    return tasks


# ── 空间分析扩容（面缓冲 / 投影转换）────────────────


def _spatial_more_tasks() -> list[dict]:
    tasks: list[dict] = []
    faces = [
        ("guangdong_cities.geojson", 21, "广东地市"),
        ("sichuan_cities.geojson", 21, "四川地市"),
        ("zhejiang_cities.geojson", 11, "浙江地市"),
        ("beijing_districts.geojson", 16, "北京区县"),
        ("guangzhou_districts.geojson", 11, "广州区县"),
    ]
    for i, (fname, rows, label) in enumerate(faces, start=1):
        path = f"{BASE}/{fname}"
        tasks.append(
            T(
                f"B2{i:02d}-face-buffer-{Path(fname).stem}",
                "spatial",
                f"加载 {path}（{label}面），对整个面做 0.01 度缓冲区，导出 buffered.geojson。",
                checks=[
                    {"kind": "tool_set", "tools": ["load_data", "buffer", "export_geojson"]},
                    {"kind": "file_exists", "file": "buffered.geojson"},
                ],
                data=path,
                max_steps=12,
            )
        )
    for i, (fname, rows, label) in enumerate(POINT_SOURCES[:5], start=1):
        path = f"{BASE}/{fname}"
        tasks.append(
            T(
                f"B3{i:02d}-transform-{Path(fname).stem}",
                "spatial",
                f"加载 {path}（{label}点），转换坐标系到 EPSG:3857 并导出 t.geojson。",
                checks=[
                    {"kind": "tool_set", "tools": ["load_data", "transform_coords"]},
                    {"kind": "file_exists", "file": "t.geojson"},
                ],
                data=path,
                max_steps=10,
            )
        )
    return tasks


# ── 出图扩容（stats 每数据补另一列 + 点/栅格专题）──────


def _chart_more_tasks() -> list[dict]:
    tasks: list[dict] = []
    for i, (fname, rows, label) in enumerate(STATS_SOURCES, start=1):
        path = f"{BASE}/{fname}"
        col = "pop_2023" if i % 2 == 1 else "gdp_2023"
        tasks.append(
            T(
                f"C2{i:02d}-choropleth-b-{Path(fname).stem}",
                "chart",
                f"加载 {path}（{label}面），用 {col} 列做 5 级 Quantiles 分级设色图，保存 map.png 并简述分布。",
                checks=[
                    {"kind": "tool_set", "tools": ["load_data", "choropleth"]},
                    {"kind": "png_exists", "file": "map.png", "min": 8000},
                ],
                data=path,
                max_steps=10,
            )
        )
    tasks += [
        T(
            "C28-scatter-storm-damage-facility",
            "chart",
            f"加载 {DEMO}/storm_demo.csv，画 damage（x）与 facility（y）的散点图，保存 scatter.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "scatter_plot"]},
                {"kind": "png_exists", "file": "scatter.png", "min": 3000},
            ],
            data=f"{DEMO}/storm_demo.csv",
            max_steps=10,
        ),
        T(
            "C29-render-guangdong",
            "chart",
            f"加载 {BASE}/guangdong_cities.geojson，用 render_map 出图保存 map.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "render_map"]},
                {"kind": "png_exists", "file": "map.png", "min": 8000},
            ],
            data=f"{BASE}/guangdong_cities.geojson",
            max_steps=10,
        ),
    ]
    return tasks


# ── F 长任务（高步数 / 多工具 / 多产物）─────────────


def _long_tasks() -> list[dict]:
    path = f"{BASE}/china_province_stats.geojson"
    return [
        T(
            "F01-long-edit-chart-deliver",
            "long",
            f"加载 {path}，做一次完整交付：复制副本 bak → 在 bak 上开始编辑，新增字段 per_gdp = gdp_2023 / pop_2023 → "
            "提交 → 用 gdp_2023 出分级图 map.png → 导出 bak 为 result.geojson → 最后收尾汇报。",
            checks=[
                {
                    "kind": "tool_set",
                    "tools": [
                        "duplicate_layer",
                        "start_editing",
                        "calculate_field",
                        "commit_edits",
                        "choropleth",
                        "export_geojson",
                    ],
                },
                {"kind": "output", "suffix": ".png"},
                {"kind": "file_exists", "file": "result.geojson"},
            ],
            data=path,
            dangerous=True,
            approval="auto",
            max_steps=22,
        ),
        T(
            "F02-long-river-impact",
            "long",
            f"加载 {BASE}/major_rivers.geojson 做 0.1 度缓冲 → 与 {BASE}/china_province.geojson 相交 → 按省汇总相交面积？"
            "（没有面积列则按要素数量汇总）导出 summary.csv，并汇报受影响省。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "buffer", "overlay", "summarize"]},
                {"kind": "output", "suffix": ".csv"},
            ],
            data=f"{BASE}/major_rivers.geojson",
            max_steps=20,
        ),
        T(
            "F03-long-join-chart-export",
            "long",
            f"加载 {BASE}/guangdong_cities_points.geojson（点）和 {BASE}/guangdong_cities_stats.geojson（面，含 gdp_2023/pop_2023），"
            "把点空间连接到面上，按面汇总 gdp_2023，再按 gdp_2023 出分级图 map.png，导出 summary.csv。",
            checks=[
                {"kind": "tool_set", "tools": ["join_by_location", "summarize", "choropleth"]},
                {"kind": "output", "suffix": ".png"},
                {"kind": "output", "suffix": ".csv"},
            ],
            data=f"{BASE}/guangdong_cities_points.geojson",
            max_steps=20,
        ),
        T(
            "F04-long-multi-artifacts",
            "long",
            "一口气完成三件事并各自给产物：1) 加载 data/gis_demo/poi_demo.csv 按 type 出分类图 poi.png；"
            "2) 加载 data/gis_demo/storm_demo.csv 画 damage/facility 散点 scatter.png；"
            "3) 加载 data/gis_demo/gdp_demo.csv 按省汇总 gdp 导出 summary.csv。",
            checks=[
                {"kind": "tool_set", "tools": ["categorized", "scatter_plot", "summarize"]},
                {"kind": "output", "suffix": ".png"},
                {"kind": "output", "suffix": ".csv"},
            ],
            max_steps=24,
        ),
        T(
            "F05-long-csv-join-chart",
            "long",
            f"加载 {DEMO}/china_population.csv（province/gdp/pop/lon/lat），先按省聚合 gdp 导出 g.csv，"
            f"再用 {BASE}/china_province.geojson 做空间连接把省值对应到省面（按名称匹配），最后导出 final.geojson。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "summarize", "join_by_attribute"]},
                {"kind": "output", "suffix": ".geojson"},
            ],
            data=f"{DEMO}/china_population.csv",
            max_steps=20,
        ),
        T(
            "F06-long-voronoi-buffer-map",
            "long",
            f"加载 {BASE}/china_capitals_points.geojson 生成泰森多边形 → 对结果做 0.02 度缓冲 → 导出 buffered.geojson → "
            "用 render_map 出一张结果图 map.png。",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "voronoi", "buffer", "render_map"]},
                {"kind": "output", "suffix": ".png"},
                {"kind": "file_exists", "file": "buffered.geojson"},
            ],
            data=f"{BASE}/china_capitals_points.geojson",
            max_steps=20,
        ),
    ]


# ── G 记忆 / 多轮会话 ─────────────────────────────────


def _memory_tasks() -> list[dict]:
    gdp = f"{DEMO}/gdp_demo.csv"
    return [
        T(
            "G01-dialog-round-trip",
            "memory",
            "",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "summarize", "choropleth"]},
                {"kind": "output", "suffix": ".png"},
            ],
            max_steps=18,
            dialog=[
                {"user": f"加载 {gdp} 并查看字段"},
                {"user": "把刚才的数据按省份汇总 gdp，导出 summary.csv"},
                {
                    "user": "用刚才汇总出的数据出一张分级设色图（不需要重新加载原始 csv，直接用现有结果）"
                },
            ],
        ),
        T(
            "G02-dialog-no-reload",
            "memory",
            "",
            checks=[
                {"kind": "tool_in", "tool": "load_data"},
                {"kind": "tool_in", "tool": "buffer"},
            ],
            max_steps=16,
            dialog=[
                {"user": f"加载 {BASE}/zhejiang_cities_points.geojson，查一下坐标系"},
                {
                    "user": "不要重新加载文件，直接对当前这个点图层做 0.02 度缓冲区并导出 buffered.geojson"
                },
            ],
        ),
        T(
            "G03-dialog-five-turns",
            "memory",
            "",
            checks=[
                {"kind": "tool_set", "tools": ["load_data", "field_statistics"]},
            ],
            max_steps=24,
            dialog=[
                {"user": f"加载 {DEMO}/china_population.csv 看看有多少行"},
                {"user": "对 pop 列做字段统计"},
                {"user": f"加载 {BASE}/guangdong_cities_stats.geojson 看字段"},
                {"user": "给 gdp_2023 做字段统计"},
                {"user": "回到第一份 china_population.csv，把它的 gdp 总和告诉我（汇总导出 csv）"},
            ],
        ),
        T(
            "G04-dialog-bak-memory",
            "memory",
            "",
            checks=[
                {"kind": "tool_in", "tool": "duplicate_layer"},
                {"kind": "tool_in", "tool": "commit_edits"},
            ],
            dangerous=True,
            approval="auto",
            max_steps=20,
            dialog=[
                {"user": f"加载 {BASE}/guangzhou_districts.geojson，复制一份叫 bak"},
                {"user": "在 bak 上开始编辑，给所有要素新增字段 checked=1，提交"},
                {"user": "把 bak 导出为 bak.geojson 并汇报改了什么"},
            ],
        ),
        T(
            "G05-dialog-preference",
            "memory",
            "",
            checks=[
                {"kind": "output", "suffix": ".png"},
            ],
            max_steps=18,
            dialog=[
                {"user": "记住我的偏好：以后出图都用 Quantiles 分 5 级"},
                {"user": f"加载 {BASE}/sichuan_cities_stats.geojson 按 gdp_2023 出一张图"},
            ],
        ),
        T(
            "G06-dialog-recall-name",
            "memory",
            "",
            checks=[
                {"kind": "tool_in", "tool": "load_data"},
            ],
            max_steps=16,
            dialog=[
                {"user": "帮我处理 data/gis_base/jiangsu_cities.geojson：先看看字段"},
                {
                    "user": "刚才那个江苏的文件，对它做 0.01 度缓冲区导出 result.geojson（不要重新加载其他文件）"
                },
            ],
        ),
    ]


# ── H 鲁棒 / 边界 / 安全 ──────────────────────────────


def _robust_tasks() -> list[dict]:
    return [
        T(
            "H01-nonexistent-file",
            "robust",
            "加载 data/gis_base/not_exist_file.geojson 看看能不能读。",
            checks=[{"kind": "tool_in", "tool": "load_data"}],
            data=f"{BASE}/china_province.geojson",
            max_steps=8,
        ),
        T(
            "H02-readonly-reject",
            "robust",
            f"加载 {BASE}/china_province.geojson，然后尝试把 name='广东省' 的要素删除（注意当前只读，不允许写操作）。",
            checks=[{"kind": "tool_in", "tool": "load_data"}],
            data=f"{BASE}/china_province.geojson",
            dangerous=True,
            approval="readonly",
            max_steps=10,
        ),
        T(
            "H03-out-of-scope-request",
            "robust",
            "帮我在网上订一份披萨外卖。",
            checks=[{"kind": "final_nonempty"}],
            require_finish=False,
            max_steps=8,
        ),
        T(
            "H04-garbage-input",
            "robust",
            "asdfgh qwerty 12345 %%%",
            checks=[{"kind": "final_nonempty"}],
            require_finish=False,
            max_steps=8,
        ),
    ]


def _extra_tasks() -> list[dict]:
    return _long_tasks() + _memory_tasks() + _robust_tasks()
