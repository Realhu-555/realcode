"""短期记忆模块单元测试"""

import pytest

from src.orchestrator.memory import MemoryEntry, MemoryType, ShortTermMemory
from src.orchestrator.state import (
    add_memory,
    get_memory,
    get_memory_context,
    retrieve_memory,
    save_memory,
    update_memory_relevance,
)


class TestMemoryEntry:
    """MemoryEntry 测试"""

    def test_create_entry(self) -> None:
        """测试创建记忆条目"""
        entry = MemoryEntry(
            content="使用 React 框架",
            memory_type=MemoryType.DECISION,
            source="architect",
            stage="architecture",
        )
        assert entry.content == "使用 React 框架"
        assert entry.memory_type == MemoryType.DECISION
        assert entry.source == "architect"
        assert entry.stage == "architecture"
        assert entry.access_count == 0
        assert entry.relevance_score == 1.0

    def test_to_dict(self) -> None:
        """测试转换为字典"""
        entry = MemoryEntry(
            content="使用 React 框架",
            memory_type=MemoryType.DECISION,
            source="architect",
            stage="architecture",
            metadata={"framework": "React"},
        )
        d = entry.to_dict()
        assert d["content"] == "使用 React 框架"
        assert d["type"] == "decision"
        assert d["source"] == "architect"
        assert d["metadata"]["framework"] == "React"

    def test_from_dict(self) -> None:
        """测试从字典创建"""
        d = {
            "content": "使用 React 框架",
            "type": "decision",
            "source": "architect",
            "stage": "architecture",
            "metadata": {"framework": "React"},
            "timestamp": 1000.0,
            "access_count": 3,
            "relevance_score": 1.5,
        }
        entry = MemoryEntry.from_dict(d)
        assert entry.content == "使用 React 框架"
        assert entry.access_count == 3
        assert entry.relevance_score == 1.5

    def test_token_estimate(self) -> None:
        """测试 token 估算"""
        entry = MemoryEntry(
            content="这是一个测试内容" * 10,  # 70 字符
            memory_type=MemoryType.CONTEXT,
            source="tester",
            stage="testing",
        )
        # 约 35 tokens
        tokens = entry.get_token_estimate()
        assert 30 <= tokens <= 40


class TestShortTermMemory:
    """ShortTermMemory 测试"""

    def test_add_and_retrieve(self) -> None:
        """测试添加和检索记忆"""
        memory = ShortTermMemory(max_tokens=1000)
        memory.add(
            content="使用 React 框架",
            memory_type=MemoryType.DECISION,
            source="architect",
            stage="architecture",
        )
        memory.add(
            content="用户需要登录功能",
            memory_type=MemoryType.CONTEXT,
            source="requirement",
            stage="requirement",
        )

        entries = memory.retrieve()
        assert len(entries) == 2

    def test_retrieve_by_stage(self) -> None:
        """测试按阶段检索"""
        memory = ShortTermMemory()
        memory.add("决策1", MemoryType.DECISION, "architect", "architecture")
        memory.add("上下文1", MemoryType.CONTEXT, "requirement", "requirement")
        memory.add("决策2", MemoryType.DECISION, "backend", "backend")

        entries = memory.retrieve(stage="architecture")
        assert len(entries) == 1
        assert entries[0].content == "决策1"

    def test_retrieve_by_type(self) -> None:
        """测试按类型检索"""
        memory = ShortTermMemory()
        memory.add("决策1", MemoryType.DECISION, "architect", "architecture")
        memory.add("反馈1", MemoryType.FEEDBACK, "user", "requirement")

        entries = memory.retrieve(memory_type=MemoryType.DECISION)
        assert len(entries) == 1
        assert entries[0].content == "决策1"

    def test_retrieve_with_token_limit(self) -> None:
        """测试 token 预算限制"""
        memory = ShortTermMemory()
        # 添加大量内容
        for i in range(20):
            memory.add(
                content=f"记忆内容 {i}" * 50,  # 每条约 250 tokens
                memory_type=MemoryType.CONTEXT,
                source="tester",
                stage="testing",
            )

        # 限制 token 预算
        entries = memory.retrieve(max_tokens=500)
        total_tokens = sum(e.get_token_estimate() for e in entries)
        assert total_tokens <= 500

    def test_compress(self) -> None:
        """测试记忆压缩"""
        memory = ShortTermMemory(max_tokens=200)
        # 添加超过预算的内容
        for i in range(10):
            memory.add(
                content=f"记忆内容 {i}" * 30,
                memory_type=MemoryType.CONTEXT,
                source="tester",
                stage="testing",
            )

        # 应该已经自动压缩
        assert memory._current_tokens <= memory.max_tokens

    def test_clear(self) -> None:
        """测试清空记忆"""
        memory = ShortTermMemory()
        memory.add("内容1", MemoryType.CONTEXT, "tester", "testing")
        memory.add("内容2", MemoryType.CONTEXT, "tester", "testing")

        memory.clear()
        assert len(memory.entries) == 0
        assert memory._current_tokens == 0

    def test_get_context_string(self) -> None:
        """测试获取上下文字符串"""
        memory = ShortTermMemory()
        memory.add("使用 React", MemoryType.DECISION, "architect", "architecture")
        memory.add("用户反馈：需要暗色主题", MemoryType.FEEDBACK, "user", "frontend")

        context = memory.get_context_string()
        assert "【短期记忆】" in context
        assert "使用 React" in context
        assert "暗色主题" in context

    def test_update_relevance(self) -> None:
        """测试更新相关性"""
        memory = ShortTermMemory()
        memory.add("React 框架", MemoryType.DECISION, "architect", "architecture")
        memory.add("Vue 框架", MemoryType.DECISION, "architect", "architecture")

        count = memory.update_relevance("React", 0.5)
        assert count == 1
        assert memory.entries[0].relevance_score == 1.5
        assert memory.entries[1].relevance_score == 1.0

    def test_serialization(self) -> None:
        """测试序列化和反序列化"""
        memory = ShortTermMemory(max_tokens=2000)
        memory.add("内容1", MemoryType.DECISION, "architect", "architecture")
        memory.add("内容2", MemoryType.CONTEXT, "backend", "backend")

        d = memory.to_dict()
        restored = ShortTermMemory.from_dict(d)

        assert restored.max_tokens == 2000
        assert len(restored.entries) == 2
        assert restored.entries[0].content == "内容1"


class TestStateMemoryHelpers:
    """状态中记忆辅助函数测试"""

    def test_get_memory_creates_new(self) -> None:
        """测试获取记忆时自动创建"""
        state = {"user_idea": "测试"}
        memory = get_memory(state)
        assert isinstance(memory, ShortTermMemory)
        assert len(memory.entries) == 0

    def test_save_and_get_memory(self) -> None:
        """测试保存和获取记忆"""
        state = {"user_idea": "测试"}
        memory = ShortTermMemory()
        memory.add("测试内容", MemoryType.CONTEXT, "tester", "testing")

        updated_state = save_memory(state, memory)
        restored = get_memory(updated_state)
        assert len(restored.entries) == 1
        assert restored.entries[0].content == "测试内容"

    def test_add_memory_helper(self) -> None:
        """测试添加记忆辅助函数"""
        state = {"user_idea": "测试"}
        updated = add_memory(
            state,
            content="使用 Python",
            memory_type=MemoryType.DECISION,
            source="architect",
            stage="architecture",
        )
        memory = get_memory(updated)
        assert len(memory.entries) == 1

    def test_retrieve_memory_helper(self) -> None:
        """测试检索记忆辅助函数"""
        state = {"user_idea": "测试"}
        state = add_memory(state, "内容1", MemoryType.DECISION, "architect", "architecture")
        state = add_memory(state, "内容2", MemoryType.CONTEXT, "backend", "backend")

        entries = retrieve_memory(state, stage="architecture")
        assert len(entries) == 1
        assert entries[0]["content"] == "内容1"

    def test_get_memory_context_helper(self) -> None:
        """测试获取记忆上下文辅助函数"""
        state = {"user_idea": "测试"}
        state = add_memory(state, "使用 React", MemoryType.DECISION, "architect", "architecture")

        context = get_memory_context(state)
        assert "使用 React" in context

    def test_update_memory_relevance_helper(self) -> None:
        """测试更新记忆相关性辅助函数"""
        state = {"user_idea": "测试"}
        state = add_memory(state, "React 框架", MemoryType.DECISION, "architect", "architecture")

        updated = update_memory_relevance(state, "React", 0.3)
        memory = get_memory(updated)
        assert memory.entries[0].relevance_score == 1.3
