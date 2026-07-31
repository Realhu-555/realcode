"""工具系统启动注册"""

from src.tools.registry import tool_registry
from src.tools.implementations.web_search import WebSearchTool
from src.tools.implementations.content_io import (
    ContentSaveTool,
    ContentReadTool,
    ContentListTool,
)
from src.tools.implementations.database import (
    BrandLookupTool,
    ProjectSaveTool,
    ProjectLoadTool,
)

tool_registry \
    .register(WebSearchTool()) \
    .register(ContentSaveTool()) \
    .register(ContentReadTool()) \
    .register(ContentListTool()) \
    .register(BrandLookupTool()) \
    .register(ProjectSaveTool()) \
    .register(ProjectLoadTool())
