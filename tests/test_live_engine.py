"""LiveEngine（M2a 只读阶段）单元测试 — 不依赖 QGIS 插件，mock 网络。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest
from src.gis_toolkit.engine import GisEngineError
from src.gis_toolkit.live_engine import LiveEngine
from src.utils.config import settings


class _FakeResponse:
    """urllib.urlopen 的替身：返回固定 JSON。"""

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None


def _patch_urlopen(payload: dict):
    return mock.patch(
        "urllib.request.urlopen",
        return_value=_FakeResponse(payload),
    )


def test_missing_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "live_qgis_token", "")
    with pytest.raises(GisEngineError, match="LIVE_QGIS_TOKEN"):
        LiveEngine(url="http://127.0.0.1:9999")


def test_get_project_info_parses_live_state(monkeypatch):
    monkeypatch.setattr(settings, "live_qgis_token", "test-token")
    state = {
        "project": r"D:\work\demo.qgz",
        "crs": "EPSG:4326",
        "layers": [
            {
                "id": "layer_1",
                "name": "村界",
                "type": "Vector",
                "geometry": "Polygon",
                "features": 12,
                "selected": 2,
                "editing": True,
            }
        ],
    }
    with _patch_urlopen({"ok": True, "state": state}):
        engine = LiveEngine(url="http://127.0.0.1:8756")
        info = engine.get_project_info()
    assert info["engine"] == "qgis-live"
    assert info["project"].endswith("demo.qgz")
    assert info["crs"] == "EPSG:4326"
    assert info["layer_count"] == 1
    assert info["layers"][0]["name"] == "村界"


def test_list_layers_returns_all(monkeypatch):
    monkeypatch.setattr(settings, "live_qgis_token", "test-token")
    state = {
        "project": "",
        "crs": "",
        "layers": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
    }
    with _patch_urlopen({"ok": True, "state": state}):
        engine = LiveEngine(url="http://127.0.0.1:8756")
        result = engine.list_layers()
    assert result["count"] == 2
    assert [layer["name"] for layer in result["layers"]] == ["A", "B"]


def test_unsupported_tool_raises(monkeypatch):
    monkeypatch.setattr(settings, "live_qgis_token", "test-token")
    with _patch_urlopen({"ok": True, "state": {"project": "", "crs": "", "layers": []}}):
        engine = LiveEngine(url="http://127.0.0.1:8756")
    with pytest.raises(GisEngineError, match="尚未支持"):
        engine.render_map(output="x.png")


def test_export_geojson_posts_invoke(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "live_qgis_token", "test-token")
    calls = []

    def fake_urlopen(request, timeout=None):
        calls.append(request)
        if getattr(request, "data", None) is not None:  # POST /v1/tools/invoke
            return _FakeResponse(
                {"ok": True, "result": {"output": "layer.geojson", "size_bytes": 4}}
            )
        return _FakeResponse({"ok": True, "state": {"project": "", "crs": "", "layers": []}})

    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        engine = LiveEngine(url="http://127.0.0.1:8756", out_dir=str(tmp_path / "out"))
        result = engine.export_geojson("layer.geojson")

    headers = {key.lower(): value for key, value in calls[-1].header_items()}
    assert headers["x-gis-token"] == "test-token"
    payload = json.loads(calls[-1].data)
    assert payload["tool"] == "export_geojson"
    assert payload["out_dir"].endswith("out")
    assert result["outputs"] == ["layer.geojson"]
    output_path = Path(result["output_paths"][0])
    assert output_path.parent.name == "out"
    assert output_path.name == "layer.geojson"


def test_session_snapshot_interface_noop(monkeypatch):
    """会话层会访问 engine._layer 与 save_layer_snapshot——live 应安全跳过。"""
    monkeypatch.setattr(settings, "live_qgis_token", "test-token")
    with _patch_urlopen({"ok": True, "state": {"project": "", "crs": "", "layers": []}}):
        engine = LiveEngine(url="http://127.0.0.1:8756")
    assert engine._layer is None
    assert engine.save_layer_snapshot("anything.geojson") is None


def test_connection_refused_raises(monkeypatch):
    monkeypatch.setattr(settings, "live_qgis_token", "test-token")
    with (
        mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")),
        pytest.raises(GisEngineError, match="无法连接 QGIS 插件"),
    ):
        LiveEngine(url="http://127.0.0.1:1")
