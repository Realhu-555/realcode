"""内容读写工具

key 约定（与 ContentProjectState 一致）：
  - gzh_content:   公众号
  - zhihu_content: 知乎
  - xhs_content:   小红书
  - review_report: 审校报告

channel 参数对应关系：
  - "gongzhonghao" → gzh_content
  - "zhihu"         → zhihu_content
  - "xiaohongshu"   → xhs_content
"""

from src.tools.protocol import ToolContext, ToolDescription, ToolKind, ToolResult

# channel → state key 映射
_CHANNEL_KEY = {
    "gongzhonghao": "gzh_content",
    "zhihu": "zhihu_content",
    "xiaohongshu": "xhs_content",
}


class ContentSaveTool:
    """保存渠道内容 — 用于渠道 Agent 持久化产出"""

    tool_id = "content_save"
    kind = ToolKind.WRITE
    description = ToolDescription(
        name="content_save",
        description="将生成的内容保存到项目草稿中",
        parameters={
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "enum": ["gongzhonghao", "zhihu", "xiaohongshu"],
                    "description": "渠道标识",
                },
                "content": {
                    "type": "string",
                    "description": "要保存的完整内容（Markdown 格式）",
                },
            },
            "required": ["channel", "content"],
        },
    )

    async def execute(self, ctx: ToolContext, channel: str, content: str) -> ToolResult:
        key = _CHANNEL_KEY[channel]
        # 实际写入 project_state（由 orchestrator 管理生命周期）
        ctx.project_state[key] = content
        return ToolResult(
            success=True,
            data={"channel": channel, "saved_len": len(content)},
        )


class ContentReadTool:
    """读取指定渠道内容 — 审校 Agent 用"""

    tool_id = "content_read"
    kind = ToolKind.READ
    description = ToolDescription(
        name="content_read",
        description="读取指定渠道的已生成内容",
        parameters={
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "enum": ["gongzhonghao", "zhihu", "xiaohongshu"],
                    "description": "要读取的渠道标识",
                },
            },
            "required": ["channel"],
        },
    )

    async def execute(self, ctx: ToolContext, channel: str) -> ToolResult:
        key = _CHANNEL_KEY[channel]
        content = ctx.project_state.get(key, "")
        return ToolResult(
            success=True,
            data={
                "channel": channel,
                "content": str(content),
                "length": len(str(content)),
            },
        )


class ContentListTool:
    """列出所有产出 — 导出 Agent 用"""

    tool_id = "content_list"
    kind = ToolKind.READ
    description = ToolDescription(
        name="content_list",
        description="列出当前项目的所有内容产出（各渠道 + 审校报告）",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )

    async def execute(self, ctx: ToolContext) -> ToolResult:
        state = ctx.project_state
        items = []
        for channel, key in _CHANNEL_KEY.items():
            content = state.get(key)
            items.append({
                "channel": channel,
                "has_content": bool(content),
                "length": len(str(content)) if content else 0,
            })
        review = state.get("review_report")
        items.append({
            "channel": "review",
            "has_content": bool(review),
            "length": len(str(review)) if review else 0,
        })
        return ToolResult(success=True, data={"items": items})
