"""数据库工具 — 品牌档案 + 内容项目持久化

- brand_lookup: 查找品牌档案（策略/审校 Agent 用）
- project_save: 保存内容项目到 SQLite（导出 Agent 用）
- project_load: 从 SQLite 恢复项目（导出 Agent 用）
"""

import os
from datetime import datetime

from src.tools.protocol import ToolContext, ToolDescription, ToolKind, ToolResult
from src.orchestrator.long_term_memory import LongTermMemory


class BrandLookupTool:
    """查找已有品牌档案 — 策略 Agent 用"""

    tool_id = "brand_lookup"
    kind = ToolKind.READ
    description = ToolDescription(
        name="brand_lookup",
        description="根据产品名称查找已有的品牌档案（调性、目标用户、卖点），用于复用历史策略",
        parameters={
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "产品名称，用于模糊匹配已有品牌档案",
                },
            },
            "required": ["product_name"],
        },
    )

    def __init__(self):
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "data", "memory.db"
        )
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = LongTermMemory()
        return self._db

    async def execute(self, ctx: ToolContext, product_name: str) -> ToolResult:
        try:
            profiles = self.db.search_brand_profiles(product_name) if hasattr(self.db, "search_brand_profiles") else []
            if not profiles:
                ctx_dict = self.db.get_brand_profile_context(ctx.session_id) if hasattr(self.db, "get_brand_profile_context") else {}
                if ctx_dict:
                    profiles = [ctx_dict]

            if profiles:
                return ToolResult(
                    success=True,
                    data={"profiles": profiles, "count": len(profiles)},
                )
            return ToolResult(
                success=True,
                data={"profiles": [], "count": 0},
                system_reminder="未找到已有品牌档案。可以基于用户当前输入建立新档案。",
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"查询失败: {e}")


class ProjectSaveTool:
    """保存内容项目到 SQLite"""

    tool_id = "project_save"
    kind = ToolKind.WRITE
    description = ToolDescription(
        name="project_save",
        description="将当前项目的完整内容（策略 + 三渠道 + 审校报告）持久化到数据库，不会因服务重启丢失",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )

    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = LongTermMemory()
        return self._db

    async def execute(self, ctx: ToolContext) -> ToolResult:
        try:
            state = ctx.project_state
            self.db.save_content_project({
                "id": ctx.session_id,
                "product_name": state.get("product_name", ""),
                "product_description": state.get("product_description", ""),
                "strategy": state.get("strategy", ""),
                "gzh_content": state.get("gzh_content", ""),
                "zhihu_content": state.get("zhihu_content", ""),
                "xhs_content": state.get("xhs_content", ""),
                "review_report": state.get("review_report", ""),
                "status": state.get("current_stage", "done"),
                "updated_at": datetime.now().isoformat(),
            })
            return ToolResult(
                success=True,
                data={"saved": True},
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"保存失败: {e}")


class ProjectLoadTool:
    """从 SQLite 加载项目"""

    tool_id = "project_load"
    kind = ToolKind.READ
    description = ToolDescription(
        name="project_load",
        description="从数据库加载历史项目，用于查看或复现之前的内容",
        parameters={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "项目 ID",
                },
            },
            "required": ["project_id"],
        },
    )

    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = LongTermMemory()
        return self._db

    async def execute(self, ctx: ToolContext, project_id: str) -> ToolResult:
        try:
            project = self.db.get_content_project(project_id)
            if project:
                return ToolResult(success=True, data=project)
            return ToolResult(
                success=True,
                data=None,
                system_reminder=f"未找到项目 {project_id}。",
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"加载失败: {e}")
