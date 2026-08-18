"""工具系统启动注册"""

from src.tools.implementations.data_inspect import DataInspectTool
from src.tools.registry import tool_registry

tool_registry.register(DataInspectTool())
