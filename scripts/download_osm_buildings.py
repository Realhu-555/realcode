"""OSM 建筑轮廓下载器（GIS 3D 城市可视化 · 阶段 0）

从 Overpass API 按 bbox 下载建筑 way 轮廓，统一估算高度字段 height_m，
输出 GeoJSON（FeatureCollection），供 frontend/3d-demo 拉伸为 3D 体块。

高度估算策略（OSM 中国区高度字段覆盖低，必做）：
1. `height` 标签存在 → 直接使用（米）；
2. 否则 `building:levels` × 3.0 米/层；
3. 都没有 → 默认 10 米（building=garage 用 4 米）。

用法：
    python scripts/download_osm_buildings.py
    python scripts/download_osm_buildings.py --bbox 39.97,116.30,40.01,116.34
    python scripts/download_osm_buildings.py --out data/gis_3d/city.geojson

注意：
- OSM 数据为 ODbL 许可，展示需署名 © OpenStreetMap contributors；
- 高度为估算值，仅用于可视化演示，非测绘数据；
- Overpass 有频率/体积限制，演示固定用中关村小范围。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - 依赖缺失提示
    sys.exit("缺少依赖 requests，请先执行: pip install requests")

# 中关村-五道口默认范围（含清华/北大周边，约 4km×4km）
DEFAULT_BBOX = (39.97, 116.30, 40.01, 116.34)
DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
DEFAULT_OUT = (
    Path(__file__).resolve().parents[1] / "data" / "gis_3d" / "zhongguancun_buildings.geojson"
)

# building 类型 → 默认估算高度（米），未列出的用 DEFAULT_FLOOR_HEIGHT
BUILDING_DEFAULT_HEIGHTS = {
    "garage": 4.0,
    "garages": 4.0,
    "shed": 3.0,
    "hut": 3.0,
    "roof": 3.0,
}
DEFAULT_FLOOR_HEIGHT = 3.0  # 米/层
DEFAULT_HEIGHT = 10.0  # 无任何高度线索时的兜底（米）


def _parse_bbox(text: str) -> tuple[float, float, float, float]:
    """解析 "south,west,north,east" 为 float 四元组，校验数值合法"""
    parts = [float(p.strip()) for p in text.split(",")]
    if len(parts) != 4:
        raise SystemExit("--bbox 需为 south,west,north,east 四个逗号分隔的数值")
    south, west, north, east = parts
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise SystemExit(f"bbox 越界或不合法: {text!r}")
    return south, west, north, east


def build_overpass_query(south: float, west: float, north: float, east: float) -> str:
    """构造 Overpass QL：取 bbox 内所有 building way，带几何坐标"""
    return (
        f"[out:json][timeout:60];\n"
        f"(\n"
        f'  way["building"]({south},{west},{north},{east});\n'
        f");\n"
        f"out geom;\n"
    )


def estimate_height(tags: dict[str, str]) -> float:
    """按策略估算建筑高度（米），返回 (height_m, 依据说明) 由调用方自行处理"""
    raw = tags.get("height")
    if raw:
        try:
            # 兼容 "12.5" / "12.5 m" / "12.5m"
            value = float(str(raw).lower().replace("m", "").strip())
            if value > 0:
                return value
        except ValueError:
            pass
    levels = tags.get("building:levels")
    if levels:
        try:
            value = float(levels)
            if value > 0:
                return value * DEFAULT_FLOOR_HEIGHT
        except ValueError:
            pass
    return BUILDING_DEFAULT_HEIGHTS.get(tags.get("building", ""), DEFAULT_HEIGHT)


def _feature_from_way(way: dict[str, Any]) -> dict[str, Any] | None:
    """把 Overpass way 元素转为带 height_m 的 GeoJSON Feature；无有效几何返回 None"""
    geom = way.get("geometry")
    if not geom or len(geom) < 4:
        return None
    tags = way.get("tags", {})
    height_m = estimate_height(tags)
    # OSM lon/lat → GeoJSON [lon, lat]
    coords = [[p["lon"], p["lat"]] for p in geom]
    if coords[0] != coords[-1]:
        coords.append(list(coords[0]))  # 闭合环
    return {
        "type": "Feature",
        "properties": {
            "osm_id": way.get("id"),
            "building": tags.get("building", ""),
            "height": tags.get("height", ""),
            "building:levels": tags.get("building:levels", ""),
            "height_m": round(height_m, 2),
        },
        "geometry": {"type": "Polygon", "coordinates": [coords]},
    }


def download_buildings(
    bbox: tuple[float, float, float, float],
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: int = 90,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """请求 Overpass 并返回 (Feature 列表, 统计)"""
    query = build_overpass_query(*bbox)
    headers = {
        "User-Agent": "gis-3d-demo/0.1 (educational demo)",
        "Accept": "application/json",
    }
    resp = requests.post(endpoint, data={"data": query}, headers=headers, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    stats = {
        "elements": len(payload.get("elements", [])),
        "with_height": 0,
        "with_levels": 0,
        "estimated_default": 0,
    }
    features: list[dict[str, Any]] = []
    for way in payload.get("elements", []):
        if way.get("type") != "way":
            continue
        tags = way.get("tags", {})
        if tags.get("height"):
            stats["with_height"] += 1
        elif tags.get("building:levels"):
            stats["with_levels"] += 1
        else:
            stats["estimated_default"] += 1
        feature = _feature_from_way(way)
        if feature is not None:
            features.append(feature)
    return features, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--bbox",
        default=None,
        help="south,west,north,east（默认中关村-五道口范围）",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="输出 GeoJSON 路径（默认 data/gis_3d/zhongguancun_buildings.geojson）",
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Overpass API 端点")
    args = parser.parse_args(argv)

    bbox = _parse_bbox(args.bbox) if args.bbox else DEFAULT_BBOX
    print(f"正在请求 Overpass 下载 bbox={bbox} 的建筑轮廓 ...")
    try:
        features, stats = download_buildings(bbox, endpoint=args.endpoint)
    except requests.RequestException as exc:  # pragma: no cover - 网络失败提示
        print(f"下载失败: {exc}", file=sys.stderr)
        print("请检查网络或稍后重试；演示页可先用已有数据文件。", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fc = {
        "type": "FeatureCollection",
        "name": "OSM buildings (height estimated)",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)

    print(
        f"完成: {len(features)} 栋建筑 → {out_path}\n"
        f"高度来源: 直接 height={stats['with_height']} 栋 / "
        f"levels 估算={stats['with_levels']} 栋 / "
        f"默认估算={stats['estimated_default']} 栋"
    )
    print("提示: 建筑高度为估算值，仅用于可视化演示，非测绘数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
