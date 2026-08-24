"""长期记忆管理模块

提供跨项目的知识积累能力，支持：
- 项目信息存储和检索
- 经验教训管理
- 用户偏好学习
- 语义搜索类似项目
- 品牌档案管理（营销内容平台新增）
- 内容项目管理（营销内容平台新增）
"""

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# ── 轻量向量化（自研哈希特征，无外部依赖） ──────────────────────────
# 说明：经验教训的语义检索不引入 ChromaDB/外部 embedding 服务，用
# 字符 n-gram 哈希特征向量（hashing trick）+ 余弦相似度实现轻量语义召回，
# 对中文短文本足够且零依赖、确定性可复现。
_EMBED_DIM = 256


def _feature_hash(feature: str, dim: int, salt: str) -> int:
    """对特征做带盐 MD5 哈希映射到 [0, dim)"""
    return int(hashlib.md5((salt + feature).encode("utf-8")).hexdigest(), 16) % dim


def _tokenize(text: str) -> list[str]:
    """中文按 单字 + 2-gram + 3-gram，英文/数字按小写词切分"""
    tokens: list[str] = []
    tokens.extend(re.findall(r"[a-z0-9]+", text.lower()))
    cjk = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    tokens.extend(cjk)
    for i in range(len(cjk) - 1):
        tokens.append(cjk[i : i + 2])
    for i in range(len(cjk) - 2):
        tokens.append(cjk[i : i + 3])
    return tokens


def _embed_vector(text: str, dim: int = _EMBED_DIM) -> list[float]:
    """文本 → L2 归一化特征向量（随机符号哈希）"""
    vec = [0.0] * dim
    for feat in _tokenize(text or ""):
        idx = _feature_hash(feat, dim, "w")
        sign = 1.0 if _feature_hash(feat, dim, "s") % 2 == 0 else -1.0
        vec[idx] += sign
    norm = sum(x * x for x in vec) ** 0.5
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    """两个已归一化向量的余弦相似度（点积）"""
    return sum(x * y for x, y in zip(a, b, strict=False))


@dataclass
class ProjectRecord:
    """项目记录"""

    id: str
    name: str
    idea: str
    tech_stack: dict[str, Any]
    modules: list[str]
    status: str  # completed / failed / in_progress
    quality_score: float  # 测试通过率
    review_rounds: int  # 总审阅轮次
    token_used: int
    created_at: str | None = None

    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "idea": self.idea,
            "tech_stack": json.dumps(self.tech_stack, ensure_ascii=False),
            "modules": json.dumps(self.modules, ensure_ascii=False),
            "status": self.status,
            "quality_score": self.quality_score,
            "review_rounds": self.review_rounds,
            "token_used": self.token_used,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectRecord":
        """从字典创建项目记录"""
        tech_stack = data.get("tech_stack", "{}")
        if isinstance(tech_stack, str):
            tech_stack = json.loads(tech_stack)

        modules = data.get("modules", "[]")
        if isinstance(modules, str):
            modules = json.loads(modules)

        return cls(
            id=data["id"],
            name=data["name"],
            idea=data["idea"],
            tech_stack=tech_stack,
            modules=modules,
            status=data["status"],
            quality_score=data.get("quality_score", 0.0),
            review_rounds=data.get("review_rounds", 0),
            token_used=data.get("token_used", 0),
            created_at=data.get("created_at"),
        )


@dataclass
class Lesson:
    """经验教训"""

    id: str
    project_id: str
    agent_name: str
    category: str  # success / failure / preference / bug
    lesson: str
    created_at: str | None = None

    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "agent_name": self.agent_name,
            "category": self.category,
            "lesson": self.lesson,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lesson":
        """从字典创建经验教训"""
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            agent_name=data["agent_name"],
            category=data["category"],
            lesson=data["lesson"],
            created_at=data.get("created_at"),
        )


@dataclass
class UserPreference:
    """用户偏好"""

    key: str
    value: str
    confidence: float  # 置信度（多次确认后提高）
    updated_at: str | None = None

    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreference":
        """从字典创建用户偏好"""
        return cls(
            key=data["key"],
            value=data["value"],
            confidence=data.get("confidence", 0.5),
            updated_at=data.get("updated_at"),
        )


class LongTermMemory:
    """长期记忆管理器

    管理跨项目的知识积累，支持：
    - 项目信息存储和检索
    - 经验教训管理
    - 用户偏好学习
    - 语义搜索类似项目
    """

    def __init__(self, db_path: str = "long_term_memory.db") -> None:
        """初始化长期记忆管理器。

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建项目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                idea TEXT NOT NULL,
                tech_stack TEXT,
                modules TEXT,
                status TEXT DEFAULT 'in_progress',
                quality_score FLOAT DEFAULT 0.0,
                review_rounds INTEGER DEFAULT 0,
                token_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建经验教训表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                agent_name TEXT,
                category TEXT,
                lesson TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # 经验教训向量表（语义检索用；无向量时回退文本匹配）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_embeddings (
                lesson_id TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建用户偏好表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                confidence FLOAT DEFAULT 0.5,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 品牌档案表（营销内容平台 — 新增）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                target_users TEXT,
                key_selling_points TEXT,
                tone TEXT,
                competitors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        # 内容项目表（营销内容平台 — 新增）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_projects (
                id TEXT PRIMARY KEY,
                created_by TEXT NOT NULL DEFAULT '',
                product_name TEXT NOT NULL,
                product_description TEXT,
                target_users TEXT,
                key_selling_points TEXT,
                brand_tone TEXT,
                competitors TEXT,
                user_idea TEXT,
                input_mode TEXT DEFAULT 'form',
                strategy TEXT,
                gzh_content TEXT,
                zhihu_content TEXT,
                xhs_content TEXT,
                review_report TEXT,
                status TEXT DEFAULT 'draft',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_project(self, project: ProjectRecord) -> None:
        """保存项目记录。

        Args:
            project: 项目记录
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        data = project.to_dict()
        cursor.execute(
            """
            INSERT OR REPLACE INTO projects
            (id, name, idea, tech_stack, modules, status, quality_score,
             review_rounds, token_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["name"],
                data["idea"],
                data["tech_stack"],
                data["modules"],
                data["status"],
                data["quality_score"],
                data["review_rounds"],
                data["token_used"],
                data["created_at"],
            ),
        )
        conn.commit()
        conn.close()

    def get_project(self, project_id: str) -> ProjectRecord | None:
        """获取项目记录。

        Args:
            project_id: 项目 ID

        Returns:
            项目记录，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        # 转换为字典
        columns = [
            "id",
            "name",
            "idea",
            "tech_stack",
            "modules",
            "status",
            "quality_score",
            "review_rounds",
            "token_used",
            "created_at",
        ]
        data = dict(zip(columns, row, strict=False))
        return ProjectRecord.from_dict(data)

    def list_projects(self) -> list[ProjectRecord]:
        """列出所有项目。

        Returns:
            项目记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        projects = []
        columns = [
            "id",
            "name",
            "idea",
            "tech_stack",
            "modules",
            "status",
            "quality_score",
            "review_rounds",
            "token_used",
            "created_at",
        ]
        for row in rows:
            data = dict(zip(columns, row, strict=False))
            projects.append(ProjectRecord.from_dict(data))

        return projects

    def delete_project(self, project_id: str) -> None:
        """删除项目及其相关经验。

        Args:
            project_id: 项目 ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lessons WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()

    def save_lesson(self, lesson: Lesson) -> None:
        """保存经验教训（同步写入语义向量，向量失败不阻断主写入）。

        Args:
            lesson: 经验教训
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        data = lesson.to_dict()
        cursor.execute(
            """
            INSERT OR REPLACE INTO lessons
            (id, project_id, agent_name, category, lesson, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["project_id"],
                data["agent_name"],
                data["category"],
                data["lesson"],
                data["created_at"],
            ),
        )
        try:
            embedding = json.dumps(_embed_vector(lesson.lesson))
            cursor.execute(
                "INSERT OR REPLACE INTO lesson_embeddings (lesson_id, embedding) VALUES (?, ?)",
                (data["id"], embedding),
            )
        except Exception:
            pass  # 向量生成失败不影响经验教训主记录
        conn.commit()
        conn.close()

    def _embed_text(self, text: str, dim: int = _EMBED_DIM) -> list[float]:
        """暴露给上层/测试的文本向量化（确定性可复现）"""
        return _embed_vector(text, dim)

    def _get_lesson_embeddings(self, lesson_id: str) -> str | None:
        """按 lesson id 取向量 JSON（无记录返回 None）"""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT embedding FROM lesson_embeddings WHERE lesson_id = ?", (lesson_id,)
        ).fetchone()
        conn.close()
        return row[0] if row else None

    def _all_lesson_embeddings(self) -> list[tuple[str, list[float]]]:
        """返回全部 (lesson_id, 向量) 列表"""
        conn = self._get_connection()
        rows = conn.execute("SELECT lesson_id, embedding FROM lesson_embeddings").fetchall()
        conn.close()
        out: list[tuple[str, list[float]]] = []
        for lesson_id, emb_str in rows:
            try:
                out.append((lesson_id, json.loads(emb_str)))
            except Exception:
                continue
        return out

    def semantic_search_lessons(
        self,
        query: str,
        limit: int = 5,
        agent_name: str | None = None,
    ) -> list[Lesson]:
        """按语义相关性召回经验教训（余弦 top-k）。

        Args:
            query: 查询文本
            limit: 最大返回数量
            agent_name: 按 agent 过滤（如按用户隔离）

        Returns:
            相关经验教训列表（按相关性降序）
        """
        query_vec = _embed_vector(query)
        scored: list[tuple[float, str]] = []
        for lesson_id, emb in self._all_lesson_embeddings():
            score = _cosine(query_vec, emb)
            if score > 0:
                scored.append((score, lesson_id))
        scored.sort(key=lambda x: x[0], reverse=True)

        lessons = self.get_lessons(agent_name=agent_name)
        by_id = {item.id: item for item in lessons}
        out: list[Lesson] = []
        for _score, lesson_id in scored[:limit]:
            if lesson_id in by_id:
                out.append(by_id[lesson_id])
        return out

    def get_lessons(
        self,
        project_id: str | None = None,
        agent_name: str | None = None,
        category: str | None = None,
    ) -> list[Lesson]:
        """获取经验教训。

        Args:
            project_id: 按项目 ID 过滤
            agent_name: 按 Agent 名称过滤
            category: 按类别过滤

        Returns:
            经验教训列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM lessons WHERE 1=1"
        params: list[Any] = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        lessons = []
        columns = ["id", "project_id", "agent_name", "category", "lesson", "created_at"]
        for row in rows:
            data = dict(zip(columns, row, strict=False))
            lessons.append(Lesson.from_dict(data))

        return lessons

    def save_user_preference(self, preference: UserPreference) -> None:
        """保存用户偏好。

        Args:
            preference: 用户偏好
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        data = preference.to_dict()
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_preferences
            (key, value, confidence, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (data["key"], data["value"], data["confidence"], data["updated_at"]),
        )
        conn.commit()
        conn.close()

    def get_user_preference(self, key: str) -> UserPreference | None:
        """获取用户偏好。

        Args:
            key: 偏好键名

        Returns:
            用户偏好，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        columns = ["key", "value", "confidence", "updated_at"]
        data = dict(zip(columns, row, strict=False))
        return UserPreference.from_dict(data)

    def update_preference_confidence(self, key: str, boost: float) -> None:
        """更新用户偏好置信度。

        Args:
            key: 偏好键名
            boost: 置信度增量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE user_preferences
            SET confidence = MIN(1.0, confidence + ?),
                updated_at = ?
            WHERE key = ?
            """,
            (boost, datetime.now().isoformat(), key),
        )
        conn.commit()
        conn.close()

    def search_similar_projects(self, query: str, limit: int = 5) -> list[ProjectRecord]:
        """搜索类似项目（简单文本匹配）。

        注意：完整实现应使用 ChromaDB 进行语义搜索。

        Args:
            query: 查询文本
            limit: 最大返回数量

        Returns:
            类似项目列表
        """
        projects = self.list_projects()
        query_lower = query.lower()
        # 将查询拆分为关键词进行匹配
        query_keywords = set(query_lower.split())

        # 简单评分：计算查询词在项目信息中的出现次数
        scored_projects: list[tuple[float, ProjectRecord]] = []
        for project in projects:
            score = 0.0
            # 检查项目名称
            if query_lower in project.name.lower():
                score += 2.0
            # 检查需求描述
            if query_lower in project.idea.lower():
                score += 3.0
            # 检查关键词匹配
            idea_lower = project.idea.lower()
            for keyword in query_keywords:
                if keyword in idea_lower:
                    score += 0.5
                if keyword in project.name.lower():
                    score += 0.3
            # 检查模块
            for module in project.modules:
                if query_lower in module.lower():
                    score += 1.0
                for keyword in query_keywords:
                    if keyword in module.lower():
                        score += 0.3
            # 检查技术栈
            for tech in project.tech_stack.values():
                if query_lower in str(tech).lower():
                    score += 1.0

            if score > 0:
                scored_projects.append((score, project))

        # 按分数排序
        scored_projects.sort(key=lambda x: x[0], reverse=True)

        return [project for _, project in scored_projects[:limit]]

    def get_relevant_lessons(self, context: str, limit: int = 5) -> list[Lesson]:
        """获取相关经验教训。

        优先向量语义检索；对无向量的历史数据回退简单文本匹配，
        保证旧库兼容不丢召回。

        Args:
            context: 上下文信息
            limit: 最大返回数量

        Returns:
            相关经验教训列表
        """
        # 语义检索优先（有向量数据的库）
        hits = self.semantic_search_lessons(context, limit=limit)
        if hits:
            return hits

        # 回退：简单文本匹配（兼容无向量历史数据）
        all_lessons = self.get_lessons()
        context_lower = context.lower()

        # 简单评分
        scored_lessons: list[tuple[float, Lesson]] = []
        for lesson in all_lessons:
            score = 0.0
            if context_lower in lesson.lesson.lower():
                score += 2.0
            # 成功经验权重更高
            if lesson.category == "success":
                score *= 1.5
            # 失败经验作为警告
            if lesson.category == "failure":
                score *= 1.2

            if score > 0:
                scored_lessons.append((score, lesson))

        # 按分数排序
        scored_lessons.sort(key=lambda x: x[0], reverse=True)

        return [lesson for _, lesson in scored_lessons[:limit]]

    # ============================================================
    # 品牌档案管理（营销内容平台 — 新增）
    # ============================================================

    def save_brand_profile(self, profile: dict[str, Any]) -> None:
        """保存品牌档案"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO brand_profiles
            (id, name, description, target_users, key_selling_points,
             tone, competitors, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile["id"],
                profile["name"],
                profile.get("description", ""),
                profile.get("target_users", ""),
                json.dumps(profile.get("key_selling_points", []), ensure_ascii=False),
                profile.get("tone", ""),
                json.dumps(profile.get("competitors", []), ensure_ascii=False),
                profile.get("created_at", datetime.now().isoformat()),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def get_brand_profile(self, profile_id: str) -> dict[str, Any] | None:
        """获取品牌档案"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brand_profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_brand_profile(row)

    def list_brand_profiles(self) -> list[dict[str, Any]]:
        """列出所有品牌档案"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brand_profiles ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_brand_profile(row) for row in rows]

    def search_brand_by_name(self, name: str) -> dict[str, Any] | None:
        """按名称搜索品牌档案"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM brand_profiles WHERE name LIKE ? LIMIT 1",
            (f"%{name}%",),
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_brand_profile(row)

    @staticmethod
    def _row_to_brand_profile(row: tuple) -> dict[str, Any]:
        """数据库行 → 品牌档案字典"""
        columns = [
            "id",
            "name",
            "description",
            "target_users",
            "key_selling_points",
            "tone",
            "competitors",
            "created_at",
            "updated_at",
        ]
        data = dict(zip(columns, row, strict=False))
        # 反序列化 JSON 字段
        for field in ("key_selling_points", "competitors"):
            raw = data.get(field, "[]")
            if isinstance(raw, str):
                try:
                    data[field] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    data[field] = []
        return data

    # ============================================================
    # 内容项目管理（营销内容平台 — 新增）
    # ============================================================

    def save_content_project(self, project: dict[str, Any]) -> None:
        """保存内容项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO content_projects
            (id, product_name, product_description, target_users,
             key_selling_points, brand_tone, competitors, user_idea,
             input_mode, strategy, gzh_content, zhihu_content,
             xhs_content, review_report, status, error_message,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project["id"],
                project.get("product_name", ""),
                project.get("product_description", ""),
                project.get("target_users", ""),
                json.dumps(project.get("key_selling_points", []), ensure_ascii=False),
                project.get("brand_tone", ""),
                json.dumps(project.get("competitors", []), ensure_ascii=False),
                project.get("user_idea", ""),
                project.get("input_mode", "form"),
                project.get("strategy", ""),
                project.get("gzh_content", ""),
                project.get("zhihu_content", ""),
                project.get("xhs_content", ""),
                project.get("review_report", ""),
                project.get("status", "draft"),
                project.get("error_message", ""),
                project.get("created_at", datetime.now().isoformat()),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def get_content_project(self, project_id: str) -> dict[str, Any] | None:
        """获取内容项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_content_project(row)

    def list_content_projects(self, limit: int = 20) -> list[dict[str, Any]]:
        """列出最近的内容项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM content_projects ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_content_project(row) for row in rows]

    @staticmethod
    def _row_to_content_project(row: tuple) -> dict[str, Any]:
        """数据库行 → 内容项目字典"""
        columns = [
            "id",
            "product_name",
            "product_description",
            "target_users",
            "key_selling_points",
            "brand_tone",
            "competitors",
            "user_idea",
            "input_mode",
            "strategy",
            "gzh_content",
            "zhihu_content",
            "xhs_content",
            "review_report",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        data = dict(zip(columns, row, strict=False))
        # 反序列化 JSON 字段
        for field in ("key_selling_points", "competitors"):
            raw = data.get(field, "[]")
            if isinstance(raw, str):
                try:
                    data[field] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    data[field] = []
        return data

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息。

        Returns:
            统计信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 项目统计
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(token_used) FROM projects")
        total_tokens = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(quality_score) FROM projects WHERE quality_score > 0")
        avg_quality = cursor.fetchone()[0] or 0.0

        # 经验统计
        cursor.execute("SELECT COUNT(*) FROM lessons")
        total_lessons = cursor.fetchone()[0]

        # 用户偏好统计
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        total_preferences = cursor.fetchone()[0]

        conn.close()

        return {
            "total_projects": total_projects,
            "total_tokens": total_tokens,
            "avg_quality_score": round(avg_quality, 2),
            "total_lessons": total_lessons,
            "total_preferences": total_preferences,
        }

    def close(self) -> None:
        """关闭数据库连接"""
        # SQLite 的连接在每次操作后已经关闭
        pass
