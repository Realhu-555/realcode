"""网络搜索工具 — Tavily 真实搜索

策略 Agent 专用，用于搜索竞品信息、行业趋势、目标用户画像。
"""

import os

from src.tools.protocol import ToolContext, ToolDescription, ToolKind, ToolResult


class WebSearchTool:
    """Tavily 网络搜索"""

    tool_id = "web_search"
    kind = ToolKind.SEARCH
    description = ToolDescription(
        name="web_search",
        description="搜索互联网获取竞品信息、行业趋势和目标用户画像。返回结果的标题、URL 和摘要。",
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

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from tavily import TavilyClient

            self._client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
        return self._client

    async def execute(self, ctx: ToolContext, query: str, max_results: int = 5) -> ToolResult:
        try:
            response = self.client.search(
                query=query,
                max_results=min(max_results, 10),
                search_depth="basic",
                include_raw_content=False,
            )
            results = response.get("results", [])

            # 精简为 Agent 可读格式
            formatted = []
            for r in results[:max_results]:
                formatted.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                })

            return ToolResult(
                success=True,
                data={"query": query, "results": formatted},
                system_reminder=f"搜索完成，返回 {len(formatted)} 条结果。请将搜索结果融入策略分析，不要直接复制粘贴。",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"搜索失败: {str(e)}",
                system_reminder="搜索暂时不可用，请基于已有知识进行分析。",
            )
