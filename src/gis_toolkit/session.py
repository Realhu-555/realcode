"""GIS 助手会话管理 — 多轮连续对话 + 会话持久化

每个会话持有可复用的 GisEngine（保留当前图层与产物）和完整对话历史。
- 空闲超时清理内存，但会话元数据/历史/图层快照持久化到 JSON，可跨进程恢复
- 图层以 GeoJSON 快照到会话输出目录，恢复会话时自动重新加载
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import suppress
from pathlib import Path

from src.gis_toolkit.approval import ApprovalGate
from src.gis_toolkit.engine import create_gis_engine
from src.utils.config import settings

SESSION_TTL_SECONDS = 30 * 60  # 内存中空闲 30 分钟过期（持久化保留）
SESSIONS_DB = "data/gis_sessions.json"
SESSION_MESSAGE_CAP = 200  # 持久化历史上限（超出丢弃最旧轮次，防止 JSON 无限膨胀）


class GisSession:
    """单次 GIS 对话会话：引擎状态 + 对话历史 + 展示轮次"""

    def __init__(self, session_id: str, out_dir: Path, title: str = "新会话") -> None:
        self.session_id = session_id
        self.out_dir = Path(out_dir)
        self.engine = create_gis_engine(
            engine=settings.gis_engine,
            out_dir=str(self.out_dir),
            allowed_roots=list(settings.gis_allowed_roots) or ["data"],
        )
        self.approval_gate = ApprovalGate()  # HITL：危险操作审批门（默认 ask）
        self.messages: list[dict] = []  # 完整 LLM 对话消息（system 之外）
        self.summary: str = ""  # 滚动摘要（超出上下文阈值时由 agent 生成）
        self.history: list[dict] = []  # 每轮摘要（user_request + final）
        self.rounds: list[dict] = []  # 每轮展示数据（前端恢复用）
        self.title = title
        self.has_layer = False
        self.last_active = time.time()
        self.created_at = time.time()

    def touch(self) -> None:
        """刷新活跃时间"""
        self.last_active = time.time()

    def append_round(
        self, messages: list[dict], user_request: str, final: str, result: dict
    ) -> None:
        """本轮结束后追加历史：rounds 记录展示数据，图层快照。

        对话原文全量保留（上限 SESSION_MESSAGE_CAP），是否压缩由 agent 的
        滚动摘要策略决定（_prepare_messages 只取最近窗口）。
        """
        self.messages.extend(messages)
        if len(self.messages) > SESSION_MESSAGE_CAP:
            self.messages = self.messages[-SESSION_MESSAGE_CAP:]
        self.history.append({"user_request": user_request, "final": final})
        if not self.title or self.title == "新会话":
            self.title = user_request[:24]
        self.rounds.append(
            {
                "user": user_request,
                "final": final,
                "steps": result.get("steps", 0),
                "outputs": result.get("outputs", []),
                "trajectory": result.get("trajectory", []),
                "timed_out": result.get("timed_out", False),
            }
        )
        self._snapshot_layer()
        self.touch()

    def _snapshot_layer(self) -> None:
        """把当前图层快照为 GeoJSON 到会话输出目录，供跨进程恢复"""
        if self.engine._layer is None:
            self.has_layer = False
            return
        try:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            self.engine.save_layer_snapshot(str(self.out_dir / "layer.geojson"))
            self.has_layer = True
        except Exception:
            self.has_layer = False

    def restore_layer(self) -> None:
        """从快照恢复图层（若存在）"""
        if not self.has_layer:
            return
        snapshot = self.out_dir / "layer.geojson"
        if snapshot.is_file():
            try:
                self.engine.load_data(str(snapshot))
            except Exception:
                self.has_layer = False

    def to_dict(self) -> dict:
        """序列化为可持久化 dict"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.last_active,
            "messages": self.messages,
            "summary": self.summary,
            "history": self.history,
            "rounds": self.rounds,
            "has_layer": self.has_layer,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GisSession:
        """从持久化数据恢复会话（引擎由调用方重建）"""
        sid = data["session_id"]
        out_dir = Path("data/gis_toolkit_out") / sid
        sess = cls(sid, out_dir, title=data.get("title", "新会话"))
        sess.created_at = data.get("created_at", time.time())
        sess.last_active = data.get("updated_at", time.time())
        sess.messages = data.get("messages", [])
        sess.summary = data.get("summary", "")
        sess.history = data.get("history", [])
        sess.rounds = data.get("rounds", [])
        sess.has_layer = data.get("has_layer", False)
        return sess


class GisSessionStore:
    """会话注册表：按用户管理，持久化到 JSON，支持列表/详情/删除"""

    def __init__(self, db_path: str = SESSIONS_DB, ttl: int = SESSION_TTL_SECONDS) -> None:
        self.ttl = ttl
        self.db_path = Path(db_path)
        self._sessions: dict[str, dict[str, GisSession]] = {}  # user_id -> sid -> session

    # ── 生命周期 ──
    def get_or_create(
        self, session_id: str | None = None, user_id: str = "anonymous"
    ) -> tuple[str, GisSession]:
        """按 session_id 复用会话；不存在则新建"""
        user_map = self._sessions.setdefault(user_id, {})
        if session_id and session_id in user_map:
            sess = user_map[session_id]
            sess.touch()
            return session_id, sess
        if session_id:
            restored = self._restore(session_id, user_id)
            if restored is not None:
                user_map[session_id] = restored
                return session_id, restored
        sid = uuid.uuid4().hex[:12]
        out_dir = Path("data/gis_toolkit_out") / sid
        out_dir.mkdir(parents=True, exist_ok=True)
        sess = GisSession(sid, out_dir)
        user_map[sid] = sess
        self._persist(user_id)
        self._cleanup(user_id)
        return sid, sess

    def save(self, user_id: str, session: GisSession) -> None:
        """持久化会话"""
        self._sessions.setdefault(user_id, {})[session.session_id] = session
        self._persist(user_id)

    def list_sessions(self, user_id: str) -> list[dict]:
        """返回会话摘要列表（按更新时间倒序）"""
        data = self._read_user(user_id)
        items = [
            {
                "session_id": sid,
                "title": d.get("title", "新会话"),
                "created_at": d.get("created_at", 0),
                "updated_at": d.get("updated_at", 0),
                "rounds": len(d.get("rounds", [])),
            }
            for sid, d in data.items()
        ]
        items.sort(key=lambda x: x["updated_at"], reverse=True)
        return items

    def get_detail(self, user_id: str, session_id: str) -> dict | None:
        """返回会话详情（含每轮展示数据，前端恢复对话用）"""
        data = self._read_user(user_id)
        d = data.get(session_id)
        if not d:
            return None
        return {
            "session_id": session_id,
            "title": d.get("title", "新会话"),
            "created_at": d.get("created_at", 0),
            "updated_at": d.get("updated_at", 0),
            "rounds": d.get("rounds", []),
        }

    def delete(self, user_id: str, session_id: str) -> bool:
        """删除会话（内存 + 持久化 + 输出目录）"""
        if session_id in self._sessions.get(user_id, {}):
            del self._sessions[user_id][session_id]
        data = self._read_user(user_id)
        if session_id not in data:
            return False
        del data[session_id]
        self._write_user(user_id, data)
        out_dir = Path("data/gis_toolkit_out") / session_id
        if out_dir.is_dir():
            with suppress(OSError):
                for f in out_dir.iterdir():
                    f.unlink()
            with suppress(OSError):
                out_dir.rmdir()
        return True

    def clear(self) -> None:
        """清空内存会话（测试用）"""
        self._sessions.clear()

    # ── 持久化 ──
    def _restore(self, session_id: str, user_id: str) -> GisSession | None:
        """从 JSON 恢复会话（引擎重建 + 图层快照恢复）"""
        data = self._read_user(user_id)
        d = data.get(session_id)
        if not d:
            return None
        try:
            sess = GisSession.from_dict(d)
            sess.restore_layer()
            return sess
        except Exception:
            return None

    def _read_user(self, user_id: str) -> dict:
        """读取指定用户的持久化会话数据"""
        if not self.db_path.is_file():
            return {}
        try:
            with self.db_path.open("r", encoding="utf-8") as f:
                all_data = json.load(f)
            return all_data.get(user_id, {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_user(self, user_id: str, data: dict) -> None:
        """写入指定用户的持久化会话数据（合并其它用户）"""
        all_data: dict = {}
        if self.db_path.is_file():
            try:
                with self.db_path.open("r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                all_data = {}
        all_data[user_id] = data
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.db_path.open("w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=1)

    def _persist(self, user_id: str) -> None:
        """把某用户内存会话合并写入 JSON"""
        data = self._read_user(user_id)
        for sid, sess in self._sessions.get(user_id, {}).items():
            data[sid] = sess.to_dict()
        self._write_user(user_id, data)

    def _cleanup(self, user_id: str) -> None:
        """清理某用户内存中的空闲超时会话（持久化保留）"""
        now = time.time()
        user_map = self._sessions.get(user_id, {})
        expired = [k for k, s in user_map.items() if now - s.last_active > self.ttl]
        for k in expired:
            del user_map[k]
