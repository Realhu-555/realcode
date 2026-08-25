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


def test_summarize_sorted_desc(tmp_path):
    """summarize 按结果列降序排序（Top 名单）"""
    pts = tmp_path / "pts.csv"
    pts.write_text(
        "province,gdp,lon,lat\nA,10,116,39\nB,30,117,40\nC,20,118,41\n",
        encoding="utf-8",
    )
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    eng.summarize(
        "gdp",
        groupby="province",
        agg="sum",
        output="rank.csv",
        sort_by="gdp",
        desc=True,
    )
    df = pd.read_csv(tmp_path / "out" / "rank.csv")
    assert list(df["province"]) == ["B", "C", "A"]  # 30, 20, 10 降序


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


# ── P0 新工具：join_by_location / voronoi / crs / list_layers ──────────


def test_join_by_location_point_in_poly(tmp_path):
    """空间连接：点归属面（within），另一图层属性并入"""
    inner = tmp_path / "inner_points.csv"
    inner.write_text("name,lon,lat\np1,2,2\np2,8,8\n", encoding="utf-8")
    poly = tmp_path / "poly_a.geojson"
    gpd.GeoDataFrame(
        {"region": ["A"]},
        geometry=[box(0, 0, 10, 10)],
        crs="EPSG:4326",
    ).to_file(poly, driver="GeoJSON")

    eng = _engine(tmp_path)
    eng.load_data(str(inner))
    res = eng.join_by_location(str(poly), predicate="within")
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 2
    assert "region" in res["layer"]["columns"]


def test_join_by_location_crs_mismatch(tmp_path):
    """CRS 不一致时报错"""
    inner = tmp_path / "pts.csv"
    inner.write_text("name,lon,lat\np1,2,2\n", encoding="utf-8")
    other = tmp_path / "poly_3857.geojson"
    gpd.GeoDataFrame(
        {"name": ["X"]},
        geometry=[box(0, 0, 10, 10)],
        crs="EPSG:3857",
    ).to_file(other, driver="GeoJSON")

    eng = _engine(tmp_path)
    eng.load_data(str(inner))
    with pytest.raises(GisEngineError, match="CRS"):
        eng.join_by_location(str(other))


def test_voronoi_from_points(tmp_path):
    """泰森多边形：点图层 → 面图层"""
    pts = tmp_path / "pts.csv"
    pts.write_text("id,lon,lat\n1,0,0\n2,10,0\n3,5,10\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.voronoi()
    assert res["status"] == "ok"
    assert res["layer"]["geometry_type"] in ("Polygon", "MultiPolygon")
    assert res["layer"]["rows"] >= 3


def test_voronoi_requires_points(tmp_path):
    """非点图层 voronoi 报错"""
    poly = tmp_path / "poly.geojson"
    gpd.GeoDataFrame(
        {"name": ["A"]},
        geometry=[box(0, 0, 10, 10)],
        crs="EPSG:4326",
    ).to_file(poly, driver="GeoJSON")
    eng = _engine(tmp_path)
    eng.load_data(str(poly))
    with pytest.raises(GisEngineError, match="点图层"):
        eng.voronoi()


def test_get_crs_and_set_crs(tmp_path):
    """get_crs 返回坐标系；set_crs 重设声明；非法 CRS 报错"""
    pts = tmp_path / "pts.csv"
    pts.write_text("id,lon,lat\n1,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))

    info = eng.get_crs()
    assert info["status"] == "ok"
    assert info["epsg"] == 4326

    res = eng.set_crs("EPSG:3857")
    assert res["status"] == "ok"
    assert eng.get_crs()["crs"] == "EPSG:3857"

    with pytest.raises(GisEngineError, match="无效坐标系"):
        eng.set_crs("NOT_A_CRS")


def test_list_layers_snapshot(tmp_path):
    """list_layers 返回会话状态快照"""
    pts = tmp_path / "pts.csv"
    pts.write_text("id,lon,lat\n1,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    snap = eng.list_layers()
    assert snap["status"] == "ok"
    assert snap["has_layer"] is False

    eng.load_data(str(pts))
    eng.summarize("id", agg="count", output="s.csv")
    snap = eng.list_layers()
    assert snap["has_layer"] is True
    assert snap["layer"]["rows"] == 1
    assert "s.csv" in snap["outputs"]
    assert snap["output_paths"]
    assert snap["out_dir"]


# ── P1 新工具：field_statistics / unique_values / transform_coords / render_map ──


def test_field_statistics(tmp_path):
    """字段统计：数值列返回 count/mean/min/max/missing"""
    pts = tmp_path / "pts.csv"
    pts.write_text("id,val,lon,lat\n1,10,116,39\n2,20,117,40\n3,,118,41\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.field_statistics("val")
    assert res["status"] == "ok"
    assert res["count"] == 2
    assert res["mean"] == 15.0
    assert res["min"] == 10
    assert res["max"] == 20
    assert res["missing"] == 1


def test_field_statistics_missing_column(tmp_path):
    pts = tmp_path / "pts.csv"
    pts.write_text("id,lon,lat\n1,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    with pytest.raises(GisEngineError, match="列不存在"):
        eng.field_statistics("nope")


def test_unique_values(tmp_path):
    """唯一取值：分类列去重"""
    pts = tmp_path / "pts.csv"
    pts.write_text("cat,lon,lat\nA,116,39\nB,117,40\nA,118,41\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.unique_values("cat")
    assert res["status"] == "ok"
    assert res["count"] == 2
    assert set(res["values"]) == {"A", "B"}
    assert res["truncated"] is False


def test_transform_coords(tmp_path):
    """重投影：EPSG:4326 → EPSG:3857，坐标值变化"""
    pts = tmp_path / "pts.csv"
    pts.write_text("id,lon,lat\n1,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.transform_coords("EPSG:3857")
    assert res["status"] == "ok"
    assert eng.get_crs()["crs"] == "EPSG:3857"
    with pytest.raises(GisEngineError, match="无效坐标系"):
        eng.transform_coords("NOT_A_CRS")


def test_render_map(tmp_path):
    """渲染地图：输出 PNG"""
    pts = tmp_path / "pts.csv"
    pts.write_text("id,lon,lat\n1,116,39\n2,117,40\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.render_map(output="map.png")
    assert res["status"] == "ok"
    assert res["size_bytes"] > 0
    assert (tmp_path / "out" / "map.png").is_file()


def test_run_algorithm_dissolve(tmp_path):
    """dissolve：按字段融合要素"""
    pts = tmp_path / "pts.csv"
    pts.write_text("cat,lon,lat\nA,116,39\nA,117,40\nB,118,41\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.run_algorithm("dissolve", {"field": "cat"})
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 2


def test_run_algorithm_centroids(tmp_path):
    """centroids：要素质心"""
    poly = tmp_path / "poly.geojson"
    gpd.GeoDataFrame({"name": ["A"]}, geometry=[box(0, 0, 10, 10)], crs="EPSG:4326").to_file(
        poly, driver="GeoJSON"
    )
    eng = _engine(tmp_path)
    eng.load_data(str(poly))
    res = eng.run_algorithm("centroids")
    assert res["status"] == "ok"
    assert res["layer"]["geometry_type"] == "Point"
    assert res["layer"]["rows"] == 1


def test_run_algorithm_unknown(tmp_path):
    """未知算法报错（白名单边界）"""
    pts = tmp_path / "pts.csv"
    pts.write_text("id,lon,lat\n1,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    with pytest.raises(GisEngineError, match="未知算法"):
        eng.run_algorithm("evil_script")


def test_load_raster_metadata(tmp_path):
    """load_raster：返回栅格元数据（宽高/波段/CRS/范围）"""
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

    eng = _engine(tmp_path)
    res = eng.load_raster(str(tif))
    assert res["status"] == "ok"
    assert res["raster"]["width"] == 4
    assert res["raster"]["height"] == 3
    assert res["raster"]["bands"] == 1
    assert res["raster"]["crs"] == "EPSG:4326"
    assert len(res["raster"]["bounds"]) == 4


def test_load_raster_rejects_non_raster(tmp_path):
    """非栅格文件报错"""
    bad = tmp_path / "not_raster.tif"
    bad.write_text("not a tiff", encoding="utf-8")
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError, match="加载栅格失败"):
        eng.load_raster(str(bad))


# ── Gate 6 编辑会话（HITL 审批联动）─────────────────


def test_edit_session_add_commit(tmp_path):
    """编辑会话：start → add → commit 生效"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\nB,117,40\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    assert eng.start_editing()["status"] == "ok"
    res = eng.add_features("POINT(118 41)", {"name": "C"})
    assert res["status"] == "ok"
    # commit 前当前图层仍是 2 行（未生效）
    assert eng.list_layers()["layer"]["rows"] == 2
    eng.commit_edits()
    assert eng.list_layers()["layer"]["rows"] == 3


def test_edit_session_rollback(tmp_path):
    """编辑会话：rollback 丢弃修改"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\nB,117,40\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    eng.start_editing()
    eng.delete_features([0])
    eng.rollback_edits()
    assert eng.list_layers()["layer"]["rows"] == 2  # 回滚恢复


def test_edit_requires_start(tmp_path):
    """未 start_editing 时编辑报错"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    with pytest.raises(GisEngineError, match="未开始编辑"):
        eng.add_features("POINT(118 41)")


def test_edit_update_and_delete(tmp_path):
    """编辑会话：update 属性 + delete 要素"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,val,lon,lat\nA,1,116,39\nB,2,117,40\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    eng.start_editing()
    res = eng.update_features("name == 'A'", {"val": 99})
    assert res["status"] == "ok" and "1 个" in res["message"]
    eng.delete_features([1])
    eng.commit_edits()
    layer = eng.list_layers()["layer"]
    assert layer["rows"] == 1
    sample = eng.inspect_data()["sample_rows"]
    assert sample[0]["val"] == 99


def test_duplicate_layer(tmp_path):
    """复制图层为新的当前图层（编辑前备份）"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    assert eng.duplicate_layer()["status"] == "ok"
    assert eng.list_layers()["layer"]["rows"] == 1


def test_calculate_field(tmp_path):
    """编辑会话：按表达式生成新列，commit 前不生效"""
    pts = tmp_path / "pts.csv"
    pts.write_text(
        "name,gdp,pop,lon,lat\nA,100,10,116,39\nB,200,20,117,40\n",
        encoding="utf-8",
    )
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    eng.start_editing()
    res = eng.calculate_field("gdp / pop", "per_capita")
    assert res["status"] == "ok" and "per_capita" in res["message"]
    assert "per_capita" not in eng.list_layers()["layer"]["columns"]  # 未 commit 不生效
    eng.commit_edits()
    sample = eng.inspect_data()["sample_rows"]
    assert sample[0]["per_capita"] == 10.0
    assert sample[1]["per_capita"] == 10.0


def test_calculate_field_where(tmp_path):
    """编辑会话：where 限定计算范围，不满足的要素置空"""
    pts = tmp_path / "pts.csv"
    pts.write_text(
        "name,gdp,pop,lon,lat\nA,100,10,116,39\nB,200,20,117,40\n",
        encoding="utf-8",
    )
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    eng.start_editing()
    res = eng.calculate_field("gdp / pop", "per_capita", where="name == 'A'")
    assert res["status"] == "ok"
    eng.commit_edits()
    sample = eng.inspect_data()["sample_rows"]
    assert sample[0]["per_capita"] == 10.0
    assert pd.isna(sample[1]["per_capita"])


def test_calculate_field_errors(tmp_path):
    """字段重名 / 非法表达式 / 未开始编辑均报错"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,gdp,lon,lat\nA,100,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    with pytest.raises(GisEngineError, match="未开始编辑"):
        eng.calculate_field("gdp * 2", "new_col")
    eng.start_editing()
    with pytest.raises(GisEngineError, match="字段已存在"):
        eng.calculate_field("gdp * 2", "gdp")
    with pytest.raises(GisEngineError, match="计算表达式无效"):
        eng.calculate_field("gdp / 0 +", "new_col")


def test_calculate_field_dangerous():
    """calculate_field 属于危险写操作，需走人工审批"""
    from src.gis_toolkit.approval import DANGEROUS_TOOLS

    assert "calculate_field" in DANGEROUS_TOOLS


def test_categorized(tmp_path):
    """分类设色：按类别出图"""
    pts = tmp_path / "pts.csv"
    pts.write_text("cat,lon,lat\nA,116,39\nB,117,40\nA,118,41\nC,119,42\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.categorized("cat", output="cat.png")
    assert res["status"] == "ok"
    assert res["classes"] == 3
    assert (tmp_path / "out" / "cat.png").is_file()


def test_categorized_missing_column(tmp_path):
    pts = tmp_path / "pts.csv"
    pts.write_text("cat,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    with pytest.raises(GisEngineError, match="列不存在"):
        eng.categorized("nope")


def test_set_labeling_and_render(tmp_path):
    """设置标注后出图带标注"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\nB,117,40\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    assert eng.set_labeling("name")["status"] == "ok"
    res = eng.render_map(output="labeled.png")
    assert res["status"] == "ok"
    assert (tmp_path / "out" / "labeled.png").is_file()
    # 关闭标注
    assert eng.set_labeling("name", enabled=False)["status"] == "ok"


def test_set_labeling_missing_column(tmp_path):
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    with pytest.raises(GisEngineError, match="列不存在"):
        eng.set_labeling("nope")


def test_get_project_info(tmp_path):
    """get_project_info：返回引擎状态摘要"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    info = eng.get_project_info()
    assert info["status"] == "ok"
    assert info["engine"] == "geopandas"
    assert info["layer"] is None

    eng.load_data(str(pts))
    info = eng.get_project_info()
    assert info["layer"]["rows"] == 1
    assert info["out_dir"]


def test_save_project_geopandas_unsupported(tmp_path):
    """geopandas 引擎 save_project 报错提示用 QGIS 引擎"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    with pytest.raises(GisEngineError, match="QGIS 工程"):
        eng.save_project()


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


# ── 省界底图 choropleth ─────────────────────────────


def _fake_base_map():
    """假省界：北京 / 上海 两个矩形（EPSG:4326），name 带行政后缀"""
    return gpd.GeoDataFrame(
        {"name": ["北京市", "上海市"], "adcode": [110000, 310000]},
        geometry=[box(116.0, 39.5, 117.0, 40.5), box(121.0, 31.0, 122.0, 32.0)],
        crs="EPSG:4326",
    )


def test_province_norm():
    assert GisEngine._province_norm("北京市") == "北京"
    assert GisEngine._province_norm("河北省") == "河北"
    assert GisEngine._province_norm("内蒙古自治区") == "内蒙古"
    assert GisEngine._province_norm("广西壮族自治区") == "广西"
    assert GisEngine._province_norm("新疆维吾尔自治区") == "新疆"
    assert GisEngine._province_norm("香港特别行政区") == "香港"


def test_choropleth_aggregates_province_onto_base_map(point_csv, tmp_path):
    """点数据 + province 列 + 省界底图 → 按省份聚合输出省面图"""
    eng = GisEngine(
        data_file=point_csv, out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)]
    )
    eng._base_map = _fake_base_map()
    res = eng.choropleth(column="gdp", scheme="Quantiles", k=3, output="province_map.png")
    assert res["status"] == "ok"
    assert (tmp_path / "out" / "province_map.png").is_file()
    assert "按省份聚合" in res["message"]


def test_choropleth_points_overlay_base_map(tmp_path):
    """点数据无 province 列 + 省界底图 → 底图叠加点着色"""
    p = tmp_path / "cities.csv"
    p.write_text(
        "city,gdp,lon,lat\nA,100,116.5,39.9\nB,200,121.5,31.2\n",
        encoding="utf-8",
    )
    eng = GisEngine(data_file=str(p), out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)])
    eng._base_map = _fake_base_map()
    res = eng.choropleth(column="gdp", output="overlay.png")
    assert res["status"] == "ok"
    assert (tmp_path / "out" / "overlay.png").is_file()
    assert "底图" in res["message"]


# ── join_by_attribute（属性连接）──────────────────────


def test_join_by_attribute_basic(tmp_path):
    """属性连接：按关键字段把关联表并入当前图层（inner 默认）"""
    layer = tmp_path / "regions.csv"
    layer.write_text("code,name,lon,lat\nA,东区,1,1\nB,西区,2,2\n", encoding="utf-8")
    stats = tmp_path / "stats.csv"
    stats.write_text("code,gdp\nA,100\nB,200\n", encoding="utf-8")

    eng = _engine(tmp_path)
    eng.load_data(str(layer))
    res = eng.join_by_attribute(str(stats), left_key="code", right_key="code")
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 2
    assert "gdp" in res["layer"]["columns"]
    assert res["layer"]["columns"][-1] == "gdp"


def test_join_by_attribute_left_keeps_all(tmp_path):
    """how=left：保留当前图层全部行，未匹配行属性为空"""
    layer = tmp_path / "regions.csv"
    layer.write_text("code,name,lon,lat\nA,东区,1,1\nB,西区,2,2\n", encoding="utf-8")
    stats = tmp_path / "stats.csv"
    stats.write_text("code,gdp\nA,100\n", encoding="utf-8")

    eng = _engine(tmp_path)
    eng.load_data(str(layer))
    res = eng.join_by_attribute(str(stats), left_key="code", right_key="code", how="left")
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 2


def test_join_by_attribute_inner_drops_unmatched(tmp_path):
    """how=inner：只保留匹配行"""
    layer = tmp_path / "regions.csv"
    layer.write_text("code,name,lon,lat\nA,东区,1,1\nB,西区,2,2\n", encoding="utf-8")
    stats = tmp_path / "stats.csv"
    stats.write_text("code,gdp\nA,100\n", encoding="utf-8")

    eng = _engine(tmp_path)
    eng.load_data(str(layer))
    res = eng.join_by_attribute(str(stats), left_key="code", right_key="code")
    assert res["status"] == "ok"
    assert res["layer"]["rows"] == 1


def test_join_by_attribute_errors(tmp_path):
    """错误分支：未加载图层 / 左表缺字段 / 关联表缺字段 / how 非法"""
    layer = tmp_path / "regions.csv"
    layer.write_text("code,name,lon,lat\nA,东区,1,1\n", encoding="utf-8")
    stats = tmp_path / "stats.csv"
    stats.write_text("code,gdp\nA,100\n", encoding="utf-8")

    # 未加载图层
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError, match="先 load_data"):
        eng.join_by_attribute(str(stats), left_key="code", right_key="code")

    # 当前图层缺少连接字段
    eng.load_data(str(layer))
    with pytest.raises(GisEngineError, match="当前图层缺少连接字段"):
        eng.join_by_attribute(str(stats), left_key="nope", right_key="code")

    # 关联表缺少连接字段
    with pytest.raises(GisEngineError, match="关联表缺少连接字段"):
        eng.join_by_attribute(str(stats), left_key="code", right_key="nope")

    # how 非法
    with pytest.raises(GisEngineError, match="how 必须是 inner/left"):
        eng.join_by_attribute(str(stats), left_key="code", right_key="code", how="outer")


# ── 图层管理增强：rename / remove / inventory ──────────


def test_rename_layer(tmp_path):
    """重命名当前图层（仅元数据，不改数据文件）"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    assert eng.list_layers()["layer"]["name"] == "pts"  # load 时取文件名
    res = eng.rename_layer("行政点")
    assert res["status"] == "ok"
    assert "行政点" in res["message"]
    assert eng.list_layers()["layer"]["name"] == "行政点"
    with pytest.raises(GisEngineError, match="不能为空"):
        eng.rename_layer("   ")


def test_remove_layer(tmp_path):
    """移除当前图层，图层与编辑会话状态清空"""
    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    eng.start_editing()
    assert eng.list_layers()["has_layer"] is True
    res = eng.remove_layer()
    assert res["status"] == "ok"
    assert eng.list_layers()["has_layer"] is False
    with pytest.raises(GisEngineError, match="无需移除"):
        eng.remove_layer()


def test_export_layer_inventory(tmp_path):
    """导出图层清单 JSON（名称/行数/字段/CRS/几何类型/范围/产物）"""
    import json

    pts = tmp_path / "pts.csv"
    pts.write_text("name,lon,lat\nA,116,39\n", encoding="utf-8")
    eng = _engine(tmp_path)
    eng.load_data(str(pts))
    res = eng.export_layer_inventory("inv.json")
    assert res["status"] == "ok"
    assert res["inventory_file"] == "inv.json"
    inv_path = tmp_path / "out" / "inv.json"
    assert inv_path.exists()
    data = json.loads(inv_path.read_text(encoding="utf-8"))
    assert data["name"] == "pts"
    assert data["rows"] == 1
    assert "name" in data["columns"] and "lon" in data["columns"]
    assert data["crs"] is not None
    assert data["geometry_type"] is not None
    assert data["bounds"] is not None
    assert "outputs" in data
    assert "exported_at" in data


def test_remove_layer_approval_required():
    """remove_layer 必须列入危险工具审批清单"""
    from src.gis_toolkit.approval import DANGEROUS_TOOLS

    assert "remove_layer" in DANGEROUS_TOOLS


# ── layout_map / load_basemap（Gate 8）──────────────


def test_layout_map_basic(poly_a, tmp_path):
    """layout_map 默认排版出图：产物落盘 + 尺寸正常"""
    eng = _engine(tmp_path, data_file=poly_a, allowed=[str(tmp_path)])
    eng.load_data(poly_a)
    res = eng.layout_map()
    assert res["status"] == "ok"
    out = tmp_path / "out" / "layout_map.png"
    assert out.exists()
    assert res.get("size_bytes", 0) > 0
    assert out.stat().st_size > 1000


def test_layout_map_with_legend_and_elements(point_csv, tmp_path):
    """layout_map 按字段生成图例 + 比例尺 + 指北针"""
    eng = _engine(tmp_path, data_file=point_csv, allowed=[str(tmp_path)])
    eng.load_data(point_csv)
    res = eng.layout_map(
        title="测试排版",
        legend_column="province",
        show_legend=True,
        show_scalebar=True,
        show_north_arrow=True,
        output="layout_legend.png",
    )
    assert res["status"] == "ok"
    assert (tmp_path / "out" / "layout_legend.png").exists()


def test_layout_map_requires_layer(tmp_path):
    """未加载图层时 layout_map 必须报错"""
    eng = _engine(tmp_path)
    with pytest.raises(GisEngineError):
        eng.layout_map()


def test_layout_map_bad_legend_column(poly_a, tmp_path):
    """不存在的图例字段必须报错"""
    eng = _engine(tmp_path, data_file=poly_a, allowed=[str(tmp_path)])
    eng.load_data(poly_a)
    with pytest.raises(GisEngineError):
        eng.layout_map(legend_column="no_such_field")


def _write_test_tif(path, width=8, height=8):
    """写入 3 波段小 GeoTIFF 用作本地底图"""
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds

    profile = {
        "driver": "GTiff",
        "width": width,
        "height": height,
        "count": 3,
        "dtype": "uint8",
        "crs": "EPSG:4326",
        "transform": from_bounds(0, 0, 10, 10, width, height),
    }
    data = np.zeros((3, height, width), dtype="uint8")
    data[0, :, :] = 200
    data[1, :, :] = 200
    data[2, :, :] = 200
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data)


def test_load_basemap_local(poly_a, tmp_path):
    """load_basemap(local) 加载本地 GeoTIFF，并在 render_map/layout_map 叠加不报错"""
    tif = tmp_path / "base.tif"
    _write_test_tif(tif)
    eng = _engine(tmp_path, data_file=poly_a, allowed=[str(tmp_path)])
    eng.load_data(poly_a)
    res = eng.load_basemap(source="local", url=str(tif), name="底图")
    assert res["status"] == "ok"
    assert res["basemap"]["kind"] == "local"
    # 叠加底图渲染不报错
    eng.render_map(output="map_with_base.png")
    eng.layout_map(output="layout_with_base.png")
    assert (tmp_path / "out" / "map_with_base.png").exists()


def test_load_basemap_xyz(poly_a, tmp_path):
    """load_basemap(xyz) 记录在线瓦片配置（引擎不实际拉取）"""
    eng = _engine(tmp_path, data_file=poly_a, allowed=[str(tmp_path)])
    eng.load_data(poly_a)
    res = eng.load_basemap(
        source="xyz",
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="OSM",
    )
    assert res["status"] == "ok"
    assert res["basemap"]["kind"] == "xyz"
    assert res["basemap"]["url"]


def test_load_basemap_bad_source(poly_a, tmp_path):
    """未知底图来源必须报错"""
    eng = _engine(tmp_path, data_file=poly_a, allowed=[str(tmp_path)])
    eng.load_data(poly_a)
    with pytest.raises(GisEngineError):
        eng.load_basemap(source="foo", url="x")


def test_load_basemap_local_missing_file(poly_a, tmp_path):
    """本地底图文件不存在必须报错"""
    eng = _engine(tmp_path, data_file=poly_a, allowed=[str(tmp_path)])
    eng.load_data(poly_a)
    with pytest.raises(GisEngineError):
        eng.load_basemap(source="local", url=str(tmp_path / "no_such.tif"))
