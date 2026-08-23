"""生成 GIS 演示/测试配套数据（派生 + 合成）。

用法（需在项目 venv 中运行，依赖 geopandas/rasterio）：
    venv\\Scripts\\python.exe scripts\\generate_test_data.py

产物：
- data/gis_base/*_points.geojson     由边界 center 派生的点图层
- data/gis_base/*_stats.geojson      边界 + 演示统计字段（gdp_2023/pop_2023）
- data/gis_base/major_rivers.geojson 示意水系线
- data/gis_base/dem_demo.tif         演示 DEM 栅格（北京范围）
- data/gis_demo/china_population.csv 省级人口/GDP 演示数据
- data/gis_demo/poi_demo.csv         合成 POI 点数据
- data/gis_bench_data/cities.geojson 修复城市名乱码

说明：统计字段为近似演示值（基于公开统计年鉴的粗略值），仅用于功能测试，
不用于正式业务；水系为示意线，非精确测绘数据。
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = PROJECT_ROOT / "data" / "gis_base"
DEMO_DIR = PROJECT_ROOT / "data" / "gis_demo"
BENCH_DIR = PROJECT_ROOT / "data" / "gis_bench_data"


# ── 演示统计字段（gdp_2023 亿元 / pop_2023 万人）────────────────────────
PROVINCE_STATS: dict[str, tuple[float, float]] = {
    "北京市": (43761, 2186),
    "天津市": (16737, 1364),
    "河北省": (43944, 7393),
    "山西省": (25698, 3466),
    "内蒙古自治区": (24627, 2396),
    "辽宁省": (30209, 4182),
    "吉林省": (13531, 2339),
    "黑龙江省": (15884, 3062),
    "上海市": (47219, 2487),
    "江苏省": (128222, 8526),
    "浙江省": (82553, 6627),
    "安徽省": (47051, 6121),
    "福建省": (54355, 4183),
    "江西省": (32200, 4515),
    "山东省": (92069, 10123),
    "河南省": (59132, 9815),
    "湖北省": (55804, 5838),
    "湖南省": (50013, 6568),
    "广东省": (135673, 12706),
    "广西壮族自治区": (27202, 5027),
    "海南省": (7551, 1043),
    "重庆市": (30146, 3191),
    "四川省": (60133, 8368),
    "贵州省": (20913, 3865),
    "云南省": (30021, 4673),
    "西藏自治区": (2393, 365),
    "陕西省": (33786, 3952),
    "甘肃省": (11864, 2465),
    "青海省": (3799, 594),
    "宁夏回族自治区": (5315, 729),
    "新疆维吾尔自治区": (19126, 2598),
    "台湾省": (53200, 2342),
    "香港特别行政区": (27000, 750),
    "澳门特别行政区": (3100, 68),
}

GUANGDONG_STATS: dict[str, tuple[float, float]] = {
    "广州市": (30356, 1883),
    "韶关市": (1620, 285),
    "深圳市": (34606, 1779),
    "珠海市": (4233, 249),
    "汕头市": (3158, 555),
    "佛山市": (13276, 961),
    "江门市": (4022, 482),
    "湛江市": (3794, 704),
    "茂名市": (3982, 622),
    "肇庆市": (2793, 414),
    "惠州市": (5639, 607),
    "梅州市": (1408, 387),
    "汕尾市": (1431, 268),
    "河源市": (1367, 282),
    "阳江市": (1612, 262),
    "清远市": (2030, 397),
    "东莞市": (11438, 1049),
    "中山市": (3851, 447),
    "潮州市": (1357, 257),
    "揭阳市": (2459, 558),
    "云浮市": (1207, 238),
}

SICHUAN_STATS: dict[str, tuple[float, float]] = {
    "成都市": (22074, 2140),
    "自贡市": (1670, 268),
    "攀枝花市": (1304, 121),
    "泸州市": (2582, 428),
    "德阳市": (3015, 346),
    "绵阳市": (4038, 489),
    "广元市": (1173, 228),
    "遂宁市": (1728, 282),
    "内江市": (1800, 313),
    "乐山市": (2448, 316),
    "南充市": (2718, 551),
    "眉山市": (1738, 296),
    "宜宾市": (3806, 460),
    "广安市": (1511, 320),
    "达州市": (2656, 534),
    "雅安市": (1048, 142),
    "巴中市": (797, 265),
    "资阳市": (1023, 223),
    "阿坝藏族羌族自治州": (505, 82),
    "甘孜藏族自治州": (490, 110),
    "凉山彝族自治州": (2261, 531),
}

ZHEJIANG_STATS: dict[str, tuple[float, float]] = {
    "杭州市": (20059, 1252),
    "宁波市": (16452, 969),
    "温州市": (8731, 976),
    "嘉兴市": (7062, 558),
    "湖州市": (4015, 343),
    "绍兴市": (7791, 539),
    "金华市": (6011, 716),
    "衢州市": (2126, 229),
    "舟山市": (2100, 117),
    "台州市": (6240, 671),
    "丽水市": (1964, 251),
}

BEIJING_DISTRICT_STATS: dict[str, tuple[float, float]] = {
    "东城区": (3281, 70),
    "西城区": (5700, 111),
    "朝阳区": (7900, 345),
    "丰台区": (2300, 201),
    "石景山区": (1050, 56),
    "海淀区": (11000, 313),
    "门头沟区": (250, 39),
    "房山区": (950, 132),
    "通州区": (1300, 184),
    "顺义区": (1300, 132),
    "昌平区": (1500, 227),
    "大兴区": (1600, 199),
    "怀柔区": (450, 28),
    "平谷区": (350, 46),
    "密云区": (400, 52),
    "延庆区": (230, 35),
}

GUANGZHOU_DISTRICT_STATS: dict[str, tuple[float, float]] = {
    "荔湾区": (1271, 112),
    "越秀区": (3688, 103),
    "海珠区": (2760, 111),
    "天河区": (6552, 224),
    "白云区": (2800, 226),
    "黄埔区": (4315, 117),
    "番禺区": (2980, 280),
    "花都区": (1850, 165),
    "南沙区": (2328, 93),
    "从化区": (500, 73),
    "增城区": (1400, 156),
}


def _read_geojson(name: str) -> dict:
    path = BASE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"缺少边界文件: {path}（先运行 scripts/download_test_data.py）")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_geojson(name: str, data: dict) -> None:
    (BASE_DIR / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"生成 {name}: {len(data.get('features', []))} 个要素")


def derive_point_layers() -> None:
    """从边界 center 字段派生点图层（省会/市/区县政府驻地示意点）"""
    plan = [
        ("china_provinces_full.geojson", "china_capitals_points.geojson"),
        ("beijing_districts.geojson", "beijing_districts_points.geojson"),
        ("guangdong_cities.geojson", "guangdong_cities_points.geojson"),
        ("sichuan_cities.geojson", "sichuan_cities_points.geojson"),
        ("zhejiang_cities.geojson", "zhejiang_cities_points.geojson"),
    ]
    for src, out in plan:
        data = _read_geojson(src)
        features = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            center = props.get("center")
            if not center or not props.get("name"):
                continue
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "name": props.get("name"),
                        "adcode": props.get("adcode"),
                        "level": props.get("level"),
                    },
                    "geometry": {"type": "Point", "coordinates": center},
                }
            )
        _write_geojson(out, {"type": "FeatureCollection", "features": features})


def augment_stats_layers() -> None:
    """边界 + 演示统计字段 → 可直接做面分级设色的图层"""
    plan = [
        ("china_provinces_full.geojson", "china_province_stats.geojson", PROVINCE_STATS),
        ("guangdong_cities.geojson", "guangdong_cities_stats.geojson", GUANGDONG_STATS),
        ("sichuan_cities.geojson", "sichuan_cities_stats.geojson", SICHUAN_STATS),
        ("zhejiang_cities.geojson", "zhejiang_cities_stats.geojson", ZHEJIANG_STATS),
        ("beijing_districts.geojson", "beijing_districts_stats.geojson", BEIJING_DISTRICT_STATS),
        (
            "guangzhou_districts.geojson",
            "guangzhou_districts_stats.geojson",
            GUANGZHOU_DISTRICT_STATS,
        ),
    ]
    for src, out, stats in plan:
        data = _read_geojson(src)
        missing = []
        matched = 0
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            name = props.get("name")
            stat = stats.get(name)
            if stat is None:
                missing.append(name)
                continue
            props["gdp_2023"] = stat[0]
            props["pop_2023"] = stat[1]
            matched += 1
        _write_geojson(out, data)
        print(f"  -> 匹配 {matched} 个，缺失 {missing if missing else '无'}")


def build_population_csv() -> None:
    """省级人口/GDP CSV（短名 + 省会坐标，供 load_data 点聚合分级设色）"""
    data = _read_geojson("china_provinces_full.geojson")
    rows = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        name = props.get("name")
        stat = PROVINCE_STATS.get(name)
        if not stat or not name:
            continue
        short = (
            name.replace("壮族自治区", "")
            .replace("维吾尔自治区", "")
            .replace("回族自治区", "")
            .replace("特别行政区", "")
            .replace("自治区", "")
            .replace("省", "")
            .replace("市", "")
        )
        center = props.get("center") or props.get("centroid")
        if not center:
            continue
        rows.append(
            {
                "province": short,
                "gdp": stat[0],
                "pop": stat[1],
                "lon": center[0],
                "lat": center[1],
            }
        )
    out = DEMO_DIR / "china_population.csv"
    lines = ["province,gdp,pop,lon,lat"]
    for row in rows:
        lines.append(
            f"{row['province']},{row['gdp']},{row['pop']},{row['lon']:.4f},{row['lat']:.4f}"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"生成 {out.name}: {len(rows)} 行")


def build_poi_csv() -> None:
    """合成 POI 点数据（北京/上海/广州/深圳/成都范围内）"""
    rng = random.Random(42)
    cities = [
        ("北京", 116.4074, 39.9042),
        ("上海", 121.4737, 31.2304),
        ("广州", 113.2644, 23.1291),
        ("深圳", 114.0579, 22.5431),
        ("成都", 104.0665, 30.5723),
    ]
    types = ["学校", "医院", "商场", "公园", "地铁站"]
    names = [
        "示例一中",
        "示例二中",
        "中心医院",
        "市人民医院",
        "购物中心",
        "万象城",
        "滨江公园",
        "人民公园",
        "地铁1号线站",
        "地铁2号线站",
    ]
    rows = ["id,name,type,city,lon,lat"]
    idx = 1
    for city, lon0, lat0 in cities:
        for _ in range(8):
            lon = round(lon0 + rng.uniform(-0.25, 0.25), 6)
            lat = round(lat0 + rng.uniform(-0.2, 0.2), 6)
            name = rng.choice(names)
            kind = rng.choice(types)
            rows.append(f"{idx},{name},{kind},{city},{lon},{lat}")
            idx += 1
    out = DEMO_DIR / "poi_demo.csv"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"生成 {out.name}: {idx - 1} 行（合成数据）")


def build_rivers() -> None:
    """主要河流示意线（长江/黄河/珠江/淮河/海河/松花江）"""
    rivers = [
        (
            "长江",
            [
                (90.5, 33.3),
                (97.2, 31.6),
                (99.7, 30.5),
                (101.8, 29.0),
                (104.1, 28.8),
                (107.4, 29.9),
                (109.3, 30.5),
                (111.3, 30.3),
                (113.4, 30.2),
                (114.3, 30.6),
                (116.4, 30.7),
                (118.6, 31.0),
                (120.9, 31.2),
                (121.9, 31.4),
            ],
        ),
        (
            "黄河",
            [
                (96.2, 34.7),
                (99.6, 36.1),
                (103.8, 36.1),
                (106.3, 36.5),
                (108.7, 37.9),
                (110.2, 38.8),
                (111.4, 40.2),
                (113.5, 40.0),
                (114.8, 38.9),
                (116.5, 38.0),
                (118.4, 37.4),
                (119.2, 37.7),
            ],
        ),
        (
            "珠江",
            [
                (103.6, 24.0),
                (105.5, 23.6),
                (107.5, 23.8),
                (110.2, 23.6),
                (112.0, 23.1),
                (113.2, 23.1),
                (113.6, 22.8),
            ],
        ),
        ("淮河", [(112.3, 32.4), (114.0, 32.7), (116.0, 33.0), (118.3, 33.1), (120.3, 33.9)]),
        ("海河", [(114.2, 38.0), (116.3, 39.0), (117.2, 39.1)]),
        ("松花江", [(125.0, 44.5), (126.0, 45.5), (128.0, 45.9), (130.5, 46.5), (132.0, 47.7)]),
    ]
    features = []
    for name, coords in rivers:
        features.append(
            {
                "type": "Feature",
                "properties": {"name": name, "kind": "river"},
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
    _write_geojson(
        "major_rivers.geojson",
        {"type": "FeatureCollection", "features": features},
    )


def build_dem_raster() -> None:
    """生成北京范围演示 DEM 栅格（100x100，仅用于 load_raster 测试）"""
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds

    width, height = 100, 100
    xs = np.linspace(0, 1, width)
    ys = np.linspace(0, 1, height)
    gx, gy = np.meshgrid(xs, ys)
    dem = 200 + 300 * gy + 150 * np.sin(gx * 6) * np.cos(gy * 5) + 80 * np.sin(gx * 12)
    out = BASE_DIR / "dem_demo.tif"
    with rasterio.open(
        out,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_bounds(115.4, 39.4, 117.5, 41.1, width, height),
    ) as dst:
        dst.write(dem.astype("float32"), 1)
    print(f"生成 {out.name}: {width}x{height} float32")


def fix_bench_cities() -> None:
    """修复 gis_bench_data/cities.geojson 的城市名乱码"""
    path = BENCH_DIR / "cities.geojson"
    data = json.loads(path.read_text(encoding="utf-8"))
    fixes = [
        (116.4, 39.9, "北京"),
        (121.5, 31.2, "上海"),
        (113.3, 23.1, "广州"),
    ]
    for feature, (lon, lat, name) in zip(data.get("features", []), fixes, strict=False):
        feature["properties"]["city"] = name
        feature["geometry"]["coordinates"] = [lon, lat]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"修复 {path.name}")


def main() -> int:
    for name in (
        "china_province.geojson",
        "beijing_districts.geojson",
        "guangdong_cities.geojson",
        "sichuan_cities.geojson",
        "zhejiang_cities.geojson",
        "guangzhou_districts.geojson",
        "china_provinces_full.geojson",
    ):
        if not (BASE_DIR / name).exists():
            print(f"缺少 {name}，请先运行 scripts/download_test_data.py")
            return 1
    derive_point_layers()
    augment_stats_layers()
    build_population_csv()
    build_poi_csv()
    build_rivers()
    build_dem_raster()
    fix_bench_cities()
    print("全部生成完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
