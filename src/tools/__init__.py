"""工具系统启动注册"""

from src.tools.registry import tool_registry
from src.tools.implementations.web_search import WebSearchTool
from src.tools.implementations.content_io import (
    ContentSaveTool,
    ContentReadTool,
    ContentListTool,
)

tool_registry \
    .register(WebSearchTool()) \
    .register(ContentSaveTool()) \
    .register(ContentReadTool()) \
    .register(ContentListTool())
