"""工具注册表

单例注册表，支持：
- 链式注册（Builder 模式）
- 按 Agent 权限过滤工具描述
- 运行时查找工具实例
"""

from src.tools.protocol import Tool, ToolDescription


class ToolRegistry:
    """单例工具注册表"""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> "ToolRegistry":
        self._tools[tool.tool_id] = tool
        return self

    def build_descriptions(self, agent_tool_ids: list[str]) -> list[ToolDescription]:
        """为指定 Agent 生成工具描述列表（注入 system prompt）"""
        return [
            self._tools[tid].description
            for tid in agent_tool_ids
            if tid in self._tools
        ]

    def build_openai_tools(self, agent_tool_ids: list[str]) -> list[dict]:
        """生成 OpenAI/DeepSeek 原生 function calling 格式的 tools 参数"""
        result = []
        for tid in agent_tool_ids:
            tool = self._tools.get(tid)
            if tool is None:
                continue
            desc = tool.description
            result.append({
                "type": "function",
                "function": {
                    "name": desc.name,
                    "description": desc.description,
                    "parameters": desc.parameters,
                },
            })
        return result

    def get(self, tool_id: str) -> Tool | None:
        return self._tools.get(tool_id)

    def list_all(self) -> list[str]:
        return list(self._tools.keys())


# 全局单例
tool_registry = ToolRegistry()
