"""内容读写工具 —— 渠道 Agent 和审校 Agent 共用

- content_save: 渠道 Agent 保存草稿
- content_read: 审校 Agent 读取指定渠道内容
- content_list: 审校/导出 Agent 列出所有产出
"""

from src.tools.protocol import Tool, ToolContext, ToolDescription, ToolKind, ToolResult


class ContentSaveTool:
    """保存渠道内容"""

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
        """保存内容到项目状态"""
        return ToolResult(
            success=True,
            data={"channel": channel, "content": content},
            system_reminder=f"{channel} 内容已保存到草稿。",
        )


class ContentReadTool:
    """读取指定渠道内容"""

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
        """从项目状态中读取指定渠道内容"""
        state = ctx.project_state
        content = state.get(f"{channel}_content", "")
        return ToolResult(
            success=True,
            data={"channel": channel, "content": str(content)},
        )


class ContentListTool:
    """列出所有产出"""

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
        """列出项目所有产出"""
        state = ctx.project_state
        channels = ["gongzhonghao", "zhihu", "xiaohongshu"]
        items = []
        for ch in channels:
            content = state.get(f"{ch}_content")
            items.append({
                "channel": ch,
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
