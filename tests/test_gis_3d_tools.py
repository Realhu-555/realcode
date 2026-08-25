"""P3 阶段 2：3D 城市可视化工具单测（download_osm_buildings / render_3d）。

覆盖：高度估算、height_m 字段补齐、render_3d 产物与 URL、download bbox 校验、
Overpass 成功/失败路径（mock 网络）、schema 自动暴露。
"""

import json

import geopandas as gpd
import pytest
import src.gis_toolkit.engine as engine_mod
from shapely.geometry import box
from src.gis_toolkit.engine import GisEngine, GisEngineError
from src.gis_toolkit.schemas import TOOL_SCHEMAS

# ── 高度估算 ──


def test_estimate_height_priority():
    assert engine_mod._estimate_height({"height": "21"}) == 21.0
    assert engine_mod._estimate_height({"height": "12.5 m"}) == 12.5
    assert engine_mod._estimate_height({"building:levels": "4"}) == 12.0
    assert engine_mod._estimate_height({"building:levels": "3"}) == 9.0
    assert engine_mod._estimate_height({"building": "garage"}) == 4.0
    assert engine_mod._estimate_height({"building": "shed"}) == 3.0
    assert engine_mod._estimate_height({"building": "residential"}) == 10.0
    assert engine_mod._estimate_height({}) == 10.0


def test_apply_height_field():
    gdf = gpd.GeoDataFrame(
        {
            "name": ["a", "b", "c", "d"],
            "height": [None, "18m", None, None],
            "building:levels": [None, None, "5", None],
        },
        geometry=[box(i, i, i + 1, i + 1) for i in range(4)],
        crs="EPSG:4326",
    )
    out = engine_mod._apply_height_field(gdf)
    assert "height_m" in out.columns
    assert list(out["height_m"]) == [10.0, 18.0, 15.0, 10.0]


def test_apply_height_field_prefers_existing_height_m():
    gdf = gpd.GeoDataFrame(
        {"name": ["a"], "height_m": [30.0], "height": [5.0]},
        geometry=[box(0, 0, 1, 1)],
        crs="EPSG:4326",
    )
    out = engine_mod._apply_height_field(gdf)
    assert list(out["height_m"]) == [30.0]


# ── render_3d ──


def _engine(tmp_path, data_file=None):
    return GisEngine(
        data_file=data_file,
        out_dir=str(tmp_path / "out"),
        allowed_roots=[str(tmp_path)],
    )


def _poly_geojson(tmp_path, heights=None):
    heights = heights or [10.0, 20.0]
    gdf = gpd.GeoDataFrame(
        {"name": ["a", "b"], "height": heights},
        geometry=[box(0, 0, 1, 1), box(2, 2, 3, 3)],
        crs="EPSG:4326",
    )
    p = tmp_path / "polys.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return str(p)


def test_render_3d_creates_preview(tmp_path, monkeypatch):
    static_dir = tmp_path / "static" / "3d-demo"
    monkeypatch.setattr(engine_mod, "_3D_STATIC_DIR", static_dir)
    eng = _engine(tmp_path, data_file=_poly_geojson(tmp_path))
    res = eng.render_3d(output="test_preview")
    assert res["status"] == "ok"
    assert "3d_preview_url" in res
    assert res["3d_preview_url"].endswith("/3d-demo/?data=test_preview.geojson")
    out_file = static_dir / "test_preview.geojson"
    assert out_file.is_file()
    fc = json.loads(out_file.read_text(encoding="utf-8"))
    heights = [f["properties"]["height_m"] for f in fc["features"]]
    assert heights == [10.0, 20.0]


def test_render_3d_requires_layer(tmp_path):
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError):
        eng.render_3d()


# ── download_osm_buildings ──


def test_download_invalid_bbox(tmp_path):
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError):
        eng.download_osm_buildings("x", south=40, west=116, north=39, east=117)


class _FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _osm_payload(ways):
    return {"elements": ways}


def _way(oid, coords, tags):
    return {
        "type": "way",
        "id": oid,
        "tags": tags,
        "geometry": [{"lon": c[0], "lat": c[1]} for c in coords],
    }


def test_download_success(tmp_path, monkeypatch):
    monkeypatch.setattr(engine_mod, "_OSM_DATA_DIR", tmp_path)
    eng = _engine(tmp_path)
    payload = _osm_payload(
        [
            _way(1, [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)], {"building": "yes", "height": "21"}),
            _way(
                2,
                [(2, 2), (2, 3), (3, 3), (3, 2), (2, 2)],
                {"building": "yes", "building:levels": "4"},
            ),
            _way(3, [(4, 4), (4, 5), (5, 5)], {"building": "yes"}),  # 非法环（<3 点）丢弃
            {"type": "node", "id": 9, "lat": 0, "lon": 0},  # 非 way 忽略
        ]
    )
    monkeypatch.setattr(
        engine_mod.requests,
        "post",
        lambda *a, **k: _FakeResp(200, payload),
    )
    res = eng.download_osm_buildings(city="test_city", south=0, west=0, north=10, east=10)
    assert res["status"] == "ok"
    assert res["stats"]["total"] == 3
    assert res["stats"]["height_direct"] == 1
    assert res["stats"]["levels_used"] == 1
    out_file = tmp_path / "test_city_buildings.geojson"
    assert out_file.is_file()
    fc = json.loads(out_file.read_text(encoding="utf-8"))
    by_id = {f["properties"]["osm_id"]: f["properties"]["height_m"] for f in fc["features"]}
    assert by_id == {1: 21.0, 2: 12.0, 3: 10.0}
    # 多边形需闭合
    ring = fc["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]


def test_download_http_error(tmp_path, monkeypatch):
    monkeypatch.setattr(engine_mod, "_OSM_DATA_DIR", tmp_path)
    eng = _engine(tmp_path)
    monkeypatch.setattr(engine_mod.requests, "post", lambda *a, **k: _FakeResp(429, {}))
    with pytest.raises(GisEngineError, match="HTTP 429"):
        eng.download_osm_buildings("t", south=0, west=0, north=1, east=1)


def test_download_no_features(tmp_path, monkeypatch):
    monkeypatch.setattr(engine_mod, "_OSM_DATA_DIR", tmp_path)
    eng = _engine(tmp_path)
    monkeypatch.setattr(
        engine_mod.requests, "post", lambda *a, **k: _FakeResp(200, _osm_payload([]))
    )
    with pytest.raises(GisEngineError, match="没有建筑要素"):
        eng.download_osm_buildings("t", south=0, west=0, north=1, east=1)


# ── schema 自动暴露 ──


def test_schema_exposes_3d_tools():
    names = {t["function"]["name"] for t in TOOL_SCHEMAS}
    assert {"download_osm_buildings", "render_3d"} <= names


def test_engine_dispatch_has_3d_methods():
    eng = GisEngine(out_dir="data/gis_toolkit_out", allowed_roots=["data"])
    assert callable(getattr(eng, "download_osm_buildings", None))
    assert callable(getattr(eng, "render_3d", None))
    eng.finish([])
