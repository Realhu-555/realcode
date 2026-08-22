"""T6: 产物校验器单测 — 文件存在/非空/可读性"""

from pathlib import Path

from src.gis_toolkit.checker import check_outputs


def _mk_png(path: Path, size: int = 1024) -> Path:
    path.write_bytes(b"\x89PNG" + b"\x00" * (size - 4))
    return path


def test_check_png_ok(tmp_path):
    p = _mk_png(tmp_path / "a.png")
    assert check_outputs({"output_paths": [str(p)]}) == []


def test_check_empty_png_fails(tmp_path):
    p = tmp_path / "empty.png"
    p.write_bytes(b"")
    errors = check_outputs({"output_paths": [str(p)]})
    assert any("空" in e for e in errors)


def test_check_csv_ok(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    assert check_outputs({"output_paths": [str(p)]}) == []


def test_check_csv_empty_fails(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("a,b\n", encoding="utf-8")
    errors = check_outputs({"output_paths": [str(p)]})
    assert any("无数据行" in e for e in errors)


def test_check_geojson_ok(tmp_path):
    import geopandas as gpd
    from shapely.geometry import Point

    p = tmp_path / "pt.geojson"
    gpd.GeoDataFrame(
        {"id": [1]}, geometry=[Point(116, 39)], crs="EPSG:4326"
    ).to_file(p, driver="GeoJSON")
    assert check_outputs({"output_paths": [str(p)]}) == []


def test_check_invalid_geojson_fails(tmp_path):
    p = tmp_path / "bad.geojson"
    p.write_text("{not valid", encoding="utf-8")
    errors = check_outputs({"output_paths": [str(p)]})
    assert any("无法读取" in e for e in errors)


def test_check_missing_file_fails(tmp_path):
    errors = check_outputs({"output_paths": [str(tmp_path / "nope.png")]})
    assert any("不存在" in e for e in errors)


def test_check_no_outputs_passes():
    assert check_outputs({"status": "ok"}) == []


def test_check_outputs_without_paths_skips():
    """兼容只有文件名（无 output_paths）的返回：跳过校验"""
    assert check_outputs({"status": "ok", "outputs": ["x.png"]}) == []


def test_check_mixed_ok_and_bad(tmp_path):
    good = _mk_png(tmp_path / "good.png")
    bad = tmp_path / "bad.csv"
    bad.write_text("", encoding="utf-8")
    errors = check_outputs({"output_paths": [str(good), str(bad)]})
    assert len(errors) >= 1
    assert all("good.png" not in e for e in errors)
