"""用户设置与自定义模型管理（Settings 模块）

对应 docs/GIS-智能助手-Settings模块设计文档.md 第 4 节。

- 用户标量偏好：复用 user_preferences 表，key = `settings:v1:{user_id}`（隔离维度并入 key）
- 用户自定义模型：新增 user_models 表，归属 `settings:{user_id}`（不同用户互不可见）
- 内置模型注册表（models.yaml）为只读基线；运行时与用户自定义叠加，同名 id 用户优先

用法:
    from src.gis_toolkit.user_settings import UserSettings
    us = UserSettings()  # 默认 long_term_memory.db
    us.save_settings("user-a", {"theme": "light"})
    us.add_model("user-a", label="Ollama", model="qwen2.5:7b", base_url="http://localhost:11434/v1")
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from src.llm.models import load_registry

# 合法枚举（对应文档第 5.1 / 5.2 节）
THEMES = {"dark", "light"}
PERMISSION_MODES = {"readonly", "auto", "ask"}
DEFAULT_SETTINGS = {"model_id": None, "theme": "dark", "permission_mode": "ask"}

_SAFE_RE = re.compile(r"[^a-z0-9]+")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
_MAX_LEN = 200


def _is_local_base_url(base_url: str) -> bool:
    """本机地址白名单：localhost / 127.0.0.1 等不强制要求 key"""
    try:
        from urllib.parse import urlparse

        host = (urlparse(base_url).hostname or "").lower().split(":")[0]
        return host in _LOCAL_HOSTS
    except Exception:
        return False


def set_env_api_key(env_name: str, api_key: str, env_path: Path | None = None) -> None:
    """把 API Key 写入项目 .env（保留注释与其他行），并更新当前进程 os.environ。

    供前端设置页配置内置模型 key 使用，避免手动改配置文件。
    """
    api_key = (api_key or "").strip()
    if not api_key or "\n" in api_key or "\r" in api_key:
        raise ValueError("API Key 不能为空或包含换行")
    path = env_path or (Path(__file__).resolve().parents[2] / ".env")
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    pattern = re.compile(rf"^{re.escape(env_name)}\s*=.*$")
    replaced = False
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            lines[i] = f"{env_name}={api_key}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{env_name}={api_key}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[env_name] = api_key


def _clean_text(value: str, field: str) -> str:
    """输入净化：长度 ≤200、禁换行"""
    if not value or "\n" in value or "\r" in value:
        raise ValueError(f"{field} 不能为空或包含换行")
    value = value.strip()
    if len(value) > _MAX_LEN:
        raise ValueError(f"{field} 长度不能超过 {_MAX_LEN} 字符")
    return value


def _slugify(label: str) -> str:
    """label → slug id（小写、非字母数字转连字符）"""
    slug = _SAFE_RE.sub("-", label.strip().lower()).strip("-")
    return slug or "model"


def probe_model_connection(
    base_url: str, model: str, api_key: str | None = None, timeout: float = 8.0
) -> dict[str, Any]:
    """连通性测试：发 1 条最小 chat 请求（max_tokens=8），成功即 ok。

    失败不抛异常，返回 ok=false + 可读 message（供前端内联展示）。
    """
    started = time.monotonic()
    try:
        client = OpenAI(base_url=base_url, api_key=api_key or "none", timeout=timeout)
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=8,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        return {"ok": True, "latency_ms": latency_ms, "message": f"连通正常（{latency_ms}ms）"}
    except Exception as exc:
        return {"ok": False, "message": f"连接失败: {exc}"}


class UserSettings:
    """用户设置 + 自定义模型 存储层（SQLite，独立连接管理）"""

    def __init__(self, db_path: str = "long_term_memory.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                confidence FLOAT DEFAULT 0.5,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_models (
                id          TEXT PRIMARY KEY,
                user_key    TEXT NOT NULL,
                label       TEXT NOT NULL,
                provider    TEXT NOT NULL DEFAULT 'openai-compatible',
                model       TEXT NOT NULL,
                base_url    TEXT NOT NULL,
                api_key     TEXT,
                capabilities TEXT NOT NULL DEFAULT '["chat","tools"]',
                created_at  REAL NOT NULL
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_models_user ON user_models(user_key)")
        conn.commit()
        conn.close()

    @staticmethod
    def _user_key(user_id: str) -> str:
        return f"settings:{user_id}"

    @staticmethod
    def _settings_key(user_id: str) -> str:
        return f"settings:v1:{user_id}"

    # ── 用户标量设置 ──────────────────────────────────────

    def get_settings(self, user_id: str) -> dict[str, Any]:
        """读取用户设置快照；无记录时返回系统默认。"""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM user_preferences WHERE key = ?",
            (self._settings_key(user_id),),
        )
        row = cursor.fetchone()
        conn.close()

        base: dict[str, Any] = {
            "model_id": load_registry().default_model_id(),
            "theme": "dark",
            "permission_mode": "ask",
        }
        if row is None:
            return base
        try:
            saved = json.loads(row[0]) if isinstance(row[0], str) else {}
        except Exception:
            saved = {}
        base.update({k: v for k, v in saved.items() if v is not None})
        return base

    def save_settings(
        self,
        user_id: str,
        patch: dict[str, Any],
        known_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        """合并写入用户设置（整块覆盖写，缺失字段保持原值）。

        Args:
            user_id: 用户 id
            patch: 要更新的字段（model_id / theme / permission_mode）
            known_ids: 合法模型 id 集合（含用户自定义）；None 时用内置注册表

        Raises:
            ValueError: 非法 model_id / theme / permission_mode
        """
        current = self.get_settings(user_id)

        if "model_id" in patch and patch["model_id"] is not None:
            mid = patch["model_id"]
            ids = known_ids if known_ids is not None else set(load_registry().models.keys())
            if mid not in ids:
                raise ValueError(f"未知模型: {mid}（可选: {', '.join(sorted(ids))}）")
            current["model_id"] = mid
        if "theme" in patch and patch["theme"] is not None:
            theme = patch["theme"]
            if theme not in THEMES:
                raise ValueError(f"非法主题: {theme}（可选: dark/light）")
            current["theme"] = theme
        if "permission_mode" in patch and patch["permission_mode"] is not None:
            mode = patch["permission_mode"]
            if mode not in PERMISSION_MODES:
                raise ValueError(f"非法权限模式: {mode}（可选: readonly/auto/ask）")
            current["permission_mode"] = mode

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_preferences (key, value, confidence, updated_at)
            VALUES (?, ?, 0.8, ?)
            """,
            (
                self._settings_key(user_id),
                json.dumps(current, ensure_ascii=False),
                time.strftime("%Y-%m-%dT%H:%M:%S"),
            ),
        )
        conn.commit()
        conn.close()
        return current

    # ── 用户自定义模型 ────────────────────────────────────

    def list_models(self, user_id: str) -> list[dict[str, Any]]:
        """当前用户的全部自定义模型（按创建时间升序）"""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, label, provider, model, base_url, api_key, capabilities, created_at "
            "FROM user_models WHERE user_key = ? ORDER BY created_at ASC",
            (self._user_key(user_id),),
        )
        rows = cursor.fetchall()
        conn.close()
        out: list[dict[str, Any]] = []
        for row in rows:
            try:
                caps = json.loads(row[6]) if isinstance(row[6], str) else ["chat", "tools"]
            except Exception:
                caps = ["chat", "tools"]
            out.append(
                {
                    "id": row[0],
                    "label": row[1],
                    "provider": row[2],
                    "model": row[3],
                    "base_url": row[4],
                    "api_key": row[5],
                    "capabilities": caps,
                    "is_custom": True,
                }
            )
        return out

    def get_model(self, user_id: str, model_id: str) -> dict[str, Any] | None:
        for m in self.list_models(user_id):
            if m["id"] == model_id:
                return m
        return None

    def add_model(
        self,
        user_id: str,
        label: str,
        model: str,
        base_url: str,
        api_key: str | None = "",
        provider: str = "openai-compatible",
        capabilities: list[str] | None = None,
    ) -> dict[str, Any]:
        """新增用户自定义模型，id 由 label 生成 slug，冲突追加序号。"""
        label = _clean_text(label, "label")
        model = _clean_text(model, "model")
        base_url = _clean_text(base_url, "base_url")
        if not base_url.lower().startswith(("http://", "https://")):
            raise ValueError("base_url 必须以 http:// 或 https:// 开头")
        if api_key and ("\n" in api_key or "\r" in api_key or len(api_key) > _MAX_LEN):
            raise ValueError("api_key 非法（长度或字符）")
        caps = list(capabilities or ["chat", "tools"])

        key = self._user_key(user_id)
        existing = self.list_models(user_id)
        for m in existing:
            if m["base_url"] == base_url and m["model"] == model:
                raise ValueError("已存在相同 base_url + model 的模型")

        base_slug = _slugify(label)
        mid = base_slug
        used = {m["id"] for m in existing}
        n = 2
        while mid in used:
            mid = f"{base_slug}-{n}"
            n += 1

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_models "
            "(id, user_key, label, provider, model, base_url, api_key, capabilities, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                mid,
                key,
                label,
                provider,
                model,
                base_url,
                api_key or None,
                json.dumps(caps, ensure_ascii=False),
                time.time(),
            ),
        )
        conn.commit()
        conn.close()
        return self.get_model(user_id, mid) or {
            "id": mid,
            "label": label,
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "api_key": api_key,
            "capabilities": caps,
            "is_custom": True,
        }

    def update_model_key(self, user_id: str, model_id: str, api_key: str | None = None) -> bool:
        """更新用户自定义模型的 API Key；归属不符/不存在返回 False。"""
        api_key = (api_key or "").strip() or None
        if api_key and ("\n" in api_key or "\r" in api_key or len(api_key) > _MAX_LEN):
            raise ValueError("api_key 非法（长度或字符）")
        key = self._user_key(user_id)
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_models SET api_key = ? WHERE id = ? AND user_key = ?",
            (api_key, model_id, key),
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def delete_model(self, user_id: str, model_id: str) -> bool:
        """删除当前用户的模型；不存在返回 False。"""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_models WHERE id = ? AND user_key = ?",
            (model_id, self._user_key(user_id)),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
