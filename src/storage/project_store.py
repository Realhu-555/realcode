"""项目持久化存储 — SQLite + 用户隔离

替换 server.py 中的 _content_pipelines 内存字典。
服务重启后数据不丢失。
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class ProjectStore:
    """用户隔离的项目存储"""

    def __init__(self, db_path: str = "data/projects.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                created_by TEXT NOT NULL DEFAULT '',
                product_name TEXT NOT NULL DEFAULT '',
                product_description TEXT DEFAULT '',
                target_users TEXT DEFAULT '',
                key_selling_points TEXT DEFAULT '[]',
                brand_tone TEXT DEFAULT '',
                competitors TEXT DEFAULT '[]',
                user_idea TEXT DEFAULT '',
                input_mode TEXT DEFAULT 'form',
                strategy TEXT,
                gzh_content TEXT,
                zhihu_content TEXT,
                xhs_content TEXT,
                review_report TEXT,
                status TEXT DEFAULT 'draft',
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        # 迁移：旧表加 created_by 列
        try:
            conn.execute("ALTER TABLE projects ADD COLUMN created_by TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 列已存在
        conn.commit()
        conn.close()

    # ════════════════════════════════════════════════════════
    # CRUD
    # ════════════════════════════════════════════════════════

    def save(self, project_id: str, state: dict, user_id: str = ""):
        now = datetime.now().isoformat()
        conn = self._get_conn()

        existing = conn.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
        created_at = now
        if existing:
            conn.execute("SELECT created_at FROM projects WHERE id=?", (project_id,))
            row = conn.execute("SELECT created_at FROM projects WHERE id=?", (project_id,)).fetchone()
            if row:
                created_at = row["created_at"]

        conn.execute("""
            INSERT OR REPLACE INTO projects
            (id, created_by, product_name, product_description, target_users,
             key_selling_points, brand_tone, competitors, user_idea, input_mode,
             strategy, gzh_content, zhihu_content, xhs_content, review_report,
             status, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, user_id,
            str(state.get("product_name", "")), str(state.get("product_description", "")),
            str(state.get("target_users", "")),
            json.dumps(state.get("key_selling_points", []), ensure_ascii=False),
            str(state.get("brand_tone", "")),
            json.dumps(state.get("competitors", []), ensure_ascii=False),
            str(state.get("user_idea", "")), str(state.get("input_mode", "form")),
            str(state.get("strategy") or ""), str(state.get("gzh_content") or ""),
            str(state.get("zhihu_content") or ""), str(state.get("xhs_content") or ""),
            str(state.get("review_report") or ""),
            str(state.get("current_stage", "draft")), str(state.get("error_message") or ""),
            created_at, now,
        ))
        conn.commit()
        conn.close()

    def get(self, project_id: str, user_id: str = "") -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM projects WHERE id=? AND (created_by=? OR created_by='')",
            (project_id, user_id),
        ).fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM projects WHERE created_by=? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [self._row_to_dict(r) for r in rows]

    # ════════════════════════════════════════════════════════
    # Helpers
    # ════════════════════════════════════════════════════════

    @staticmethod
    def _row_to_dict(row) -> dict:
        d = dict(row)
        for field in ("key_selling_points", "competitors"):
            raw = d.get(field, "[]")
            if isinstance(raw, str):
                try:
                    d[field] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    d[field] = []
        # 转成前端期望的格式
        stage = d.get("status", "draft")
        strategy = {"full_content": d["strategy"]} if d.get("strategy") else None
        contents = {
            "gongzhonghao": {"full_content": d["gzh_content"]} if d.get("gzh_content") else None,
            "zhihu": {"full_content": d["zhihu_content"]} if d.get("zhihu_content") else None,
            "xiaohongshu": {"full_content": d["xhs_content"]} if d.get("xhs_content") else None,
        }
        review = {"full_content": d["review_report"]} if d.get("review_report") else None
        return {
            "project_id": d["id"],
            "stage": stage,
            "ask_user": d.get("ask_user"),
            "strategy": strategy,
            "contents": contents,
            "review_report": review,
            "created_at": d.get("created_at", ""),
            "updated_at": d.get("updated_at", ""),
            "_full": d,  # 原始状态，Agent 运行时用
        }


# 全局单例
store = ProjectStore()
