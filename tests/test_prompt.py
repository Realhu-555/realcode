"""Prompt 系统单元测试 — context.py + renderer.py"""

import pytest
from src.prompt.context import PromptContext
from src.tools.protocol import ToolDescription

# ========================================================================
# PromptContext
# ========================================================================


class TestPromptContext:
    def test_default_creation(self):
        ctx = PromptContext()
        assert ctx.agent_name == ""
        assert ctx.tools == []
        assert ctx.product_name == ""
        assert ctx.strategy is None

    def test_creation_with_product_info(self):
        ctx = PromptContext(
            agent_name="策略专家",
            product_name="Test Product",
            key_selling_points=["fast", "secure"],
            brand_tone="专业",
        )
        assert ctx.product_name == "Test Product"
        assert len(ctx.key_selling_points) == 2
        assert ctx.brand_tone == "专业"

    def test_creation_with_tools(self):
        desc = ToolDescription(name="web_search", description="搜索", parameters={})
        ctx = PromptContext(
            agent_name="策略专家",
            tools=[desc],
        )
        assert len(ctx.tools) == 1

    def test_creation_with_strategy(self):
        ctx = PromptContext(
            agent_name="公众号创作者",
            strategy="## 策略\n\n目标用户画像...",
        )
        assert ctx.strategy is not None
        assert "策略" in ctx.strategy

    def test_creation_with_other_channels(self):
        ctx = PromptContext(
            agent_name="审校官",
            other_channel_contents={
                "公众号": "content1",
                "知乎": "content2",
            },
        )
        assert len(ctx.other_channel_contents) == 2

    def test_current_date_is_today(self):
        from datetime import date

        ctx = PromptContext()
        assert ctx.current_date == date.today().isoformat()

    def test_to_template_vars_includes_all_keys(self):
        ctx = PromptContext(
            agent_name="测试 Agent",
            role_instructions="你是测试助手",
            product_name="Product X",
            product_description="Description",
            target_users="Developers",
            key_selling_points=["fast"],
            brand_tone="极客",
            competitors=["Comp A"],
            strategy="## 策略内容",
            user_preferences="喜欢简洁风格",
        )
        vars_dict = ctx.to_template_vars()

        assert vars_dict["agent_name"] == "测试 Agent"
        assert vars_dict["product"]["name"] == "Product X"
        assert vars_dict["brand"]["tone"] == "极客"
        assert "Comp A" in vars_dict["product"]["competitors"]
        assert vars_dict["strategy"] == "## 策略内容"
        assert vars_dict["preferences"] == "喜欢简洁风格"
        assert "2026" in vars_dict["current_date"]

    def test_to_template_vars_empty_strategy_returns_empty_string(self):
        ctx = PromptContext(strategy=None)
        assert ctx.to_template_vars()["strategy"] == ""

    def test_to_template_vars_empty_other_channels(self):
        ctx = PromptContext(other_channel_contents=None)
        assert ctx.to_template_vars()["other_channels"] == {}

    def test_format_tools_empty(self):
        ctx = PromptContext()
        result = ctx._format_tools()
        assert "无可用工具" in result

    def test_format_tools_with_params(self):
        desc = ToolDescription(
            name="search",
            description="搜索互联网",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "关键词"},
                    "limit": {"type": "integer", "description": "数量"},
                },
                "required": ["query"],
            },
        )
        ctx = PromptContext(tools=[desc])
        formatted = ctx._format_tools()

        assert "search" in formatted
        assert "搜索互联网" in formatted
        assert "query" in formatted
        assert "必填" in formatted  # query 是必填


# ========================================================================
# PromptRenderer
# ========================================================================


class TestPromptRenderer:
    def test_renderer_loads_template(self):
        from src.prompt.renderer import renderer

        template = renderer.load_template("celve.md")
        assert "营销策略专家" in template
        assert "产品信息" in template
        assert "{{ product.name }}" in template

    def test_renderer_loads_all_templates(self):
        from src.prompt.renderer import renderer

        for name in ["celve.md", "gzh.md", "zhihu.md", "xhs.md", "shenjiao.md"]:
            template = renderer.load_template(name)
            assert len(template) > 100, f"{name} 模板太短"

    def test_renderer_caches(self):
        from src.prompt.renderer import renderer

        t1 = renderer.load_template("celve.md")
        t2 = renderer.load_template("celve.md")
        assert t1 is t2  # 同一对象

    def test_renderer_raises_for_missing_template(self):
        from src.prompt.renderer import renderer

        with pytest.raises(FileNotFoundError):
            renderer.load_template("nonexistent.md")

    def test_renderer_renders_with_jinja2(self):
        from src.prompt.renderer import renderer

        result = renderer.render(
            "Hello {{ name }}!",
            {"name": "World"},
        )
        assert result == "Hello World!"

    def test_renderer_renders_template_file(self):
        from src.prompt.renderer import renderer

        ctx = PromptContext(
            agent_name="策略专家",
            product_name="MyProduct",
            product_description="A great product",
            target_users="Devs",
            key_selling_points=["fast", "cheap"],
            brand_tone="专业",
        )
        rendered = renderer.render("celve.md", ctx.to_template_vars())

        assert "MyProduct" in rendered
        assert "fast" in rendered
        assert "cheap" in rendered
        assert "专业" in rendered
        assert "营销策略专家" in rendered

    def test_renderer_renders_shenjiao_template(self):
        from src.prompt.renderer import renderer

        ctx = PromptContext(
            agent_name="审校官",
            product_name="P",
            target_users="U",
            key_selling_points=["s1", "s2"],
            brand_tone="极客",
            other_channel_contents={
                "公众号": "Long article content here",
                "知乎": "Zhihu answer here",
                "小红书": "XHS note here",
            },
        )
        rendered = renderer.render("shenjiao.md", ctx.to_template_vars())

        assert "s1" in rendered
        assert "s2" in rendered
        assert "极客" in rendered
        assert "公众号" in rendered
        assert "Long article content here" in rendered

    def test_renderer_conditional_tools_section(self):
        from src.prompt.renderer import renderer

        # 无工具时显示"无可用工具"
        ctx = PromptContext(tools=[])
        rendered = renderer.render("celve.md", ctx.to_template_vars())
        assert "无可用工具" in rendered

        # 有工具时显示工具描述
        desc = ToolDescription(name="test", description="test tool", parameters={})
        ctx2 = PromptContext(tools=[desc])
        rendered2 = renderer.render("celve.md", ctx2.to_template_vars())
        assert "test" in rendered2

    def test_renderer_renders_inline_content(self):
        from src.prompt.renderer import renderer

        result = renderer.render(
            "Role: {{ role }}\nProduct: {{ product }}",
            {"role": "Writer", "product": "App"},
        )
        assert "Role: Writer" in result
        assert "Product: App" in result
