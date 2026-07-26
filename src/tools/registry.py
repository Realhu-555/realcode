"""工具注册表 —— 借鉴 grok-build 的 Builder+Finalize 模式

单例注册表，支持：
- 链式注册（Builder 模式）
- 按 Agent 权限过滤工具描述（对应 FinalizedToolset）
- 运行时查找工具实例
"""

from src.tools.protocol import Tool, ToolDescription


class ToolRegistry:
    """单例工具注册表

    对应 grok-build 的 ToolRegistryBuilder → FinalizedToolset 流程。
    简化版：不需要 finalize 步骤，直接在注册时完成。
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> "ToolRegistry":
        """注册一个工具，返回 self 支持链式调用"""
        self._tools[tool.tool_id] = tool
        return self

    def build_descriptions(self, agent_tool_ids: list[str]) -> list[ToolDescription]:
        """为指定 Agent 生成工具描述列表

        只返回该 Agent 有权限的工具描述 ——
        和 grok-build 的 {%- if tools.by_kind.X %} 条件渲染一个道理：
        Agent 看不到它无权使用的工具。

        Args:
            agent_tool_ids: 该 Agent 允许使用的工具 ID 列表

        Returns:
            工具描述列表（用于注入 system prompt）
        """
        return [
            self._tools[tid].description
            for tid in agent_tool_ids
            if tid in self._tools
        ]

    def get(self, tool_id: str) -> Tool | None:
        """获取工具实例"""
        return self._tools.get(tool_id)

    def list_all(self) -> list[str]:
        """列出所有已注册的工具 ID"""
        return list(self._tools.keys())


# 全局单例
tool_registry = ToolRegistry()
