"""P3 阶段0：scripts/download_osm_buildings.py 的高度估算 / 查询构造 / 几何生成"""

from pathlib import Path

from scripts.download_osm_buildings import (
    _feature_from_way,
    _parse_bbox,
    build_overpass_query,
    estimate_height,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "download_osm_buildings.py"


def test_build_overpass_query():
    q = build_overpass_query(39.97, 116.30, 40.01, 116.34)
    assert 'way["building"]' in q
    assert "(39.97,116.3,40.01,116.34)" in q.replace(" ", "")
    assert "out geom" in q


def test_parse_bbox_valid():
    assert _parse_bbox("39.97,116.30,40.01,116.34") == (39.97, 116.3, 40.01, 116.34)


def test_parse_bbox_invalid_raises():
    import pytest

    with pytest.raises(SystemExit):
        _parse_bbox("1,2,3")  # 数量不足
    with pytest.raises(SystemExit):
        _parse_bbox("40,116,39,117")  # south >= north


def test_estimate_height_direct():
    assert estimate_height({"height": "12.5"}) == 12.5
    assert estimate_height({"height": "12 m"}) == 12.0
    assert estimate_height({"height": "20m"}) == 20.0
    # 非法 height 值回退到 levels
    assert estimate_height({"height": "abc", "building:levels": "5"}) == 15.0


def test_estimate_height_levels():
    assert estimate_height({"building:levels": "6"}) == 18.0


def test_estimate_height_defaults():
    assert estimate_height({}) == 10.0
    assert estimate_height({"building": "garage"}) == 4.0
    assert estimate_height({"building": "shed"}) == 3.0


def test_feature_from_way_polygon():
    way = {
        "id": 42,
        "tags": {"building": "yes", "building:levels": "8"},
        "geometry": [
            {"lat": 39.99, "lon": 116.32},
            {"lat": 39.99, "lon": 116.33},
            {"lat": 39.98, "lon": 116.33},
            {"lat": 39.98, "lon": 116.32},
            {"lat": 39.99, "lon": 116.32},
        ],
    }
    f = _feature_from_way(way)
    assert f is not None
    assert f["properties"]["osm_id"] == 42
    assert f["properties"]["height_m"] == 24.0  # 8 层 × 3m
    ring = f["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]  # 闭合环
    assert f["geometry"]["type"] == "Polygon"


def test_feature_from_way_invalid_geometry():
    assert _feature_from_way({"id": 1, "tags": {}, "geometry": []}) is None
    assert _feature_from_way({"id": 2, "tags": {}, "geometry": [{"lat": 1, "lon": 2}] * 2}) is None
