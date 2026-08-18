"""GIS 引擎 9 个工具可用性验证 — 真实 GeoPandas 执行 + 产物断言"""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box
from src.gis_toolkit.engine import GisEngine, GisEngineError


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
    """10x10 矩形，左下角 (0,0)"""
    gdf = gpd.GeoDataFrame(
        {"name": ["A"], "val": [1]},
        geometry=[box(0, 0, 10, 10)],
        crs="EPSG:4326",
    )
    p = tmp_path / "poly_a.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return str(p)


@pytest.fixture()
def poly_b(tmp_path):
    """10x10 矩形，左下角 (5,0)，与 A 重叠 5x10"""
    gdf = gpd.GeoDataFrame(
        {"name": ["B"], "val": [2]},
        geometry=[box(5, 0, 15, 10)],
        crs="EPSG:4326",
    )
    p = tmp_path / "poly_b.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return str(p)


def _engine(tmp_path, data_file=None, allowed=None):
    return GisEngine(
        data_file=data_file,
        out_dir=str(tmp_path / "out"),
        allowed_roots=allowed or [str(tmp_path)],
    )


# ── load_data / inspect_data ──────────────────────────

def test_load_data_csv(point_csv, tmp_path):
    eng = _engine(tmp_path)
    res = eng.load_data(point_csv)
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 3
    assert set(res["layer"]["columns"]) == {"province", "gdp", "lon", "lat"}
    assert res["layer"]["crs"] == "EPSG:4326"
    assert res["layer"]["geometry_type"] == "Point"


def test_load_data_geojson(poly_a, tmp_path):
    eng = _engine(tmp_path)
    res = eng.load_data(poly_a)
    assert res["layer"]["rows"] == 1
    assert res["layer"]["geometry_type"] == "Polygon"


def test_load_data_rejects_whitelist_outside(tmp_path, point_csv):
    eng = _engine(tmp_path, allowed=[tmp_path / "allowed"])
    (tmp_path / "allowed").mkdir(exist_ok=True)
    with pytest.raises(GisEngineError, match="白名单"):
        eng.load_data(point_csv)


def test_inspect_data(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    res = eng.inspect_data()
    assert res["rows"] == 3
    assert len(res["bounds"]) == 4
    assert len(res["sample_rows"]) == 3
    assert res["crs"] == "EPSG:4326"


def test_inspect_without_layer(tmp_path):
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError, match="没有图层"):
        eng.inspect_data()


# ── buffer ────────────────────────────────────────────

def test_buffer_enlarges_area(poly_a, tmp_path):
    eng = _engine(tmp_path, data_file=poly_a)
    before = eng._layer.geometry.area.iloc[0]
    eng.buffer(1.0)
    after = eng._layer.geometry.area.iloc[0]
    assert after > before
    assert eng._layer.geometry.geom_type.iloc[0] in {"Polygon", "MultiPolygon"}


def test_buffer_without_layer(tmp_path):
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError, match="没有图层"):
        eng.buffer(1.0)


# ── overlay ───────────────────────────────────────────

def test_overlay_intersection(poly_a, poly_b, tmp_path):
    eng = _engine(tmp_path, data_file=poly_a)
    res = eng.overlay(poly_b, how="intersection")
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 1
    area = eng._layer.geometry.area.iloc[0]
    assert area == pytest.approx(50.0, rel=1e-6)  # 5 x 10 重叠区


def test_overlay_union(poly_a, poly_b, tmp_path):
    eng = _engine(tmp_path, data_file=poly_a)
    eng.overlay(poly_b, how="union")
    assert eng._layer.geometry.area.sum() == pytest.approx(150.0, rel=1e-6)


def test_overlay_rejects_bad_how(poly_a, poly_b, tmp_path):
    eng = _engine(tmp_path, data_file=poly_a)
    with pytest.raises(GisEngineError, match="how"):
        eng.overlay(poly_b, how="touch")


def test_overlay_rejects_crs_mismatch(poly_a, poly_b, tmp_path):
    eng = _engine(tmp_path, data_file=poly_a)
    bad = tmp_path / "bad_crs.geojson"
    gpd.GeoDataFrame(
        {"name": ["B"]},
        geometry=[box(5, 0, 15, 10)],
        crs="EPSG:3857",
    ).to_file(bad, driver="GeoJSON")
    with pytest.raises(GisEngineError, match="CRS"):
        eng.overlay(str(bad), how="intersection")


# ── choropleth / scatter_plot ─────────────────────────

def test_choropleth(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    res = eng.choropleth(column="gdp", scheme="Quantiles", k=3, output="map.png")
    assert res["status"] == "ok"
    assert res["size_bytes"] > 0
    assert (tmp_path / "out" / "map.png").stat().st_size > 0


def test_choropleth_missing_column(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    with pytest.raises(GisEngineError, match="列不存在"):
        eng.choropleth(column="nope", output="map.png")


def test_scatter_plot(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    res = eng.scatter_plot(x="lon", y="lat", output="scatter.png")
    assert res["status"] == "ok"
    assert res["size_bytes"] > 0


# ── summarize ─────────────────────────────────────────

def test_summarize_groupby(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    res = eng.summarize(column="gdp", groupby="province", agg="sum", output="s.csv")
    assert res["summary_rows"] == 3
    out = pd.read_csv(tmp_path / "out" / "s.csv")
    assert set(out["province"]) == {"北京", "上海", "广东"}
    assert out.set_index("province").loc["北京", "gdp"] == 100


def test_summarize_global_agg(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    res = eng.summarize(column="gdp", agg="sum", output="total.csv")
    assert res["summary_rows"] == 1
    out = pd.read_csv(tmp_path / "out" / "total.csv")
    assert out["gdp"].iloc[0] == 450


def test_summarize_rejects_bad_agg(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    with pytest.raises(GisEngineError, match="agg"):
        eng.summarize(column="gdp", agg="median", output="s.csv")


# ── export_geojson / finish ───────────────────────────

def test_export_geojson(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    res = eng.export_geojson(output="pts.geojson")
    assert res["status"] == "ok"
    back = gpd.read_file(tmp_path / "out" / "pts.geojson")
    assert len(back) == 3


def test_finish_declares_only_real_outputs(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    eng.choropleth(column="gdp", output="real.png")
    res = eng.finish(outputs=["real.png", "fake.png"], summary="完成")
    assert res["status"] == "finished"
    assert res["outputs"] == ["real.png"]  # 谎报的 fake.png 被剔除


# ── 文件名净化 / 输入白名单 ───────────────────────────

def test_output_filename_rejects_path_traversal(point_csv, tmp_path):
    eng = _engine(tmp_path, data_file=point_csv)
    with pytest.raises(GisEngineError, match="非法产物文件名"):
        eng.choropleth(column="gdp", output="../evil.png")
    with pytest.raises(GisEngineError, match="非法产物文件名"):
        eng.export_geojson(output="a/b.geojson")


def test_load_data_rejects_missing_file(tmp_path):
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError, match="文件不存在"):
        eng.load_data(str(tmp_path / "nope.csv"))


def test_csv_without_coords_rejected(tmp_path):
    p = tmp_path / "no_xy.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError, match="经纬度"):
        eng.load_data(str(p))
