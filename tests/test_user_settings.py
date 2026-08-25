"""Settings 设置模块测试（SPEC: docs/GIS-智能助手-Settings模块设计文档.md）

覆盖（第 9.1 节）:
1. 用户标量设置 CRUD：PUT 写入、GET 读取、无记录返回默认、非法 model_id 400
2. 用户自定义模型 CRUD：POST 生成 id、DELETE 隔离、内置模型 DELETE 403
3. 注册表叠加：load_registry(user_key) 内置+自定义合并、同名 id 用户优先
4. 连通性测试：mock OpenAI 客户端成功/失败两分支
"""

import hashlib

import pytest
from fastapi.testclient import TestClient
from src.gis_toolkit.user_settings import UserSettings, probe_model_connection
from src.llm.models import load_registry, reload_registry
from src.web import server

client = TestClient(server.app)
HEADERS = {"X-API-Key": "settings-test-key"}
# 与 auth.get_user_id 一致：Key 哈希前 16 位
TEST_UID = hashlib.sha256(b"settings-test-key").hexdigest()[:16]


@pytest.fixture()
def us(tmp_path):
    """每个测试独立的 UserSettings（隔离的 SQLite）"""
    return UserSettings(str(tmp_path / "settings_test.db"))


# ════════════════════════════════════════════════════════════
# 1. 用户标量设置 CRUD
# ════════════════════════════════════════════════════════════


def test_settings_default_when_empty(us):
    """无记录时返回系统默认"""
    s = us.get_settings("user-a")
    assert s["model_id"] == "deepseek-v4-pro"
    assert s["theme"] == "dark"
    assert s["permission_mode"] == "ask"


def test_settings_put_get_roundtrip(us):
    """PUT 部分字段 → GET 返回合并后的完整快照"""
    saved = us.save_settings("user-a", {"theme": "light", "permission_mode": "auto"})
    assert saved["theme"] == "light"
    assert saved["permission_mode"] == "auto"
    assert saved["model_id"] == "deepseek-v4-pro"  # 未改字段保持默认

    got = us.get_settings("user-a")
    assert got["theme"] == "light"
    assert got["permission_mode"] == "auto"


def test_settings_reject_unknown_model(us):
    """非法 model_id 拒绝写入"""
    with pytest.raises(ValueError):
        us.save_settings("user-a", {"model_id": "no-such-model"})


def test_settings_isolated_by_user(us):
    """A 用户设置不影响 B 用户"""
    us.save_settings("user-a", {"theme": "light"})
    assert us.get_settings("user-b")["theme"] == "dark"


# ════════════════════════════════════════════════════════════
# 2. 用户自定义模型 CRUD
# ════════════════════════════════════════════════════════════


def test_add_model_generates_slug(us):
    """POST 从 label 生成 slug id"""
    m = us.add_model(
        "user-a",
        label="My Gateway",
        model="qwen2.5:7b",
        base_url="http://localhost:11434/v1",
    )
    assert m["id"] == "my-gateway"
    assert m["is_custom"] is True


def test_add_model_conflict_appends_number(us):
    """同名 label 冲突追加序号"""
    us.add_model("user-a", label="My Gateway", model="a", base_url="http://localhost:11434/v1")
    m2 = us.add_model("user-a", label="My Gateway", model="b", base_url="http://localhost:11434/v1")
    assert m2["id"] == "my-gateway-2"


def test_add_model_reject_duplicate_endpoint(us):
    """重复 (user_key, base_url, model) 拒绝"""
    us.add_model("user-a", label="Gw", model="m1", base_url="http://localhost:11434/v1")
    with pytest.raises(ValueError):
        us.add_model("user-a", label="Gw2", model="m1", base_url="http://localhost:11434/v1")


def test_delete_custom_model(us):
    """删除用户自定义模型成功"""
    m = us.add_model("user-a", label="Gw", model="m1", base_url="http://localhost:11434/v1")
    assert us.delete_model("user-a", m["id"]) is True
    assert us.list_models("user-a") == []


def test_models_isolated_by_user(us):
    """A 的模型 B 不可见/不可删"""
    us.add_model("user-a", label="Gw", model="m1", base_url="http://localhost:11434/v1")
    assert len(us.list_models("user-b")) == 0
    assert us.delete_model("user-b", "gw") is False


def test_models_input_validation(us):
    """输入净化：base_url 必须 http(s) 开头、label 非空、禁换行"""
    with pytest.raises(ValueError):
        us.add_model("user-a", label="Gw", model="m1", base_url="ftp://bad")
    with pytest.raises(ValueError):
        us.add_model("user-a", label="", model="m1", base_url="http://localhost:11434/v1")
    with pytest.raises(ValueError):
        us.add_model("user-a", label="Gw\n evil", model="m1", base_url="http://localhost:11434/v1")


# ════════════════════════════════════════════════════════════
# 3. 注册表叠加（内置 ⊕ 用户自定义）
# ════════════════════════════════════════════════════════════


def test_load_registry_merges_custom(tmp_path, monkeypatch):
    """load_registry(user_key) 内置 + 自定义合并，is_custom 标记正确"""
    us = UserSettings(str(tmp_path / "merge.db"))
    us.add_model(
        "user-a", label="Ollama Local", model="qwen2.5:7b", base_url="http://localhost:11434/v1"
    )
    monkeypatch.setattr("src.llm.models._USER_SETTINGS", us)
    reload_registry()
    try:
        reg = load_registry(user_key="settings:user-a")
        assert reg.get("deepseek-v4-pro") is not None  # 内置仍在
        cfg = reg.get("ollama-local")
        assert cfg is not None
        assert cfg.is_custom is True
        assert cfg.base_url == "http://localhost:11434/v1"
        assert cfg.requires_key is False  # 本机不强制 key
    finally:
        reload_registry()


def test_load_registry_custom_overrides_builtin(tmp_path, monkeypatch):
    """同名 id 用户自定义优先"""
    us = UserSettings(str(tmp_path / "override.db"))
    us.add_model(
        "user-a",
        label="DeepSeek V4 Pro",
        model="deepseek-v4-pro",
        base_url="http://localhost:11434/v1",
    )
    monkeypatch.setattr("src.llm.models._USER_SETTINGS", us)
    reload_registry()
    try:
        reg = load_registry(user_key="settings:user-a")
        assert reg.get("deepseek-v4-pro").is_custom is True  # 用户自定义覆盖内置
        assert reg.get("deepseek-v4-pro").base_url == "http://localhost:11434/v1"
    finally:
        reload_registry()


def test_load_registry_without_user_key_untouched():
    """不带 user_key 时行为与原来一致（不影响存量测试）"""
    reg = load_registry()
    assert reg.get("deepseek-v4-pro") is not None


# ════════════════════════════════════════════════════════════
# 4. 连通性测试
# ════════════════════════════════════════════════════════════


def test_probe_connection_success(monkeypatch):
    """mock 成功：返回 ok true + latency"""
    calls = {}

    class _FakeCompletions:
        def __init__(self, *a, **k):
            pass

        def create(self, **kwargs):
            calls["model"] = kwargs.get("model")
            calls["max_tokens"] = kwargs.get("max_tokens")
            return type(
                "R",
                (),
                {"choices": [type("C", (), {"message": type("M", (), {"content": "hi"})()})]},
            )

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        @property
        def chat(self):
            return type("Chat", (), {"completions": _FakeCompletions()})()

    monkeypatch.setattr("src.gis_toolkit.user_settings.OpenAI", _FakeClient)
    result = probe_model_connection("http://localhost:11434/v1", "qwen2.5:7b", None)
    assert result["ok"] is True
    assert result["latency_ms"] >= 0
    assert calls["max_tokens"] == 8  # 最小请求


def test_probe_connection_failure(monkeypatch):
    """mock 失败：返回 ok false + 明确 message，不抛异常"""

    class _FakeClient:
        def __init__(self, *a, **k):
            raise ConnectionError("连不上 11434")

    monkeypatch.setattr("src.gis_toolkit.user_settings.OpenAI", _FakeClient)
    result = probe_model_connection("http://localhost:11434/v1", "qwen2.5:7b", None)
    assert result["ok"] is False
    assert "11434" in result["message"]


# ════════════════════════════════════════════════════════════
# 5. Web API 层
# ════════════════════════════════════════════════════════════


@pytest.fixture()
def api_us(tmp_path, monkeypatch):
    """server 用户设置换隔离实例；注册表叠加源同步替换（user_id 走真实哈希）"""
    import src.llm.models as models_mod

    us = UserSettings(str(tmp_path / "api.db"))
    monkeypatch.setattr(server, "usettings", us)
    monkeypatch.setattr(models_mod, "_USER_SETTINGS", us)
    models_mod.reload_registry()
    yield us
    models_mod.reload_registry()  # 恢复缓存，避免污染后续用例


def test_api_settings_roundtrip(api_us):
    r = client.put("/api/v1/settings", json={"theme": "light"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["theme"] == "light"

    r2 = client.get("/api/v1/settings", headers=HEADERS)
    assert r2.status_code == 200
    assert r2.json()["theme"] == "light"


def test_api_settings_reject_bad_model(api_us):
    r = client.put("/api/v1/settings", json={"model_id": "nope"}, headers=HEADERS)
    assert r.status_code == 400


def test_api_models_returns_merged(api_us):
    api_us.add_model(
        TEST_UID, label="Ollama Local", model="qwen2.5:7b", base_url="http://localhost:11434/v1"
    )
    r = client.get("/api/v1/models", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    ids = {m["id"] for m in data["models"]}
    assert "deepseek-v4-pro" in ids
    assert "ollama-local" in ids
    assert data["default"] == "deepseek-v4-pro"


def test_api_models_add_delete(api_us):
    r = client.post(
        "/api/v1/models",
        json={
            "label": "My Gateway",
            "model": "qwen2.5:7b",
            "base_url": "http://localhost:11434/v1",
            "api_key": "",
            "capabilities": ["chat", "tools"],
        },
        headers=HEADERS,
    )
    assert r.status_code == 201
    mid = r.json()["id"]
    assert mid == "my-gateway"

    r2 = client.delete(f"/api/v1/models/{mid}", headers=HEADERS)
    assert r2.status_code == 200
    assert r2.json()["ok"] is True


def test_api_delete_builtin_forbidden(api_us):
    r = client.delete("/api/v1/models/deepseek-v4-pro", headers=HEADERS)
    assert r.status_code == 403


def test_api_add_model_invalid_base_url(api_us):
    r = client.post(
        "/api/v1/models",
        json={"label": "Bad", "model": "m", "base_url": "ftp://x"},
        headers=HEADERS,
    )
    assert r.status_code == 400


def test_api_model_test_ok(api_us, monkeypatch):
    """API 连通性测试：mock 成功（patch server 模块里的引用）"""
    monkeypatch.setattr(
        server,
        "probe_model_connection",
        lambda *a, **k: {"ok": True, "latency_ms": 5, "message": "ok"},
    )
    api_us.add_model(
        TEST_UID, label="Ollama Local", model="qwen2.5:7b", base_url="http://localhost:11434/v1"
    )
    r = client.post("/api/v1/models/ollama-local/test", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["ok"] is True
