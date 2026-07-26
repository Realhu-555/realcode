"""工具系统 - ReAct Agent 的工具注册与执行"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """工具执行结果"""

    success: bool
    output: str
    error: str | None = None


class BaseTool(ABC):
    """工具基类，所有工具必须继承此类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（给 LLM 看的）"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """参数 schema（JSON Schema 格式）"""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """执行工具，返回结果字符串"""
        pass


class ToolRegistry:
    """工具注册表，管理所有可用工具"""

    def __init__(self) -> None:
        self.tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有已注册工具名称"""
        return list(self.tools.keys())

    def get_tool_descriptions(self) -> str:
        """获取所有工具的描述，用于注入到 LLM prompt"""
        descriptions = []
        for tool in self.tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(descriptions)


# ========================================================================
# 内置工具实现
# ========================================================================


class FileReadTool(BaseTool):
    """文件读取工具"""

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "读取项目目录内的文件内容"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目根目录）"}
            },
            "required": ["path"],
        }

    def execute(self, **kwargs: Any) -> str:
        path = kwargs.get("path", "")
        # MVP 阶段：实际实现需要沙箱支持
        return f"[FileRead] 读取文件: {path}"


class FileWriteTool(BaseTool):
    """文件写入工具"""

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "在项目目录内创建或覆盖文件"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"},
            },
            "required": ["path", "content"],
        }

    def execute(self, **kwargs: Any) -> str:
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        return f"[FileWrite] 写入文件 {path}，长度 {len(content)} 字符"


class TerminalTool(BaseTool):
    """终端命令执行工具"""

    @property
    def name(self) -> str:
        return "terminal"

    @property
    def description(self) -> str:
        return "在沙箱中执行终端命令（仅允许 python/pip/node/npm）"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "要执行的命令"},
            },
            "required": ["cmd"],
        }

    def execute(self, **kwargs: Any) -> str:
        cmd = kwargs.get("cmd", "")
        return f"[Terminal] 执行命令: {cmd}"


def create_default_tools() -> list[BaseTool]:
    """创建默认工具集"""
    return [FileReadTool(), FileWriteTool(), TerminalTool()]
