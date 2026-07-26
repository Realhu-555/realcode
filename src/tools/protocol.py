"""工具协议定义 —— 借鉴 grok-build 的 Tool trait 双接口设计

核心设计理念：
- 执行和描述分离：ToolDescription（给 AI 看）和 Tool.execute()（实际逻辑）独立
- ToolContext 统一注入：所有工具通过同一个上下文对象获取运行时资源
- system_reminder 后处理：工具执行后可向对话注入提醒
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ToolKind(Enum):
    """工具分类 —— 对应 grok-build 的 ToolKind"""
    SEARCH = "search"   # 搜索类（网络搜索、知识库查询）
    READ = "read"       # 读取类（读取内容、文件）
    WRITE = "write"     # 写入类（保存、导出）


@dataclass
class ToolDescription:
    """给 AI 看的工具说明 —— 和执行逻辑完全分离

    对应 grok-build 中 ToolMetadata trait 的作用：
    这段描述会被注入到 Agent 的 system prompt 中，
    Agent 只能看到它有权限使用的工具描述。
    """
    name: str                          # "web_search"
    description: str                   # "搜索互联网获取竞品信息和行业趋势"
    parameters: dict[str, Any]         # JSON Schema 格式的参数定义


@dataclass
class ToolContext:
    """工具执行上下文 —— 统一注入所有运行时资源

    对应 grok-build 的 ToolCallContext：
    所有工具通过同一个上下文对象获取资源，
    不各自 import config / get_db / read_file。
    """
    session_id: str
    working_dir: str
    project_state: dict[str, Any] = field(default_factory=dict)
    brand_profile: dict[str, Any] | None = None


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    error: str | None = None
    system_reminder: str | None = None


@runtime_checkable
class Tool(Protocol):
    """所有工具的接口协议

    对应 grok-build 的 Tool trait：
    - execute() — 执行逻辑
    - description 属性 — 给 AI 看的能力声明
    """

    tool_id: str
    kind: ToolKind
    description: ToolDescription

    async def execute(self, ctx: ToolContext, **kwargs: Any) -> ToolResult:
        """执行工具操作

        Args:
            ctx: 统一的工具执行上下文
            **kwargs: 工具特定参数（与 description.parameters 对应）

        Returns:
            ToolResult: 执行结果，可携带 system_reminder
        """
        ...
