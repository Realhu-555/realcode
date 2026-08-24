"""工具系统单元测试 — protocol.py + registry.py"""

from src.tools.protocol import ToolContext, ToolDescription, ToolKind, ToolResult

# ========================================================================
# ToolDescription
# ========================================================================


class TestToolDescription:
    def test_creation(self):
        desc = ToolDescription(
            name="web_search",
            description="搜索互联网",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                "required": ["query"],
            },
        )
        assert desc.name == "web_search"
        assert desc.description == "搜索互联网"
        assert "query" in desc.parameters["properties"]

    def test_empty_parameters(self):
        desc = ToolDescription(name="ping", description="检查服务状态", parameters={})
        assert desc.parameters == {}


# ========================================================================
# ToolContext
# ========================================================================


class TestToolContext:
    def test_creation_with_defaults(self):
        ctx = ToolContext(session_id="s1", working_dir="/tmp/test")
        assert ctx.session_id == "s1"
        assert ctx.working_dir == "/tmp/test"
        assert ctx.project_state == {}
        assert ctx.brand_profile is None

    def test_creation_with_project_state(self):
        ctx = ToolContext(
            session_id="s1",
            working_dir="/tmp",
            project_state={"product_name": "Test"},
        )
        assert ctx.project_state["product_name"] == "Test"


# ========================================================================
# ToolResult
# ========================================================================


class TestToolResult:
    def test_success_result(self):
        r = ToolResult(success=True, data={"results": [1, 2, 3]})
        assert r.success is True
        assert len(r.data["results"]) == 3
        assert r.error is None
        assert r.system_reminder is None

    def test_error_result(self):
        r = ToolResult(success=False, data=None, error="网络超时")
        assert r.success is False
        assert r.error == "网络超时"

    def test_result_with_reminder(self):
        r = ToolResult(
            success=True,
            data={"content": "hello"},
            system_reminder="内容已保存到草稿。",
        )
        assert r.system_reminder is not None


# ========================================================================
# ToolRegistry
# ========================================================================


class TestToolRegistry:
    def test_register_and_get(self):
        from src.tools.registry import ToolRegistry

        registry = ToolRegistry()

        class FakeTool:
            tool_id = "test_tool"
            kind = ToolKind.SEARCH
            description = ToolDescription(
                name="test_tool",
                description="测试工具",
                parameters={},
            )

            async def execute(self, ctx, **kwargs):
                return ToolResult(success=True, data="ok")

        registry.register(FakeTool())
        tool = registry.get("test_tool")
        assert tool is not None
        assert tool.tool_id == "test_tool"

    def test_get_missing_returns_none(self):
        from src.tools.registry import ToolRegistry

        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_build_descriptions_filters_by_agent(self):
        from src.tools.registry import ToolRegistry

        registry = ToolRegistry()

        class ToolA:
            tool_id = "tool_a"
            kind = ToolKind.SEARCH
            description = ToolDescription(name="tool_a", description="A 工具", parameters={})

            async def execute(self, ctx, **kwargs):
                return ToolResult(success=True, data="a")

        class ToolB:
            tool_id = "tool_b"
            kind = ToolKind.WRITE
            description = ToolDescription(name="tool_b", description="B 工具", parameters={})

            async def execute(self, ctx, **kwargs):
                return ToolResult(success=True, data="b")

        registry.register(ToolA()).register(ToolB())

        # 策略 Agent 只有 tool_a 权限
        descs = registry.build_descriptions(["tool_a"])
        assert len(descs) == 1
        assert descs[0].name == "tool_a"

        # 渠道 Agent 两个都有
        descs = registry.build_descriptions(["tool_a", "tool_b"])
        assert len(descs) == 2

        # 空权限列表
        descs = registry.build_descriptions([])
        assert len(descs) == 0

    def test_build_descriptions_skips_unknown(self):
        from src.tools.registry import ToolRegistry

        registry = ToolRegistry()
        # 请求不存在工具 ID 不报错
        descs = registry.build_descriptions(["ghost_tool"])
        assert descs == []

    def test_list_all(self):
        from src.tools.registry import ToolRegistry

        registry = ToolRegistry()

        class FakeTool:
            tool_id = "my_tool"
            kind = ToolKind.READ
            description = ToolDescription(name="my_tool", description="x", parameters={})

            async def execute(self, ctx, **kwargs):
                return ToolResult(success=True, data="ok")

        registry.register(FakeTool())
        assert "my_tool" in registry.list_all()
