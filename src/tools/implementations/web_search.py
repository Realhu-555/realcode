"""网络搜索工具 —— 策略 Agent 专用

用于搜索竞品信息、行业趋势、目标用户画像。
当前为模拟实现，P1 阶段接入真实搜索 API。
"""

from src.tools.protocol import Tool, ToolContext, ToolDescription, ToolKind, ToolResult


class WebSearchTool:
    """网络搜索工具"""

    tool_id = "web_search"
    kind = ToolKind.SEARCH
    description = ToolDescription(
        name="web_search",
        description="搜索互联网获取竞品信息、行业趋势和目标用户画像",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询关键词",
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回结果数（默认 5）",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    )

    async def execute(self, ctx: ToolContext, query: str, max_results: int = 5) -> ToolResult:
        """执行搜索（当前为模拟实现）

        P1 阶段接入 DuckDuckGo / SerpAPI / Tavily 等真实搜索 API。
        """
        # TODO: 接入真实搜索 API
        return ToolResult(
            success=True,
            data={
                "query": query,
                "results": [],
                "source": "simulated",
            },
            system_reminder="[搜索功能已在 MVP 中启用模拟模式，返回空结果。请在策略中基于常识进行分析。]",
        )
