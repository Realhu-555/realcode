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


# ── P0 新工具：join_by_location / voronoi / crs / list_layers ──────────

def test_join_by_location_matches_geopandas(tmp_path, qgis_engine):
    """空间连接（within）与 geopandas 对照：行数与并入属性一致"""
    inner = tmp_path / "inner_points.csv"
    inner.write_text("name,lon,lat\np1,2,2\np2,8,8\np3,50,50\n", encoding="utf-8")
    poly = tmp_path / "poly_a.geojson"
    gpd.GeoDataFrame(
        {"region": ["A"]}, geometry=[box(0, 0, 10, 10)], crs="EPSG:4326"
    ).to_file(poly, driver="GeoJSON")

    # geopandas 对照（CSV 读出来是 DataFrame，显式构造点）
    gpd_pts = gpd.GeoDataFrame(
        {"name": ["p1", "p2", "p3"]},
        geometry=gpd.points_from_xy([2, 8, 50], [2, 8, 50]),
        crs="EPSG:4326",
    )
    gpd_poly = gpd.read_file(poly)
    g = gpd.sjoin(gpd_pts, gpd_poly, how="inner", predicate="within")

    qgis_engine.load_data(str(inner))
    res = qgis_engine.join_by_location(str(poly), predicate="within")
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == len(g)
    assert "region" in res["layer"]["columns"]


def test_voronoi(point_csv, qgis_engine):
    """泰森多边形：点图层 → 面图层"""
    qgis_engine.load_data(point_csv)
    res = qgis_engine.voronoi()
    assert res["status"] == "ok"
    assert res["layer"]["geometry_type"] == "Polygon"
    assert res["layer"]["rows"] >= 3


def test_get_crs_and_set_crs(point_csv, qgis_engine):
    """get_crs / set_crs"""
    qgis_engine.load_data(point_csv)
    info = qgis_engine.get_crs()
    assert info["epsg"] == 4326
    res = qgis_engine.set_crs("EPSG:3857")
    assert res["status"] == "ok"
    assert qgis_engine.get_crs()["crs"] == "EPSG:3857"
    with pytest.raises(GisEngineError, match="无效坐标系"):
        qgis_engine.set_crs("NOT_A_CRS")


def test_list_layers(point_csv, qgis_engine):
    """list_layers 状态快照"""
    snap = qgis_engine.list_layers()
    assert snap["status"] == "ok"
    assert snap["has_layer"] is False
    qgis_engine.load_data(point_csv)
    snap = qgis_engine.list_layers()
    assert snap["has_layer"] is True
    assert snap["layer"]["rows"] == 3
    assert snap["out_dir"]


# ── P1 新工具：field_statistics / unique_values / transform_coords / render_map ──

def test_field_statistics_matches_geopandas(point_csv, qgis_engine):
    """字段统计与 geopandas 对照（count/mean/min/max）"""
    df = pd.read_csv(point_csv)
    expected = {
        "count": int(df["gdp"].count()),
        "mean": float(df["gdp"].mean()),
        "min": float(df["gdp"].min()),
        "max": float(df["gdp"].max()),
    }
    qgis_engine.load_data(point_csv)
    res = qgis_engine.field_statistics("gdp")
    assert res["status"] == "ok"
    assert res["count"] == expected["count"]
    assert abs(res["mean"] - expected["mean"]) < 1e-6
    assert abs(res["min"] - expected["min"]) < 1e-6
    assert abs(res["max"] - expected["max"]) < 1e-6


def test_unique_values(point_csv, qgis_engine):
    """唯一取值"""
    qgis_engine.load_data(point_csv)
    res = qgis_engine.unique_values("province")
    assert res["status"] == "ok"
    assert res["count"] == 3
    assert len(res["values"]) == 3


def test_transform_coords(point_csv, qgis_engine):
    """重投影：CRS 变为目标"""
    qgis_engine.load_data(point_csv)
    res = qgis_engine.transform_coords("EPSG:3857")
    assert res["status"] == "ok"
    assert qgis_engine.get_crs()["crs"] == "EPSG:3857"
    with pytest.raises(GisEngineError, match="无效坐标系"):
        qgis_engine.transform_coords("NOT_A_CRS")


def test_render_map(point_csv, qgis_engine):
    """渲染地图输出 PNG"""
    qgis_engine.load_data(point_csv)
    res = qgis_engine.render_map(output="map.png")
    assert res["status"] == "ok"
    assert res["size_bytes"] > 0
    assert (qgis_engine.out_dir / "map.png").is_file()


def test_run_algorithm_matches_geopandas(point_csv, qgis_engine):
    """dissolve 与 geopandas 对照：行数一致"""
    df = pd.read_csv(point_csv)
    expected = df.groupby("province").ngroups

    qgis_engine.load_data(point_csv)
    res = qgis_engine.run_algorithm("dissolve", {"field": "province"})
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == expected

    qgis_engine.load_data(point_csv)
    res = qgis_engine.run_algorithm("centroids")
    assert res["status"] == "ok"
    assert res["layer"]["geometry_type"] in ("Point", "MultiPoint")

    with pytest.raises(GisEngineError, match="未知算法"):
        qgis_engine.run_algorithm("evil_script")


def test_load_raster(point_csv, qgis_engine, tmp_path):
    """load_raster：QGIS 加载 GeoTIFF 返回元数据"""
    import numpy as np
    import rasterio

    tif = tmp_path / "dem.tif"
    with rasterio.open(
        tif,
        "w",
        driver="GTiff",
        width=4,
        height=3,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=rasterio.transform.from_bounds(116, 39, 117, 40, 4, 3),
    ) as dst:
        dst.write(np.ones((1, 3, 4), dtype="float32"))

    res = qgis_engine.load_raster(str(tif))
    assert res["status"] == "ok"
    assert res["raster"]["width"] == 4
    assert res["raster"]["height"] == 3
    assert res["raster"]["bands"] == 1
    assert res["raster"]["crs"] == "EPSG:4326"


def test_summarize_sorted_desc(point_csv, qgis_engine):
    """summarize 按结果列降序排序（Top 名单）"""
    qgis_engine.load_data(point_csv)
    qgis_engine.summarize(
        "gdp",
        groupby="province",
        agg="sum",
        output="rank.csv",
        sort_by="gdp",
        desc=True,
    )
    df = pd.read_csv(qgis_engine.out_dir / "rank.csv")
    assert list(df["province"]) == ["上海", "广东", "北京"]  # 200, 150, 100 降序


def _writable_points(tmp_path):
    """可编辑的 GeoJSON 点图层（CSV/delimitedtext 只读，不能编辑）"""
    gdf = gpd.GeoDataFrame(
        {"name": ["A", "B"], "val": [1, 2]},
        geometry=gpd.points_from_xy([116, 117], [39, 40]),
        crs="EPSG:4326",
    )
    p = tmp_path / "pts.geojson"
    gdf.to_file(p, driver="GeoJSON")
    return str(p)


def test_edit_session_add_commit(tmp_path, qgis_engine):
    """编辑会话：start → add → commit（QGIS EditBuffer）"""
    qgis_engine.load_data(_writable_points(tmp_path))
    assert qgis_engine.start_editing()["status"] == "ok"
    assert qgis_engine.add_features("POINT(119 32)", {"name": "C"})["status"] == "ok"
    qgis_engine.commit_edits()
    assert qgis_engine.list_layers()["layer"]["rows"] == 3


def test_edit_session_rollback(tmp_path, qgis_engine):
    """编辑会话：rollback 丢弃修改"""
    qgis_engine.load_data(_writable_points(tmp_path))
    qgis_engine.start_editing()
    qgis_engine.delete_features([0])
    qgis_engine.rollback_edits()
    assert qgis_engine.list_layers()["layer"]["rows"] == 2


def test_edit_update_and_delete(tmp_path, qgis_engine):
    """编辑会话：update 属性 + delete 要素"""
    qgis_engine.load_data(_writable_points(tmp_path))
    qgis_engine.start_editing()
    res = qgis_engine.update_features("name = 'A'", {"val": 99})
    assert res["status"] == "ok" and "1 个" in res["message"]
    qgis_engine.delete_features([1])
    qgis_engine.commit_edits()
    assert qgis_engine.list_layers()["layer"]["rows"] == 1


def test_edit_requires_start(tmp_path, qgis_engine):
    """未 start_editing 时编辑报错"""
    qgis_engine.load_data(_writable_points(tmp_path))
    with pytest.raises(GisEngineError, match="未开始编辑"):
        qgis_engine.add_features("POINT(119 32)")


def test_categorized(point_csv, qgis_engine):
    """分类设色：按类别出图（QGIS CategorizedRenderer）"""
    qgis_engine.load_data(point_csv)
    res = qgis_engine.categorized("province", output="cat.png")
    assert res["status"] == "ok"
    assert res["classes"] == 3
    assert (qgis_engine.out_dir / "cat.png").is_file()


def test_set_labeling(point_csv, qgis_engine):
    """设置标注"""
    qgis_engine.load_data(point_csv)
    res = qgis_engine.set_labeling("province")
    assert res["status"] == "ok"
    assert "启用" in res["message"]
    res = qgis_engine.set_labeling("province", enabled=False)
    assert "关闭" in res["message"]
    with pytest.raises(GisEngineError, match="列不存在"):
        qgis_engine.set_labeling("nope")
