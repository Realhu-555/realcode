"""GIS Web API 测试 — 文件上传 + 构建流水线"""

from fastapi.testclient import TestClient
from src.web import server

client = TestClient(server.app)
HEADERS = {"X-API-Key": "test-key"}

_GOOD_SCRIPT = (
    "import pandas as pd\n"
    "import geopandas as gpd\n"
    "import matplotlib.pyplot as plt\n"
    "df = pd.DataFrame({\"province\": [\"A\", \"B\"], \"gdp\": [1, 2],"
    " \"lon\": [116.4, 121.5], \"lat\": [39.9, 31.2]})\n"
    "gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[\"lon\"], df[\"lat\"]), crs=\"EPSG:4326\")\n"
    "print(\"CRS:\", gdf.crs.to_string())\n"
    "fig, ax = plt.subplots()\n"
    "gdf.plot(ax=ax, column=\"gdp\")\n"
    "fig.savefig(\"choropleth.png\")\n"
)


def _fake_agents():
    """不调用 LLM 的假 Agent 对象（exec/export 用真实节点）"""

    class _Plan:
        def run(self, s):
            return {**s, "task_plan": "1. 读取\n2. 分级\n3. 出图", "current_stage": "design"}

    class _Design:
        def run(self, s):
            return {**s, "tech_plan": "坐标系 EPSG:4326", "current_stage": "codegen"}

    class _Codegen:
        def run(self, s):
            return {**s, "script": _GOOD_SCRIPT, "current_stage": "exec"}

    class _Checker:
        def run(self, s):
            return {**s, "check_report": "整体结论: PASS", "current_stage": "check"}

    return {"plan": _Plan(), "design": _Design(), "codegen": _Codegen(), "checker": _Checker()}


# ── 上传端点 ──────────────────────────────────────────

def test_upload_csv_ok(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "GIS_UPLOAD_DIR", tmp_path)
    resp = client.post(
        "/api/v1/gis/upload",
        files={"file": ("gdp.csv", "province,gdp\n北京,1\n", "text/csv")},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["path"].endswith("gdp.csv")


def test_upload_rejects_unsupported_type(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "GIS_UPLOAD_DIR", tmp_path)
    resp = client.post(
        "/api/v1/gis/upload",
        files={"file": ("evil.exe", b"\x00\x01", "application/octet-stream")},
        headers=HEADERS,
    )
    assert resp.json()["success"] is False
    assert "不支持" in resp.json()["error"]


def test_upload_rejects_too_large(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "GIS_UPLOAD_DIR", tmp_path)
    big = b"0" * (10 * 1024 * 1024 + 1)
    resp = client.post(
        "/api/v1/gis/upload",
        files={"file": ("big.csv", big, "text/csv")},
        headers=HEADERS,
    )
    assert resp.json()["success"] is False
    assert "10MB" in resp.json()["error"]


def test_upload_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "GIS_UPLOAD_DIR", tmp_path)
    resp = client.post(
        "/api/v1/gis/upload",
        files={"file": ("gdp.csv", "a,b\n1,2\n", "text/csv")},
    )
    assert resp.status_code == 401


# ── 构建端点 ──────────────────────────────────────────

def test_build_gis_pipeline(monkeypatch):
    monkeypatch.setattr(server, "_build_gis_agents", _fake_agents)
    resp = client.post(
        "/api/v1/gis/build",
        json={"user_request": "把 GDP 数据做分级设色图", "data_file": None},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["stage"] == "done"
    assert "choropleth.png" in data["artifacts"]
    assert data["artifact_path"]
    assert data["check_report"] == "整体结论: PASS"


def test_build_gis_with_data_schema(monkeypatch, tmp_path):
    """上传数据文件后构建，data_schema 预注入成功"""
    monkeypatch.setattr(server, "_build_gis_agents", _fake_agents)
    monkeypatch.setattr(server, "GIS_UPLOAD_DIR", tmp_path)
    up = client.post(
        "/api/v1/gis/upload",
        files={"file": ("gdp.csv", "province,gdp,lon,lat\n北京,41610,116.4,39.9\n", "text/csv")},
        headers=HEADERS,
    )
    data_file = up.json()["path"]

    resp = client.post(
        "/api/v1/gis/build",
        json={"user_request": "按省份做分级设色图", "data_file": data_file},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["stage"] == "done"
    # exec 会把源数据复制进沙箱
    assert "gdp.csv" in str(data["artifacts"])
