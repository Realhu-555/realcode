"""GIS data_inspect 工具测试 — 读取 + 路径白名单 + 大小限制"""

import json

import pytest
from src.tools.implementations import data_inspect
from src.tools.implementations.data_inspect import DataInspectTool
from src.tools.protocol import ToolContext


def _ctx(data_root, **extra):
    return ToolContext(
        session_id="t",
        working_dir=str(data_root),
        project_state={"data_root": str(data_root), **extra},
    )


@pytest.mark.asyncio
async def test_inspect_csv(tmp_path):
    csv_path = tmp_path / "gdp.csv"
    csv_path.write_text(
        "province,gdp,lon,lat\n北京,41610,116.4,39.9\n上海,47219,121.5,31.2\n",
        encoding="utf-8",
    )
    result = await DataInspectTool().execute(_ctx(tmp_path), str(csv_path))
    assert result.success
    assert result.data["format"] == "csv"
    assert result.data["fields"] == ["province", "gdp", "lon", "lat"]
    assert result.data["row_count"] == 2
    assert len(result.data["sample_rows"]) == 2


@pytest.mark.asyncio
async def test_inspect_geojson(tmp_path):
    gj_path = tmp_path / "poi.geojson"
    gj_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": "a", "count": 3},
                        "geometry": {"type": "Point", "coordinates": [1, 2]},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    result = await DataInspectTool().execute(_ctx(tmp_path), str(gj_path))
    assert result.success
    assert result.data["format"] == "geojson"
    assert result.data["feature_count"] == 1
    assert result.data["fields"] == ["name", "count"]


@pytest.mark.asyncio
async def test_inspect_rejects_outside_data_root(tmp_path):
    outside = tmp_path.parent / "secret.env"
    outside.write_text("API_KEY=xxx", encoding="utf-8")
    result = await DataInspectTool().execute(_ctx(tmp_path), str(outside))
    assert not result.success
    assert "数据目录内" in result.error


@pytest.mark.asyncio
async def test_inspect_rejects_missing_file(tmp_path):
    result = await DataInspectTool().execute(_ctx(tmp_path), str(tmp_path / "nope.csv"))
    assert not result.success
    assert "不存在" in result.error


@pytest.mark.asyncio
async def test_inspect_rejects_too_large(tmp_path, monkeypatch):
    big = tmp_path / "big.csv"
    big.write_text("a\n" * 100, encoding="utf-8")
    monkeypatch.setattr(data_inspect, "MAX_SIZE_BYTES", 10)
    result = await DataInspectTool().execute(_ctx(tmp_path), str(big))
    assert not result.success
    assert "10MB" in result.error


@pytest.mark.asyncio
async def test_inspect_requires_data_root(tmp_path):
    result = await DataInspectTool().execute(
        ToolContext(session_id="t", working_dir=str(tmp_path), project_state={}),
        str(tmp_path / "x.csv"),
    )
    assert not result.success
    assert "data_root" in result.error
