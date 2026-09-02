"""模型 API Key 配置（前端设置页写 .env / user_models）单测。"""

import os

from fastapi.testclient import TestClient

from src.gis_toolkit.user_settings import UserSettings, set_env_api_key
from src.llm.models import ModelConfig
from src.web import server

client = TestClient(server.app)
HEADERS = {"X-API-Key": "model-key-test"}


# ── set_env_api_key：写入 / 替换 / 保留注释 ─────────────


def test_set_env_api_key_append_new(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# 注释行\nTAVILY_API_KEY=old\n", encoding="utf-8")
    set_env_api_key("NEW_KEY", "secret-1", env_path=env_file)
    text = env_file.read_text(encoding="utf-8")
    assert "# 注释行" in text
    assert "TAVILY_API_KEY=old" in text
    assert "NEW_KEY=secret-1" in text
    assert os.environ.get("NEW_KEY") == "secret-1"


def test_set_env_api_key_replace_existing(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=old-value\n", encoding="utf-8")
    set_env_api_key("DEEPSEEK_API_KEY", "new-value", env_path=env_file)
    text = env_file.read_text(encoding="utf-8")
    assert "DEEPSEEK_API_KEY=new-value" in text
    assert "old-value" not in text
    assert os.environ["DEEPSEEK_API_KEY"] == "new-value"


def test_set_env_api_key_reject_invalid(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    try:
        set_env_api_key("K", "  \n", env_path=env_file)
        assert False, "应拒绝空/含换行的 key"
    except ValueError:
        pass


# ── ModelConfig.has_key 修正：env 真有值才算有 key ─────


def test_has_key_env_real_value(monkeypatch):
    cfg = ModelConfig(id="x", label="X", provider="p", model="m", api_key_env="ENV_A")
    monkeypatch.setenv("ENV_A", "secret")
    assert cfg.has_key is True


def test_has_key_env_missing(monkeypatch):
    cfg = ModelConfig(id="x", label="X", provider="p", model="m", api_key_env="ENV_EMPTY")
    monkeypatch.delenv("ENV_EMPTY", raising=False)
    assert cfg.has_key is False


def test_has_key_custom_plain():
    cfg = ModelConfig(id="x", label="X", provider="p", model="m", api_key_plain="k")
    assert cfg.has_key is True


# ── UserSettings.update_model_key ─────────────────────


def test_update_model_key_ok(tmp_path):
    us = UserSettings(db_path=str(tmp_path / "ltm.db"))
    us.add_model("user-a", label="my gateway", model="m", base_url="http://localhost:11434/v1")
    mid = us.list_models("user-a")[0]["id"]
    assert us.update_model_key("user-a", mid, "new-secret") is True
    assert us.get_model("user-a", mid)["api_key"] == "new-secret"
    assert us.update_model_key("user-a", mid, "") is True  # 清空
    assert us.get_model("user-a", mid)["api_key"] is None


def test_update_model_key_not_mine(tmp_path):
    us = UserSettings(db_path=str(tmp_path / "ltm.db"))
    us.add_model("user-a", label="gw", model="m", base_url="http://localhost:11434/v1")
    mid = us.list_models("user-a")[0]["id"]
    assert us.update_model_key("user-b", mid, "x") is False


# ── API：PUT /api/v1/models/{id}/key ──────────────────


def test_put_key_custom_model():
    resp = client.post(
        "/api/v1/models",
        headers=HEADERS,
        json={"label": "key test model", "model": "m", "base_url": "http://localhost:11434/v1"},
    )
    assert resp.status_code == 201
    mid = resp.json()["id"]
    resp2 = client.put(f"/api/v1/models/{mid}/key", headers=HEADERS, json={"api_key": "sk-123"})
    assert resp2.status_code == 200
    assert resp2.json() == {"ok": True, "has_key": True}
    resp3 = client.delete(f"/api/v1/models/{mid}", headers=HEADERS)
    assert resp3.status_code == 200


def test_put_key_builtin_writes_env(monkeypatch):
    captured: dict[str, str] = {}

    def _fake_set(env_name: str, api_key: str, env_path=None):
        captured[env_name] = api_key

    monkeypatch.setattr(server, "set_env_api_key", _fake_set)
    resp = client.put(
        "/api/v1/models/deepseek-v4-pro/key",
        headers=HEADERS,
        json={"api_key": "sk-builtin-new"},
    )
    assert resp.status_code == 200
    assert captured.get("DEEPSEEK_API_KEY") == "sk-builtin-new"


def test_put_key_unknown_model():
    resp = client.put(
        "/api/v1/models/not-exist-xyz/key",
        headers=HEADERS,
        json={"api_key": "k"},
    )
    assert resp.status_code == 404


def test_put_key_empty_rejected():
    resp = client.put(
        "/api/v1/models/deepseek-v4-pro/key",
        headers=HEADERS,
        json={"api_key": " "},
    )
    assert resp.status_code == 400
