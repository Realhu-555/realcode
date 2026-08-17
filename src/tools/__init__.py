"""工具系统启动注册"""

from src.tools.implementations.content_io import (
    ContentListTool,
    ContentReadTool,
    ContentSaveTool,
)
from src.tools.implementations.data_inspect import DataInspectTool
from src.tools.implementations.database import (
    BrandLookupTool,
    ProjectLoadTool,
    ProjectSaveTool,
)
from src.tools.implementations.web_search import WebSearchTool
from src.tools.registry import tool_registry

tool_registry \
    .register(WebSearchTool()) \
    .register(ContentSaveTool()) \
    .register(ContentReadTool()) \
    .register(ContentListTool()) \
    .register(BrandLookupTool()) \
    .register(ProjectSaveTool()) \
    .register(ProjectLoadTool()) \
    .register(DataInspectTool())
