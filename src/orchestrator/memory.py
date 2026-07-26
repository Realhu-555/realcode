"""短期记忆管理模块

提供 Agent 间的上下文共享能力，支持：
- 按阶段存储关键决策和上下文
- 按主题检索相关记忆
- 自动压缩旧记忆以控制 token 开销
"""

import time
from enum import Enum
from typing import Any


class MemoryType(str, Enum):
    """记忆类型"""

    DECISION = "decision"  # 关键决策
    CONTEXT = "context"  # 上下文信息
    FEEDBACK = "feedback"  # 用户反馈
    ERROR = "error"  # 错误记录
    CONSTRAINT = "constraint"  # 约束条件


class MemoryEntry:
    """单条记忆条目"""

    def __init__(
        self,
        content: str,
        memory_type: MemoryType,
        source: str,
        stage: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """初始化记忆条目。

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            source: 来源 Agent 名称
            stage: 所属阶段
            metadata: 额外元数据
        """
        self.content = content
        self.memory_type = memory_type
        self.source = source
        self.stage = stage
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.access_count = 0
        self.relevance_score = 1.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "type": self.memory_type.value,
            "source": self.source,
            "stage": self.stage,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """从字典创建记忆条目"""
        entry = cls(
            content=data["content"],
            memory_type=MemoryType(data["type"]),
            source=data["source"],
            stage=data["stage"],
            metadata=data.get("metadata", {}),
        )
        entry.timestamp = data.get("timestamp", time.time())
        entry.access_count = data.get("access_count", 0)
        entry.relevance_score = data.get("relevance_score", 1.0)
        return entry

    def get_token_estimate(self) -> int:
        """估算 token 数量（粗略：中文 2 字/token，英文 4 字符/token）"""
        # 简化处理：按字符数除以 2 估算
        return len(self.content) // 2


class ShortTermMemory:
    """短期记忆管理器

    管理单次任务执行过程中的上下文记忆，支持：
    - 添加记忆
    - 按阶段/类型检索
    - 按相关性排序
    - 自动压缩（控制总 token 开销）
    """

    def __init__(self, max_tokens: int = 4000) -> None:
        """初始化短期记忆管理器。

        Args:
            max_tokens: 最大 token 预算
        """
        self.max_tokens = max_tokens
        self.entries: list[MemoryEntry] = []
        self._current_tokens = 0

    def add(
        self,
        content: str,
        memory_type: MemoryType,
        source: str,
        stage: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """添加一条记忆。

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            source: 来源 Agent
            stage: 所属阶段
            metadata: 额外元数据
        """
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            source=source,
            stage=stage,
            metadata=metadata,
        )

        self.entries.append(entry)
        self._current_tokens += entry.get_token_estimate()

        # 如果超过预算，压缩旧记忆
        if self._current_tokens > self.max_tokens:
            self._compress()

    def retrieve(
        self,
        stage: str | None = None,
        memory_type: MemoryType | None = None,
        source: str | None = None,
        max_tokens: int | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """检索记忆。

        Args:
            stage: 按阶段过滤
            memory_type: 按类型过滤
            source: 按来源过滤
            max_tokens: 最大 token 预算
            limit: 最大返回条数

        Returns:
            匹配的记忆条目列表，按相关性排序
        """
        filtered = self.entries.copy()

        # 按条件过滤
        if stage:
            filtered = [e for e in filtered if e.stage == stage]
        if memory_type:
            filtered = [e for e in filtered if e.memory_type == memory_type]
        if source:
            filtered = [e for e in filtered if e.source == source]

        # 按相关性排序（综合考虑时间、访问次数、相关性分数）
        def sort_key(entry: MemoryEntry) -> float:
            # 时间衰减：越新越重要
            time_factor = 1.0 / (1.0 + (time.time() - entry.timestamp) / 3600)
            # 访问次数加成
            access_factor = 1.0 + entry.access_count * 0.1
            return entry.relevance_score * time_factor * access_factor

        filtered.sort(key=sort_key, reverse=True)

        # 按 token 预算截断
        if max_tokens is None:
            max_tokens = self.max_tokens

        result: list[MemoryEntry] = []
        current_tokens = 0
        for entry in filtered[:limit]:
            entry_tokens = entry.get_token_estimate()
            if current_tokens + entry_tokens <= max_tokens:
                result.append(entry)
                entry.access_count += 1
                current_tokens += entry_tokens
            else:
                break

        return result

    def get_context_string(self, max_tokens: int = 2000) -> str:
        """获取上下文字符串，用于注入到 LLM prompt。

        Args:
            max_tokens: 最大 token 预算

        Returns:
            格式化的上下文字符串
        """
        entries = self.retrieve(max_tokens=max_tokens)
        if not entries:
            return ""

        lines = ["【短期记忆】"]
        for entry in entries:
            type_label = {
                MemoryType.DECISION: "决策",
                MemoryType.CONTEXT: "上下文",
                MemoryType.FEEDBACK: "反馈",
                MemoryType.ERROR: "错误",
                MemoryType.CONSTRAINT: "约束",
            }.get(entry.memory_type, "其他")

            lines.append(f"[{type_label}] ({entry.source}/{entry.stage}): {entry.content}")

        return "\n".join(lines)

    def update_relevance(self, content_substring: str, boost: float = 0.2) -> int:
        """更新匹配记忆的相关性分数。

        Args:
            content_substring: 内容子串匹配
            boost: 相关性提升值

        Returns:
            更新的条目数量
        """
        count = 0
        for entry in self.entries:
            if content_substring in entry.content:
                entry.relevance_score = min(2.0, entry.relevance_score + boost)
                count += 1
        return count

    def clear(self) -> None:
        """清空所有记忆"""
        self.entries.clear()
        self._current_tokens = 0

    def _compress(self) -> None:
        """压缩旧记忆，控制 token 开销。

        策略：
        1. 优先删除低相关性、旧的记忆
        2. 保留最近的记忆
        3. 保留高访问次数的记忆
        """
        if not self.entries:
            return

        # 按综合分数排序（分数低的优先删除）
        def score(entry: MemoryEntry) -> float:
            time_factor = 1.0 / (1.0 + (time.time() - entry.timestamp) / 3600)
            access_factor = 1.0 + entry.access_count * 0.1
            return entry.relevance_score * time_factor * access_factor

        self.entries.sort(key=score)

        # 删除一半的低分记忆，直到 token 开销在预算内
        while self._current_tokens > self.max_tokens * 0.8 and len(self.entries) > 1:
            removed = self.entries.pop(0)
            self._current_tokens -= removed.get_token_estimate()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式（用于持久化）"""
        return {
            "max_tokens": self.max_tokens,
            "entries": [e.to_dict() for e in self.entries],
            "_current_tokens": self._current_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShortTermMemory":
        """从字典创建记忆管理器"""
        memory = cls(max_tokens=data.get("max_tokens", 4000))
        memory.entries = [MemoryEntry.from_dict(e) for e in data.get("entries", [])]
        memory._current_tokens = data.get("_current_tokens", 0)
        return memory
