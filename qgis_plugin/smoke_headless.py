"""M1+M2b 冒烟（headless，无 GUI）：

M1：快照 → 本地服务 → HTTP 鉴权整条链路；
M2b：live_tools 首批工具链（加载→检查→增改→提交→缓冲→导出）在真实 QGIS 进程执行。

运行（用 QGIS 自带 Python，cwd = 项目根）：
    & 'D:\\QGIS\\bin\\python-qgis-ltr.bat' qgis_plugin/smoke_headless.py
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from gis_assistant import live_tools  # noqa: E402
from gis_assistant.config import get_token  # noqa: E402
from gis_assistant.control_server import ControlServer  # noqa: E402
from gis_assistant.state import ProjectSnapshot  # noqa: E402
from qgis.core import (  # noqa: E402
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)


def _build_project() -> None:
    layer = QgsVectorLayer(
        "Point?crs=EPSG:4326&field=name:string(50)",
        "smoke_pts",
        "memory",
    )
    assert layer.isValid(), "内存图层创建失败"
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(116.4, 39.9)))
    feature.setAttributes(["测试点"])
    layer.dataProvider().addFeatures([feature])
    QgsProject.instance().addMapLayer(layer)
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))


def _get(path: str, token: str, port: int, with_token: bool = True):
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}")
    if with_token:
        request.add_header("X-GIS-Token", token)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _invoke(tool: str, args: dict, out_dir: str) -> dict:
    return live_tools.invoke({"tool": tool, "args": args, "out_dir": out_dir})


def _tool_smoke(work_dir: Path) -> None:
    """M2b：编辑闭环 T1（加载→增改→提交）+ 缓冲 + 导出。"""
    in_path = work_dir / "smoke_points.geojson"
    out_dir = work_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    in_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": "A"},
                        "geometry": {"type": "Point", "coordinates": [116.4, 39.9]},
                    },
                    {
                        "type": "Feature",
                        "properties": {"name": "B"},
                        "geometry": {"type": "Point", "coordinates": [116.5, 39.95]},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    loaded = _invoke("load_data", {"path": str(in_path)}, str(out_dir))
    assert loaded["layer"]["rows"] == 2, "加载后应有 2 行"
    assert loaded["layer"]["geometry_type"] == "Point"
    name = loaded["layer"]["name"]
    project_names = {layer.name() for layer in QgsProject.instance().mapLayers().values()}
    assert name in project_names, "加载后的图层应加入当前工程"

    inspected = _invoke("inspect_data", {}, str(out_dir))
    assert len(inspected["sample_rows"]) == 2

    _invoke("start_editing", {}, str(out_dir))
    _invoke(
        "add_features", {"geometry": "POINT(116.6 39.9)", "attributes": {"name": "C"}}, str(out_dir)
    )
    _invoke("update_features", {"where": "name = 'A'", "attributes": {"name": "AA"}}, str(out_dir))
    _invoke("commit_edits", {}, str(out_dir))
    reloaded = json.loads(in_path.read_text(encoding="utf-8"))
    names = {f["properties"]["name"] for f in reloaded["features"]}
    assert names == {"AA", "B", "C"}, f"提交后要素不正确: {names}"

    duplicated = _invoke("duplicate_layer", {}, str(out_dir))
    duplicate_name = duplicated["layer"]["name"]
    assert duplicated["layer"]["rows"] == 3, "复制图层应有 3 行"
    project_names = {layer.name() for layer in QgsProject.instance().mapLayers().values()}
    assert duplicate_name in project_names, "复制图层应加入工程"

    _invoke("start_editing", {}, str(out_dir))
    try:
        _invoke("add_features", {"geometry": "POLYGON((0 0,1 0,1 1,0 1,0 0))"}, str(out_dir))
        raise AssertionError("面几何加到点图层应被拒绝")
    except RuntimeError as exc:
        assert "几何类型不匹配" in str(exc), exc
    _invoke("rollback_edits", {}, str(out_dir))

    _invoke("buffer", {"distance": 0.01}, str(out_dir))
    exported = _invoke("export_geojson", {"output": "buffer.geojson"}, str(out_dir))
    assert exported.get("output") == "buffer.geojson"
    assert (out_dir / "buffer.geojson").is_file(), "导出文件应存在"
    print("M2B TOOL SMOKE PASSED")


def main() -> int:
    app = QgsApplication([], False)
    app.initQgis()
    work_dir = Path(tempfile.mkdtemp(prefix="gis_assistant_smoke_"))
    try:
        _build_project()
        token = get_token()
        snapshot = ProjectSnapshot()
        snapshot.refresh()
        server = ControlServer(snapshot.get, token, 0)
        server.start()
        try:
            status, body = _get("/v1/health", token, server.port)
            print("health:", status, body["ok"], body.get("version"))
            status, body = _get("/v1/state", token, server.port)
            print("state:", status, "project crs =", body["state"]["crs"])
            found = [item for item in body["state"]["layers"] if item["name"] == "smoke_pts"]
            assert found, "快照中没有 smoke_pts"
            assert found[0]["features"] == 1, "要素数不符"
            assert found[0]["geometry"] == "Point", "几何类型不符"
            print("layer:", found[0])
            status, body = _get("/v1/state", token, server.port, with_token=False)
            assert status == 401, "无 Token 应返回 401"
            print("unauthorized status:", status)
            _tool_smoke(work_dir)
            print("SMOKE PASSED")
        finally:
            server.stop()
        return 0
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        app.exitQgis()


if __name__ == "__main__":
    raise SystemExit(main())
