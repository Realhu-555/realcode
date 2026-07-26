"""长期记忆模块单元测试

根据设计文档，长期记忆包括：
- 项目信息存储（projects表）
- 经验教训存储（lessons表）
- 用户偏好存储（user_preferences表）
- 语义检索（ChromaDB集成）
"""

import os

from src.orchestrator.long_term_memory import (
    Lesson,
    LongTermMemory,
    ProjectRecord,
    UserPreference,
)
from src.orchestrator.state import (
    get_long_term_memory,
    get_long_term_memory_context,
    get_long_term_memory_statistics,
    get_relevant_lessons_from_state,
    get_user_preferences_from_state,
    save_lesson_to_long_term_memory,
    save_long_term_memory_path,
    save_project_to_long_term_memory,
    save_user_preference_to_long_term_memory,
    search_similar_projects_from_state,
)


class TestProjectRecord:
    """ProjectRecord 测试"""

    def test_create_project_record(self) -> None:
        """测试创建项目记录"""
        record = ProjectRecord(
            id="proj-001",
            name="测试项目",
            idea="创建一个博客系统",
            tech_stack={"backend": "fastapi", "frontend": "vue3"},
            modules=["用户模块", "文章模块"],
            status="completed",
            quality_score=0.85,
            review_rounds=3,
            token_used=15000,
        )
        assert record.id == "proj-001"
        assert record.name == "测试项目"
        assert record.status == "completed"
        assert record.quality_score == 0.85

    def test_to_dict(self) -> None:
        """测试转换为字典"""
        record = ProjectRecord(
            id="proj-001",
            name="测试项目",
            idea="创建一个博客系统",
            tech_stack={"backend": "fastapi"},
            modules=["用户模块"],
            status="completed",
            quality_score=0.85,
            review_rounds=3,
            token_used=15000,
        )
        d = record.to_dict()
        assert d["id"] == "proj-001"
        assert d["name"] == "测试项目"
        assert d["status"] == "completed"

    def test_from_dict(self) -> None:
        """测试从字典创建"""
        d = {
            "id": "proj-001",
            "name": "测试项目",
            "idea": "创建一个博客系统",
            "tech_stack": {"backend": "fastapi"},
            "modules": ["用户模块"],
            "status": "completed",
            "quality_score": 0.85,
            "review_rounds": 3,
            "token_used": 15000,
            "created_at": "2024-01-01T00:00:00",
        }
        record = ProjectRecord.from_dict(d)
        assert record.id == "proj-001"
        assert record.name == "测试项目"


class TestLesson:
    """Lesson 测试"""

    def test_create_lesson(self) -> None:
        """测试创建经验教训"""
        lesson = Lesson(
            id="lesson-001",
            project_id="proj-001",
            agent_name="backend",
            category="success",
            lesson="使用 FastAPI 可以快速搭建 REST API",
        )
        assert lesson.id == "lesson-001"
        assert lesson.project_id == "proj-001"
        assert lesson.agent_name == "backend"
        assert lesson.category == "success"

    def test_to_dict(self) -> None:
        """测试转换为字典"""
        lesson = Lesson(
            id="lesson-001",
            project_id="proj-001",
            agent_name="backend",
            category="success",
            lesson="使用 FastAPI 可以快速搭建 REST API",
        )
        d = lesson.to_dict()
        assert d["id"] == "lesson-001"
        assert d["category"] == "success"

    def test_from_dict(self) -> None:
        """测试从字典创建"""
        d = {
            "id": "lesson-001",
            "project_id": "proj-001",
            "agent_name": "backend",
            "category": "success",
            "lesson": "使用 FastAPI 可以快速搭建 REST API",
            "created_at": "2024-01-01T00:00:00",
        }
        lesson = Lesson.from_dict(d)
        assert lesson.id == "lesson-001"
        assert lesson.category == "success"


class TestUserPreference:
    """UserPreference 测试"""

    def test_create_user_preference(self) -> None:
        """测试创建用户偏好"""
        pref = UserPreference(
            key="frontend_framework",
            value="vue3+element-plus",
            confidence=0.8,
        )
        assert pref.key == "frontend_framework"
        assert pref.value == "vue3+element-plus"
        assert pref.confidence == 0.8

    def test_to_dict(self) -> None:
        """测试转换为字典"""
        pref = UserPreference(
            key="frontend_framework",
            value="vue3+element-plus",
            confidence=0.8,
        )
        d = pref.to_dict()
        assert d["key"] == "frontend_framework"
        assert d["value"] == "vue3+element-plus"

    def test_from_dict(self) -> None:
        """测试从字典创建"""
        d = {
            "key": "frontend_framework",
            "value": "vue3+element-plus",
            "confidence": 0.8,
            "updated_at": "2024-01-01T00:00:00",
        }
        pref = UserPreference.from_dict(d)
        assert pref.key == "frontend_framework"
        assert pref.confidence == 0.8


class TestLongTermMemory:
    """LongTermMemory 测试"""

    def test_init(self) -> None:
        """测试初始化"""
        db_path = "test_memory_init.db"
        try:
            memory = LongTermMemory(db_path=db_path)
            assert memory is not None
            assert os.path.exists(db_path)
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_save_and_get_project(self) -> None:
        """测试保存和获取项目"""
        db_path = "test_memory_projects.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            project = ProjectRecord(
                id="proj-001",
                name="测试项目",
                idea="创建一个博客系统",
                tech_stack={"backend": "fastapi", "frontend": "vue3"},
                modules=["用户模块", "文章模块"],
                status="completed",
                quality_score=0.85,
                review_rounds=3,
                token_used=15000,
            )
            memory.save_project(project)

            retrieved = memory.get_project("proj-001")
            assert retrieved is not None
            assert retrieved.id == "proj-001"
            assert retrieved.name == "测试项目"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_list_projects(self) -> None:
        """测试列出项目"""
        db_path = "test_memory_list.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            # 添加多个项目
            for i in range(3):
                project = ProjectRecord(
                    id=f"proj-{i:03d}",
                    name=f"项目 {i}",
                    idea=f"需求 {i}",
                    tech_stack={},
                    modules=[],
                    status="completed",
                    quality_score=0.8,
                    review_rounds=2,
                    token_used=10000,
                )
                memory.save_project(project)

            projects = memory.list_projects()
            assert len(projects) == 3
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_save_and_get_lesson(self) -> None:
        """测试保存和获取经验教训"""
        db_path = "test_memory_lesson.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            lesson = Lesson(
                id="lesson-001",
                project_id="proj-001",
                agent_name="backend",
                category="success",
                lesson="使用 FastAPI 可以快速搭建 REST API",
            )
            memory.save_lesson(lesson)

            lessons = memory.get_lessons(project_id="proj-001")
            assert len(lessons) == 1
            assert lessons[0].id == "lesson-001"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_get_lessons_by_category(self) -> None:
        """测试按类别获取经验教训"""
        db_path = "test_memory_category.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            # 添加不同类别的经验
            for i, category in enumerate(["success", "failure", "bug"]):
                lesson = Lesson(
                    id=f"lesson-{i:03d}",
                    project_id="proj-001",
                    agent_name="backend",
                    category=category,
                    lesson=f"经验 {i}",
                )
                memory.save_lesson(lesson)

            success_lessons = memory.get_lessons(category="success")
            assert len(success_lessons) == 1
            assert success_lessons[0].category == "success"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_save_and_get_user_preference(self) -> None:
        """测试保存和获取用户偏好"""
        db_path = "test_memory_pref.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            pref = UserPreference(
                key="frontend_framework",
                value="vue3+element-plus",
                confidence=0.8,
            )
            memory.save_user_preference(pref)

            retrieved = memory.get_user_preference("frontend_framework")
            assert retrieved is not None
            assert retrieved.value == "vue3+element-plus"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_update_user_preference_confidence(self) -> None:
        """测试更新用户偏好置信度"""
        db_path = "test_memory_confidence.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            pref = UserPreference(
                key="frontend_framework",
                value="vue3+element-plus",
                confidence=0.5,
            )
            memory.save_user_preference(pref)

            # 多次确认后置信度应该增加
            memory.update_preference_confidence("frontend_framework", 0.1)
            memory.update_preference_confidence("frontend_framework", 0.1)

            retrieved = memory.get_user_preference("frontend_framework")
            assert retrieved.confidence == 0.7
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_search_similar_projects(self) -> None:
        """测试语义搜索类似项目"""
        db_path = "test_memory_search.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            # 添加项目
            project1 = ProjectRecord(
                id="proj-001",
                name="博客系统",
                idea="创建一个博客系统，支持文章发布和评论",
                tech_stack={"backend": "fastapi", "frontend": "vue3"},
                modules=["文章模块", "评论模块"],
                status="completed",
                quality_score=0.85,
                review_rounds=3,
                token_used=15000,
            )
            project2 = ProjectRecord(
                id="proj-002",
                name="电商平台",
                idea="创建一个电商平台，支持商品展示和购买",
                tech_stack={"backend": "django", "frontend": "react"},
                modules=["商品模块", "订单模块"],
                status="completed",
                quality_score=0.9,
                review_rounds=2,
                token_used=20000,
            )
            memory.save_project(project1)
            memory.save_project(project2)

            # 搜索类似项目（使用完整的项目名称进行匹配）
            similar = memory.search_similar_projects("博客系统")
            assert len(similar) > 0
            # 博客系统应该排在前面
            assert similar[0].id == "proj-001"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_get_relevant_lessons(self) -> None:
        """测试获取相关经验教训"""
        db_path = "test_memory_relevant.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            # 添加经验教训
            for i in range(5):
                lesson = Lesson(
                    id=f"lesson-{i:03d}",
                    project_id="proj-001",
                    agent_name="backend",
                    category="success",
                    lesson=f"经验教训 {i}：使用框架可以提高开发效率",
                )
                memory.save_lesson(lesson)

            # 获取相关经验
            relevant = memory.get_relevant_lessons("框架开发效率", limit=3)
            assert len(relevant) <= 3
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_delete_project(self) -> None:
        """测试删除项目"""
        db_path = "test_memory_delete.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            project = ProjectRecord(
                id="proj-001",
                name="测试项目",
                idea="测试需求",
                tech_stack={},
                modules=[],
                status="completed",
                quality_score=0.8,
                review_rounds=2,
                token_used=10000,
            )
            memory.save_project(project)

            # 删除项目
            memory.delete_project("proj-001")

            # 验证删除
            retrieved = memory.get_project("proj-001")
            assert retrieved is None
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_get_statistics(self) -> None:
        """测试获取统计信息"""
        db_path = "test_memory_stats.db"
        try:
            memory = LongTermMemory(db_path=db_path)

            # 添加测试数据
            for i in range(3):
                project = ProjectRecord(
                    id=f"proj-{i:03d}",
                    name=f"项目 {i}",
                    idea=f"需求 {i}",
                    tech_stack={},
                    modules=[],
                    status="completed",
                    quality_score=0.8,
                    review_rounds=2,
                    token_used=10000,
                )
                memory.save_project(project)

            stats = memory.get_statistics()
            assert stats["total_projects"] == 3
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
            assert stats["total_tokens"] == 30000


class TestLongTermMemoryStateIntegration:
    """长期记忆与状态集成测试"""

    def test_get_long_term_memory_creates_new(self) -> None:
        """测试获取长期记忆时自动创建"""
        state: dict = {"user_idea": "测试"}
        memory = get_long_term_memory(state)
        assert isinstance(memory, LongTermMemory)

    def test_save_and_get_long_term_memory_path(self) -> None:
        """测试保存和获取长期记忆路径"""
        state: dict = {"user_idea": "测试"}
        db_path = "test_ltm_path.db"
        try:
            updated_state = save_long_term_memory_path(state, db_path)
            assert updated_state["long_term_memory_path"] == db_path

            memory = get_long_term_memory(updated_state)
            assert isinstance(memory, LongTermMemory)
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_save_project_to_long_term_memory(self) -> None:
        """测试保存项目到长期记忆"""
        db_path = "test_ltm_project.db"
        state: dict = {"user_idea": "测试"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)
            updated_state = save_project_to_long_term_memory(
                updated_state,
                project_id="proj-001",
                name="测试项目",
                idea="创建一个博客系统",
                tech_stack={"backend": "fastapi"},
                modules=["用户模块"],
                status="completed",
                quality_score=0.85,
                review_rounds=3,
                token_used=15000,
            )

            # 验证保存成功
            memory = get_long_term_memory(updated_state)
            project = memory.get_project("proj-001")
            assert project is not None
            assert project.name == "测试项目"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_save_lesson_to_long_term_memory(self) -> None:
        """测试保存经验教训到长期记忆"""
        db_path = "test_ltm_lesson.db"
        state: dict = {"user_idea": "测试"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)
            updated_state = save_lesson_to_long_term_memory(
                updated_state,
                lesson_id="lesson-001",
                project_id="proj-001",
                agent_name="backend",
                category="success",
                lesson_text="使用 FastAPI 可以快速搭建 REST API",
            )

            # 验证保存成功
            memory = get_long_term_memory(updated_state)
            lessons = memory.get_lessons(project_id="proj-001")
            assert len(lessons) == 1
            assert lessons[0].lesson == "使用 FastAPI 可以快速搭建 REST API"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_save_user_preference_to_long_term_memory(self) -> None:
        """测试保存用户偏好到长期记忆"""
        db_path = "test_ltm_pref.db"
        state: dict = {"user_idea": "测试"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)
            updated_state = save_user_preference_to_long_term_memory(
                updated_state,
                key="frontend_framework",
                value="vue3+element-plus",
                confidence=0.8,
            )

            # 验证保存成功
            memory = get_long_term_memory(updated_state)
            pref = memory.get_user_preference("frontend_framework")
            assert pref is not None
            assert pref.value == "vue3+element-plus"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_search_similar_projects_from_state(self) -> None:
        """测试从状态中搜索类似项目"""
        db_path = "test_ltm_search.db"
        state: dict = {"user_idea": "测试"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)

            # 添加测试项目
            save_project_to_long_term_memory(
                updated_state,
                project_id="proj-001",
                name="博客系统",
                idea="创建一个博客系统，支持文章发布和评论",
                tech_stack={"backend": "fastapi", "frontend": "vue3"},
                modules=["文章模块", "评论模块"],
                status="completed",
                quality_score=0.85,
                review_rounds=3,
                token_used=15000,
            )

            # 搜索类似项目
            similar = search_similar_projects_from_state(updated_state, "博客系统")
            assert len(similar) > 0
            assert similar[0]["id"] == "proj-001"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_get_relevant_lessons_from_state(self) -> None:
        """测试从状态中获取相关经验教训"""
        db_path = "test_ltm_relevant.db"
        state: dict = {"user_idea": "测试"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)

            # 添加经验教训
            save_lesson_to_long_term_memory(
                updated_state,
                lesson_id="lesson-001",
                project_id="proj-001",
                agent_name="backend",
                category="success",
                lesson_text="使用框架可以提高开发效率",
            )

            # 获取相关经验（使用经验教训内容中的关键词进行匹配）
            relevant = get_relevant_lessons_from_state(
                updated_state, "使用框架", limit=3
            )
            assert len(relevant) > 0
            assert relevant[0]["id"] == "lesson-001"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_get_user_preferences_from_state(self) -> None:
        """测试从状态中获取用户偏好"""
        db_path = "test_ltm_prefs.db"
        state: dict = {"user_idea": "测试"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)

            # 添加用户偏好
            save_user_preference_to_long_term_memory(
                updated_state,
                key="frontend_framework",
                value="vue3+element-plus",
                confidence=0.8,
            )

            # 获取用户偏好
            prefs = get_user_preferences_from_state(updated_state)
            assert len(prefs) == 1
            assert prefs[0]["key"] == "frontend_framework"
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_get_long_term_memory_statistics(self) -> None:
        """测试获取长期记忆统计信息"""
        db_path = "test_ltm_stats.db"
        state: dict = {"user_idea": "测试"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)

            # 添加测试数据
            save_project_to_long_term_memory(
                updated_state,
                project_id="proj-001",
                name="项目 1",
                idea="需求 1",
                tech_stack={},
                modules=[],
                status="completed",
                quality_score=0.8,
                review_rounds=2,
                token_used=10000,
            )

            # 获取统计信息
            stats = get_long_term_memory_statistics(updated_state)
            assert stats["total_projects"] == 1
            assert stats["total_tokens"] == 10000
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_get_long_term_memory_context(self) -> None:
        """测试获取长期记忆上下文字符串"""
        db_path = "test_ltm_context.db"
        state: dict = {"user_idea": "创建一个博客系统"}
        try:
            updated_state = save_long_term_memory_path(state, db_path)

            # 添加测试数据
            save_project_to_long_term_memory(
                updated_state,
                project_id="proj-001",
                name="博客系统",
                idea="创建一个博客系统，支持文章发布和评论",
                tech_stack={"backend": "fastapi", "frontend": "vue3"},
                modules=["文章模块", "评论模块"],
                status="completed",
                quality_score=0.85,
                review_rounds=3,
                token_used=15000,
            )

            save_lesson_to_long_term_memory(
                updated_state,
                lesson_id="lesson-001",
                project_id="proj-001",
                agent_name="backend",
                category="success",
                lesson_text="使用 FastAPI 可以快速搭建 REST API",
            )

            # 获取上下文字符串
            context = get_long_term_memory_context(
                updated_state, "创建一个博客系统"
            )
            assert "【长期记忆】" in context
            assert "博客系统" in context
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
