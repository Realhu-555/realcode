"""QGIS 引擎 9 个工具验证 — PyQGIS worker 真实执行 + 与 GeoPandas 引擎对照

环境无 QGIS 时自动 skip（Gate 2 验收：同一批用例在两种引擎下产物与摘要 diff 通过）。
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box
from src.gis_toolkit.engine import GisEngineError, create_gis_engine
from src.gis_toolkit.qgis_engine import QgsEngine, _find_qgis_prefix


def _qgis_available() -> bool:
    try:
        _find_qgis_prefix()
        return True
    except Exception:
        return False


@pytest.fixture()
def point_csv(tmp_path):
    p = tmp_path / "points.csv"
    p.write_text(
        "province,gdp,lon,lat\n北京,100,116.4,39.9\n上海,200,121.5,31.2\n广东,150,113.3,23.1\n",
        encoding="utf-8",
    )
    return str(p)


@pytest.fixture()
def poly_a(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"name": ["A"], "val": [1]}, geometry=[box(0, 0, 10, 10)], crs="EPSG:4326"
    )
    p = tmp_path / "poly_a.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return str(p)


@pytest.fixture()
def poly_b(tmp_path):
    gdf = gpd.GeoDataFrame(
        {"name": ["B"], "val": [2]}, geometry=[box(5, 0, 15, 10)], crs="EPSG:4326"
    )
    p = tmp_path / "poly_b.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return str(p)


@pytest.fixture()
def qgis_engine(tmp_path):
    """启动一次 QGIS worker，测试结束关闭"""
    if not _qgis_available():
        pytest.skip("本机未安装 QGIS，跳过 QGIS 引擎测试")
    eng = QgsEngine(out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)])
    yield eng
    eng.close()


def test_load_data_csv(point_csv, qgis_engine):
    res = qgis_engine.load_data(point_csv)
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 3
    assert set(res["layer"]["columns"]) == {"province", "gdp", "lon", "lat"}
    assert res["layer"]["crs"] == "EPSG:4326"
    assert res["layer"]["geometry_type"] == "Point"


def test_inspect_data(point_csv, qgis_engine):
    qgis_engine.load_data(point_csv)
    res = qgis_engine.inspect_data()
    assert res["status"] == "ok"
    assert len(res["bounds"]) == 4
    assert len(res["sample_rows"]) == 3
    assert res["rows"] == 3


def test_buffer(point_csv, qgis_engine):
    qgis_engine.load_data(point_csv)
    res = qgis_engine.buffer(0.1)
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 3
    assert res["layer"]["geometry_type"] == "MultiPolygon"


def test_overlay_matches_geopandas(poly_a, poly_b, qgis_engine):
    """???????? geopandas ???Gate 2 diff ???"""
    gdf_a = gpd.read_file(poly_a)
    gdf_b = gpd.read_file(poly_b)
    for how in ("intersection", "union", "difference", "symmetric_difference"):
        qgis_engine.load_data(poly_a)  # ????? A?????????
        res = qgis_engine.overlay(poly_b, how)
        g = gpd.overlay(gdf_a, gdf_b, how=how)
        assert res["status"] == "ok"
        assert res["layer"]["rows"] == len(g), f"overlay {how} ?????: {res['layer']['rows']} vs {len(g)}"


def test_choropleth(point_csv, qgis_engine):
    qgis_engine.load_data(point_csv)
    res = qgis_engine.choropleth("gdp", "Quantiles", 3, "choropleth.png")
    assert res["status"] == "ok"
    assert res["size_bytes"] > 0
    assert len(res["classes"]) == 3
    assert (qgis_engine.out_dir / "choropleth.png").is_file()


def test_scatter_plot(point_csv, qgis_engine):
    qgis_engine.load_data(point_csv)
    res = qgis_engine.scatter_plot("gdp", "lon", "scatter.png")
    assert res["status"] == "ok"
    assert res["size_bytes"] > 0
    assert (qgis_engine.out_dir / "scatter.png").is_file()


def test_summarize(point_csv, qgis_engine):
    qgis_engine.load_data(point_csv)
    res = qgis_engine.summarize("gdp", "province", "sum", "summary.csv")
    assert res["status"] == "ok"
    assert res["summary_rows"] == 3
    out_csv = qgis_engine.out_dir / "summary.csv"
    assert out_csv.is_file()
    df = pd.read_csv(out_csv, encoding="utf-8-sig")
    assert df["gdp"].sum() == 450


def test_export_geojson(poly_a, qgis_engine):
    qgis_engine.load_data(poly_a)
    res = qgis_engine.export_geojson("layer.geojson")
    assert res["status"] == "ok"
    assert (qgis_engine.out_dir / "layer.geojson").is_file()
    assert res["size_bytes"] > 0


def test_finish_checks_outputs(point_csv, qgis_engine):
    qgis_engine.load_data(point_csv)
    res = qgis_engine.finish(["not_exists.png"], "完成")
    assert res["status"] == "finished"
    assert "not_exists.png" not in res["outputs"]


def test_snapshot(point_csv, qgis_engine, tmp_path):
    qgis_engine.load_data(point_csv)
    snap = tmp_path / "snap.geojson"
    qgis_engine.save_layer_snapshot(str(snap))
    assert snap.is_file()
    gdf = gpd.read_file(snap)
    assert len(gdf) == 3


def test_engine_switch_creates_qgs(tmp_path):
    if not _qgis_available():
        pytest.skip("本机未安装 QGIS，跳过 QGIS 引擎测试")
    eng = create_gis_engine(engine="qgis", out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)])
    assert isinstance(eng, QgsEngine)
    eng.close()


def test_unknown_engine_rejected():
    with pytest.raises(GisEngineError):
        create_gis_engine(engine="mars")


def test_whitelist_rejects_outside(tmp_path, point_csv, qgis_engine):
    qgis_engine._roots = [(tmp_path / "allowed").resolve()]
    (tmp_path / "allowed").mkdir(exist_ok=True)
    with pytest.raises(GisEngineError, match="白名单"):
        qgis_engine.load_data(point_csv)
