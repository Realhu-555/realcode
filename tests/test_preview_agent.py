"""PreviewAgent 单元测试"""

from src.agents.preview import (
    COMPONENT_TEMPLATES,
    PAGE_TYPE_MAPPING,
    PreviewAgent,
    _generate_javascript,
    _get_page_type,
    _render_card,
    _render_chart,
    _render_component,
    _render_form,
    _render_modal,
    _render_navigation,
    _render_page_content,
    _render_pagination,
    _render_table,
    _render_tabs,
)

# ========================================================================
# 辅助函数测试
# ========================================================================


class TestGetPageType:
    """_get_page_type 页面类型识别测试"""

    def test_recognizes_login_page(self) -> None:
        assert _get_page_type("用户登录") == "登录"

    def test_recognizes_register_page(self) -> None:
        assert _get_page_type("注册页面") == "注册"

    def test_recognizes_list_page(self) -> None:
        assert _get_page_type("文章列表") == "列表"

    def test_recognizes_detail_page(self) -> None:
        assert _get_page_type("订单详情") == "详情"

    def test_recognizes_dashboard(self) -> None:
        assert _get_page_type("数据仪表盘") == "仪表盘"

    def test_recognizes_settings(self) -> None:
        assert _get_page_type("系统设置") == "设置"

    def test_recognizes_management(self) -> None:
        assert _get_page_type("用户管理") == "管理"

    def test_returns_default_for_unknown(self) -> None:
        assert _get_page_type("关于我们的页面") == "默认"


class TestRenderTable:
    """_render_table 表格渲染测试"""

    def test_contains_table_tag(self) -> None:
        html = _render_table()
        assert "<table>" in html
        assert "</table>" in html

    def test_contains_mock_data(self) -> None:
        html = _render_table()
        assert "示例数据1" in html
        assert "示例数据2" in html

    def test_has_thead_and_tbody(self) -> None:
        html = _render_table()
        assert "<thead>" in html
        assert "<tbody>" in html


class TestRenderForm:
    """_render_form 表单渲染测试"""

    def test_contains_form_tag(self) -> None:
        html = _render_form()
        assert "<form" in html
        assert "</form>" in html

    def test_contains_input_fields(self) -> None:
        html = _render_form()
        assert '<input type="text"' in html

    def test_contains_submit_button(self) -> None:
        html = _render_form()
        assert "提交" in html


class TestRenderCard:
    """_render_card 卡片渲染测试"""

    def test_contains_card_class(self) -> None:
        html = _render_card()
        assert 'class="card"' in html

    def test_uses_provided_title(self) -> None:
        html = _render_card(title="测试标题")
        assert "测试标题" in html

    def test_uses_provided_content(self) -> None:
        html = _render_card(content="测试内容")
        assert "测试内容" in html

    def test_uses_defaults(self) -> None:
        html = _render_card()
        assert "卡片标题" in html
        assert "卡片内容" in html


class TestRenderChart:
    """_render_chart 图表渲染测试"""

    def test_contains_chart_placeholder(self) -> None:
        html = _render_chart()
        assert "chart-placeholder" in html
        assert "图表区域" in html


class TestRenderModal:
    """_render_modal 弹窗渲染测试"""

    def test_contains_modal_class(self) -> None:
        html = _render_modal()
        assert "modal" in html

    def test_is_hidden_by_default(self) -> None:
        html = _render_modal()
        assert "display:none" in html


class TestRenderTabs:
    """_render_tabs 标签页渲染测试"""

    def test_contains_tabs_class(self) -> None:
        html = _render_tabs()
        assert 'class="tabs"' in html

    def test_has_tab_buttons(self) -> None:
        html = _render_tabs()
        assert "标签1" in html
        assert "标签2" in html


class TestRenderPagination:
    """_render_pagination 分页渲染测试"""

    def test_contains_pagination_class(self) -> None:
        html = _render_pagination()
        assert "pagination" in html

    def test_has_navigation_buttons(self) -> None:
        html = _render_pagination()
        assert "上一页" in html
        assert "下一页" in html


class TestRenderComponent:
    """_render_component 组件分发测试"""

    def test_renders_known_component(self) -> None:
        html = _render_component("table")
        assert "<table>" in html

    def test_renders_unknown_component(self) -> None:
        html = _render_component("unknown_widget")
        assert "未知组件" in html
        assert "unknown_widget" in html

    def test_renders_topbar_with_title(self) -> None:
        html = _render_component("topbar", page_title="我的页面")
        assert "我的页面" in html


class TestRenderNavigation:
    """_render_navigation 导航渲染测试"""

    def test_returns_empty_for_no_pages(self) -> None:
        html = _render_navigation([])
        assert html == ""

    def test_renders_sidebar_with_pages(self) -> None:
        pages = [{"name": "首页"}, {"name": "列表"}, {"name": "设置"}]
        html = _render_navigation(pages)
        assert "首页" in html
        assert "列表" in html
        assert "设置" in html

    def test_first_item_is_active(self) -> None:
        pages = [{"name": "首页"}, {"name": "列表"}]
        html = _render_navigation(pages)
        assert "nav-item active" in html

    def test_non_first_items_are_not_active(self) -> None:
        pages = [{"name": "首页"}, {"name": "列表"}]
        html = _render_navigation(pages)
        lines = html.split("\n")
        # 找到第二个 li 元素，它不应该有 active
        second_li = [line for line in lines if "列表" in line][0]
        assert "nav-item active" not in second_li

    def test_generates_show_page_function(self) -> None:
        pages = [{"name": "首页"}, {"name": "列表"}]
        html = _render_navigation(pages)
        assert "showPage('page-0')" in html
        assert "showPage('page-1')" in html


class TestRenderPageContent:
    """_render_page_content 页面内容渲染测试"""

    def test_creates_page_section(self) -> None:
        page = {"name": "登录页"}
        html = _render_page_content(page, 0)
        assert 'class="page-section active"' in html
        assert 'id="page-0"' in html

    def test_non_first_page_is_not_active(self) -> None:
        page = {"name": "列表页"}
        html = _render_page_content(page, 1)
        assert 'class="page-section"' in html
        assert "active" not in html.split('class="page-section"')[1].split('"')[0]

    def test_uses_correct_components_for_list_page(self) -> None:
        page = {"name": "文章列表页"}
        html = _render_page_content(page, 0)
        assert "topbar" in html
        assert "data-table" in html
        assert "pagination" in html

    def test_uses_correct_components_for_form_page(self) -> None:
        page = {"name": "用户登录"}
        html = _render_page_content(page, 0)
        assert "data-form" in html


class TestGenerateJavascript:
    """_generate_javascript JS 生成测试"""

    def test_returns_empty_for_single_page(self) -> None:
        js = _generate_javascript(1)
        assert js == ""

    def test_returns_js_for_multiple_pages(self) -> None:
        js = _generate_javascript(3)
        assert "showPage" in js
        assert "<script>" in js
        assert "</script>" in js


# ========================================================================
# PreviewAgent 主体测试
# ========================================================================


class TestPreviewAgent:
    """PreviewAgent 核心逻辑测试"""

    def test_instantiation(self) -> None:
        """可以正常实例化"""
        agent = PreviewAgent()
        assert agent.name == "preview"

    def test_run_returns_error_when_no_pages(self) -> None:
        """缺少 pages 时返回错误"""
        agent = PreviewAgent()
        state = {"pages": [], "messages": []}
        result = agent.run(state)

        assert result["error_message"] == "缺少页面列表（pages），无法生成预览"
        assert result["current_stage"] == "error"

    def test_run_returns_error_when_pages_missing(self) -> None:
        """pages 字段不存在时返回错误"""
        agent = PreviewAgent()
        state = {"messages": []}
        result = agent.run(state)

        assert result["error_message"] == "缺少页面列表（pages），无法生成预览"
        assert result["current_stage"] == "error"

    def test_run_generates_html(self) -> None:
        """正常生成 HTML"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}, {"name": "列表"}],
            "messages": [],
        }
        result = agent.run(state)

        assert result["preview_html"] is not None
        assert "<!DOCTYPE html>" in result["preview_html"]
        assert "首页" in result["preview_html"]
        assert "列表" in result["preview_html"]

    def test_run_advances_to_backend_stage(self) -> None:
        """成功后流转到 backend 阶段"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "登录页"}],
            "messages": [],
        }
        result = agent.run(state)

        assert result["current_stage"] == "backend"

    def test_run_appends_message(self) -> None:
        """成功后添加消息"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}, {"name": "列表"}],
            "messages": [],
        }
        result = agent.run(state)

        assert len(result["messages"]) == 1
        assert result["messages"][0]["from"] == "preview"
        assert result["messages"][0]["to"] == "backend"
        assert "2 个页面" in result["messages"][0]["content"]

    def test_run_preserves_existing_messages(self) -> None:
        """保留已有消息"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}],
            "messages": [{"from": "architect", "content": "技术方案完成"}],
        }
        result = agent.run(state)

        assert len(result["messages"]) == 2
        assert result["messages"][0]["from"] == "architect"

    def test_run_does_not_mutate_input_state(self) -> None:
        """不修改输入状态"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}],
            "messages": [],
        }
        original_messages = state["messages"][:]
        result = agent.run(state)

        assert state["messages"] == original_messages
        assert result is not state

    def test_run_includes_html_skeleton(self) -> None:
        """生成的 HTML 包含完整骨架"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}],
            "messages": [],
        }
        result = agent.run(state)
        html = result["preview_html"]

        assert '<html lang="zh-CN">' in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html

    def test_run_includes_navigation(self) -> None:
        """生成的 HTML 包含导航"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}, {"name": "列表"}],
            "messages": [],
        }
        result = agent.run(state)
        html = result["preview_html"]

        assert "sidebar" in html

    def test_run_generates_page_sections(self) -> None:
        """为每个页面生成独立 section"""
        agent = PreviewAgent()
        state = {
            "pages": [
                {"name": "首页"},
                {"name": "列表"},
                {"name": "设置"},
            ],
            "messages": [],
        }
        result = agent.run(state)
        html = result["preview_html"]

        assert 'id="page-0"' in html
        assert 'id="page-1"' in html
        assert 'id="page-2"' in html

    def test_run_includes_js_for_multiple_pages(self) -> None:
        """多页面时包含 JavaScript"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}, {"name": "列表"}],
            "messages": [],
        }
        result = agent.run(state)
        html = result["preview_html"]

        assert "<script>" in html
        assert "showPage" in html

    def test_run_no_js_for_single_page(self) -> None:
        """单页面时不包含 JavaScript"""
        agent = PreviewAgent()
        state = {
            "pages": [{"name": "首页"}],
            "messages": [],
        }
        result = agent.run(state)
        html = result["preview_html"]

        assert "<script>" not in html

    def test_run_pages_without_name(self) -> None:
        """页面没有 name 字段时使用默认值"""
        agent = PreviewAgent()
        state = {
            "pages": [{"desc": "一个没有名字的页面"}],
            "messages": [],
        }
        result = agent.run(state)

        assert result["preview_html"] is not None
        assert "页面1" in result["preview_html"]

    def test_run_complex_page_types(self) -> None:
        """复杂页面类型正确映射组件"""
        agent = PreviewAgent()
        state = {
            "pages": [
                {"name": "用户登录"},
                {"name": "文章列表"},
                {"name": "数据仪表盘"},
            ],
            "messages": [],
        }
        result = agent.run(state)
        html = result["preview_html"]

        # 登录页有表单
        assert "data-form" in html
        # 列表页有表格
        assert "data-table" in html
        # 仪表盘有图表
        assert "chart-placeholder" in html


# ========================================================================
# 组件模板库完整性测试
# ========================================================================


class TestComponentTemplates:
    """确保所有模板都存在且非空"""

    REQUIRED_COMPONENTS = [
        "sidebar",
        "topbar",
        "table",
        "form",
        "card",
        "chart",
        "modal",
        "tabs",
        "pagination",
    ]

    def test_all_templates_exist(self) -> None:
        for comp in self.REQUIRED_COMPONENTS:
            assert comp in COMPONENT_TEMPLATES, f"缺少组件模板: {comp}"

    def test_all_templates_non_empty(self) -> None:
        for comp in self.REQUIRED_COMPONENTS:
            assert len(COMPONENT_TEMPLATES[comp]) > 0, f"组件模板为空: {comp}"

    def test_page_type_mapping_covers_all_components(self) -> None:
        """确保页面类型映射中引用的组件都在模板库中"""
        used_components = set()
        for components in PAGE_TYPE_MAPPING.values():
            used_components.update(components)
        for comp in used_components:
            assert comp in COMPONENT_TEMPLATES, f"页面类型引用了未定义的组件: {comp}"
