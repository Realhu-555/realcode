"""预览 Agent —— 模板填充，非 LLM 生成"""

from src.agents.base import BaseAgent

# ========================================================================
# 组件模板库
# ========================================================================

COMPONENT_TEMPLATES = {
    "sidebar": """<nav class="sidebar">
  <ul>
    {items}
  </ul>
</nav>""",
    "topbar": """<header class="topbar">
  <h1>{title}</h1>
</header>""",
    "table": """<div class="data-table">
  <table>
    <thead>
      <tr>{headers}</tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</div>""",
    "form": """<form class="data-form">
  {fields}
</form>""",
    "card": """<div class="card">
  <h3>{title}</h3>
  <p>{content}</p>
</div>""",
    "chart": """<div class="chart-placeholder">
  <p>图表区域</p>
</div>""",
    "modal": """<div class="modal" style="display:none;">
  <div class="modal-content">
    <h3>{title}</h3>
    <p>{content}</p>
  </div>
</div>""",
    "tabs": """<div class="tabs">
  <div class="tab-buttons">
    {buttons}
  </div>
  <div class="tab-content">
    {content}
  </div>
</div>""",
    "pagination": """<div class="pagination">
  <button>上一页</button>
  <span>1 / 10</span>
  <button>下一页</button>
</div>""",
}

# ========================================================================
# 页面类型到组件的映射
# ========================================================================

PAGE_TYPE_MAPPING = {
    "登录": ["form"],
    "注册": ["form"],
    "列表": ["topbar", "table", "pagination"],
    "详情": ["topbar", "card", "form"],
    "仪表盘": ["topbar", "card", "chart"],
    "设置": ["topbar", "form", "tabs"],
    "管理": ["topbar", "table", "form", "modal"],
}

# ========================================================================
# HTML 骨架
# ========================================================================

HTML_SKELETON = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; min-height: 100vh; }}
    .sidebar {{ width: 200px; background: #2c3e50; color: white; padding: 20px; }}
    .sidebar ul {{ list-style: none; }}
    .sidebar li {{ padding: 10px 0; cursor: pointer; }}
    .sidebar li:hover {{ background: #34495e; }}
    .main-content {{ flex: 1; padding: 20px; background: #f5f5f5; }}
    .topbar {{ background: white; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .data-table table {{ width: 100%; border-collapse: collapse; background: white; }}
    .data-table th, .data-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
    .data-table th {{ background: #f8f9fa; font-weight: 600; }}
    .data-form {{ background: white; padding: 20px; border-radius: 8px; }}
    .data-form label {{ display: block; margin-bottom: 8px; font-weight: 500; }}
    .data-form input, .data-form select, .data-form textarea {{ width: 100%; padding: 8px; margin-bottom: 16px; border: 1px solid #ddd; border-radius: 4px; }}
    .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .card h3 {{ margin-bottom: 10px; color: #333; }}
    .chart-placeholder {{ background: white; padding: 40px; border-radius: 8px; text-align: center; color: #999; }}
    .modal {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }}
    .modal-content {{ background: white; padding: 20px; border-radius: 8px; min-width: 300px; }}
    .tabs .tab-buttons {{ display: flex; gap: 10px; margin-bottom: 16px; }}
    .tabs .tab-buttons button {{ padding: 8px 16px; border: 1px solid #ddd; background: white; cursor: pointer; }}
    .tabs .tab-buttons button.active {{ background: #3498db; color: white; border-color: #3498db; }}
    .pagination {{ display: flex; justify-content: center; gap: 10px; margin-top: 20px; }}
    .pagination button {{ padding: 8px 16px; border: 1px solid #ddd; background: white; cursor: pointer; border-radius: 4px; }}
    .page-section {{ display: none; }}
    .page-section.active {{ display: block; }}
  </style>
</head>
<body>
{navigation}
<div class="main-content">
{content}
</div>
</body>
</html>"""


def _get_page_type(page_name: str) -> str:
    """根据页面名称猜测页面类型。"""
    for keyword, _ in PAGE_TYPE_MAPPING.items():
        if keyword in page_name:
            return keyword
    return "默认"


def _render_table() -> str:
    """渲染表格组件，带假数据。"""
    return COMPONENT_TEMPLATES["table"].format(
        headers="<th>列1</th><th>列2</th><th>列3</th>",
        rows="<tr><td>示例数据1</td><td>示例数据2</td><td>示例数据3</td></tr>"
        "<tr><td>示例数据4</td><td>示例数据5</td><td>示例数据6</td></tr>",
    )


def _render_form() -> str:
    """渲染表单组件，带假字段。"""
    return COMPONENT_TEMPLATES["form"].format(
        fields='<label>字段1</label>\n<input type="text" placeholder="请输入字段1">'
        '\n<label>字段2</label>\n<input type="text" placeholder="请输入字段2">'
        '\n<button type="submit">提交</button>'
    )


def _render_card(title: str = "卡片标题", content: str = "卡片内容") -> str:
    """渲染卡片组件。"""
    return COMPONENT_TEMPLATES["card"].format(title=title, content=content)


def _render_chart() -> str:
    """渲染图表占位符。"""
    return COMPONENT_TEMPLATES["chart"]


def _render_modal() -> str:
    """渲染弹窗组件。"""
    return COMPONENT_TEMPLATES["modal"].format(title="弹窗标题", content="弹窗内容")


def _render_tabs() -> str:
    """渲染标签页组件。"""
    return COMPONENT_TEMPLATES["tabs"].format(
        buttons='<button class="active">标签1</button><button>标签2</button><button>标签3</button>',
        content="<p>标签页内容</p>",
    )


def _render_pagination() -> str:
    """渲染分页组件。"""
    return COMPONENT_TEMPLATES["pagination"]


def _render_component(component_name: str, page_title: str = "") -> str:
    """渲染单个组件。"""
    renderers = {
        "sidebar": lambda: COMPONENT_TEMPLATES["sidebar"].format(
            items="<li>首页</li><li>功能1</li><li>功能2</li><li>设置</li>"
        ),
        "topbar": lambda: COMPONENT_TEMPLATES["topbar"].format(title=page_title or "页面标题"),
        "table": _render_table,
        "form": _render_form,
        "card": _render_card,
        "chart": _render_chart,
        "modal": _render_modal,
        "tabs": _render_tabs,
        "pagination": _render_pagination,
    }
    renderer = renderers.get(component_name)
    if renderer:
        return renderer()
    return f"<!-- 未知组件: {component_name} -->"


def _render_navigation(pages: list[dict]) -> str:
    """渲染侧边栏导航。"""
    if not pages:
        return ""
    items = []
    for i, page in enumerate(pages):
        name = page.get("name", f"页面{i + 1}")
        active = " active" if i == 0 else ""
        items.append(f'<li class="nav-item{active}" onclick="showPage(\'page-{i}\')">{name}</li>')
    return COMPONENT_TEMPLATES["sidebar"].format(items="\n    ".join(items))


def _render_page_content(page: dict, index: int) -> str:
    """渲染单个页面的内容区域。"""
    page_name = page.get("name", f"页面{index + 1}")
    page_type = _get_page_type(page_name)
    components = PAGE_TYPE_MAPPING.get(page_type, ["topbar", "card"])

    sections = []
    for comp in components:
        sections.append(_render_component(comp, page_name))

    content = "\n".join(sections)
    active_class = " active" if index == 0 else ""
    return f'<div class="page-section{active_class}" id="page-{index}">\n{content}\n</div>'


def _generate_javascript(num_pages: int) -> str:
    """生成页面切换的 JavaScript。"""
    if num_pages <= 1:
        return ""
    return """
<script>
function showPage(pageId) {
  document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  document.getElementById(pageId).classList.add('active');
  event.target.classList.add('active');
}
</script>"""


class PreviewAgent(BaseAgent):
    """预览 Agent —— 模板填充，非 LLM 生成。

    读取 PRD 页面列表和技术方案功能模块，为每个页面从预定义组件库中选择组件组合，
    用假数据填充，组装成单文件 HTML。
    """

    def __init__(self) -> None:
        super().__init__(
            name="preview",
            system_prompt="你是预览生成 Agent，负责生成静态 HTML 预设。",
        )

    def run(self, state: dict) -> dict:
        """执行预览生成。

        从 state 中读取 pages 和 modules，生成 HTML 预设。

        Args:
            state: 项目状态字典，必须包含 pages 列表

        Returns:
            更新后的状态字典，包含 preview_html 字段
        """
        pages = state.get("pages", [])
        if not pages:
            return {
                **state,
                "error_message": "缺少页面列表（pages），无法生成预览",
                "current_stage": "error",
            }

        # 1. 生成导航
        navigation = _render_navigation(pages)

        # 2. 生成各页面内容
        page_contents = []
        for i, page in enumerate(pages):
            page_contents.append(_render_page_content(page, i))

        content = "\n".join(page_contents)

        # 3. 生成 JavaScript
        js = _generate_javascript(len(pages))

        # 4. 组装 HTML
        title = pages[0].get("name", "预览") if pages else "预览"
        html = HTML_SKELETON.format(
            title=title,
            navigation=navigation,
            content=content,
        )

        # 在 </body> 前插入 JS
        if js:
            html = html.replace("</body>", f"{js}\n</body>")

        return {
            **state,
            "preview_html": html,
            "current_stage": "backend",
            "messages": state.get("messages", [])
            + [
                {
                    "from": "preview",
                    "to": "backend",
                    "type": "output",
                    "content": f"已生成 {len(pages)} 个页面的预览 HTML",
                }
            ],
        }
