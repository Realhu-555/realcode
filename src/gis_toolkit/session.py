"""GIS 助手会话管理 — 多轮连续对话

每个会话持有一个可复用的 GisEngine（保留当前图层与产物）和完整对话历史。
空闲超时自动清理，避免内存泄漏。
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from src.gis_toolkit.engine import GisEngine

SESSION_TTL_SECONDS = 30 * 60  # 空闲 30 分钟过期


class GisSession:
    """单次 GIS 对话会话：引擎状态 + 对话历史"""

    def __init__(self, session_id: str, out_dir: Path) -> None:
        self.session_id = session_id
        self.out_dir = out_dir
        self.engine = GisEngine(out_dir=str(out_dir), allowed_roots=["data"])
        self.messages: list[dict] = []  # 完整对话消息（system 之外）
        self.history: list[dict] = []  # 每轮摘要（user_request + final）
        self.last_active = time.time()
        self.created_at = time.time()

    def touch(self) -> None:
        """刷新活跃时间"""
        self.last_active = time.time()

    def append_round(self, messages: list[dict], user_request: str, final: str) -> None:
        """本轮结束后追加历史：messages 含 user/assistant/tool，截断至最近 40 条"""
        self.messages.extend(messages)
        if len(self.messages) > 40:
            # 保留最近 2 轮的 user 消息 + 最近 30 条工具往返
            self.messages = self.messages[-30:]
        self.history.append({"user_request": user_request, "final": final})
        self.touch()


class GisSessionStore:
    """会话注册表：get_or_create 复用引擎，空闲超时清理"""

    def __init__(self, ttl: int = SESSION_TTL_SECONDS) -> None:
        self.ttl = ttl
        self._sessions: dict[str, GisSession] = {}

    def get_or_create(self, session_id: str | None = None) -> tuple[str, GisSession]:
        """按 session_id 复用会话；不存在则新建"""
        if session_id and session_id in self._sessions:
            sess = self._sessions[session_id]
            sess.touch()
            return session_id, sess
        sid = uuid.uuid4().hex[:12]
        out_dir = Path("data/gis_toolkit_out") / sid
        out_dir.mkdir(parents=True, exist_ok=True)
        sess = GisSession(sid, out_dir)
        self._sessions[sid] = sess
        self._cleanup()
        return sid, sess

    def get(self, session_id: str) -> GisSession | None:
        """获取会话（不存在返回 None）"""
        return self._sessions.get(session_id)

    def clear(self) -> None:
        """清空所有会话（测试用）"""
        self._sessions.clear()

    def _cleanup(self) -> None:
        """清理空闲超时会话"""
        now = time.time()
        expired = [k for k, s in self._sessions.items() if now - s.last_active > self.ttl]
        for k in expired:
            del self._sessions[k]
