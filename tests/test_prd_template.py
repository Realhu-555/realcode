"""PRD 模板化测试"""

import pytest

from src.orchestrator.state import extract_prd_structured


# ========================================================================
# 测试数据：标准 PRD 文本
# ========================================================================

SAMPLE_PRD = """---PRD_START---
## 产品概述
团队任务看板，支持拖拽管理任务状态

## 目标用户
- **项目经理**：需要跟踪团队任务进度
- **开发人员**：需要查看和更新自己的任务

## 核心功能（按优先级）
1. **任务创建**：用户可以创建新任务并填写标题、描述、优先级（优先级：高）
2. **状态管理**：支持拖拽将任务在待办/进行中/已完成之间切换（优先级：高）
3. **指派功能**：项目经理可以将任务指派给团队成员（优先级：中）

## 页面结构
- **任务看板页面**
  - 元素：任务卡片、列标题、新建按钮
  - 操作：拖拽卡片、点击创建、点击查看详情
- **任务详情弹窗**
  - 元素：标题、描述、指派人、优先级
  - 操作：编辑、保存、关闭

## 数据模型
- **任务**：关键字段 [title, description, assignee, priority, status]
- **用户**：关键字段 [name, email, role]

## 非功能需求
- 支持 10 人以下小团队使用
- 页面加载时间不超过 2 秒
---PRD_END---
"""

SAMPLE_PRD_NO_MARKERS = """## 产品概述
个人博客系统

## 目标用户
- **博主**：分享技术文章

## 核心功能
1. **文章编辑**：支持 Markdown 编辑和发布
2. **标签分类**：按标签筛选文章
3. **评论区**：读者可以评论

## 页面结构
- **文章列表页**
  - 元素：文章卡片、搜索框、标签筛选
  - 操作：搜索、筛选、点击进入文章

## 数据模型
- **文章**：关键字段 [title, content, tags, created_at]
- **评论**：关键字段 [content, author, article_id]

## 非功能需求
- 支持移动端访问
"""


# ========================================================================
# PRD 格式验证测试
# ========================================================================


def test_prd_has_start_marker():
    """PRD 应该有 ---PRD_START--- 标记"""
    assert "---PRD_START---" in SAMPLE_PRD


def test_prd_has_end_marker():
    """PRD 应该有 ---PRD_END--- 标记"""
    assert "---PRD_END---" in SAMPLE_PRD


def test_prd_markers_are_correctly_paired():
    """PRD 标记应该正确配对"""
    start_count = SAMPLE_PRD.count("---PRD_START---")
    end_count = SAMPLE_PRD.count("---PRD_END---")
    assert start_count == 1
    assert end_count == 1


def test_prd_start_before_end():
    """PRD_START 应该在 PRD_END 之前"""
    start_pos = SAMPLE_PRD.find("---PRD_START---")
    end_pos = SAMPLE_PRD.find("---PRD_END---")
    assert start_pos < end_pos


def test_prd_has_required_sections():
    """PRD 应该包含所有必需章节"""
    required_sections = [
        "产品概述",
        "目标用户",
        "核心功能",
        "页面结构",
        "数据模型",
        "非功能需求",
    ]
    for section in required_sections:
        assert f"## {section}" in SAMPLE_PRD, f"缺少章节: ## {section}"


def test_prd_sections_are_in_order():
    """PRD 章节应该按正确顺序排列"""
    sections = [
        "产品概述",
        "目标用户",
        "核心功能",
        "页面结构",
        "数据模型",
        "非功能需求",
    ]
    positions = [SAMPLE_PRD.find(f"## {section}") for section in sections]
    # 检查位置是否递增
    for i in range(len(positions) - 1):
        assert positions[i] < positions[i + 1], f"章节顺序错误: {sections[i]} 应在 {sections[i + 1]} 之前"


def test_prd_content_between_markers():
    """PRD 内容应该在标记之间"""
    content_start = SAMPLE_PRD.find("---PRD_START---") + len("---PRD_START---")
    content_end = SAMPLE_PRD.find("---PRD_END---")
    content = SAMPLE_PRD[content_start:content_end].strip()
    assert len(content) > 0, "PRD 内容为空"


# ========================================================================
# PRD 结构化提取测试
# ========================================================================


def test_extract_returns_dict():
    """提取结果为字典类型"""
    result = extract_prd_structured(SAMPLE_PRD)
    assert isinstance(result, dict)


def test_extract_all_main_fields():
    """完整 PRD 应提取出所有主要字段"""
    result = extract_prd_structured(SAMPLE_PRD)

    assert "product_overview" in result
    assert "target_users" in result
    assert "core_features" in result
    assert "page_structure" in result
    assert "data_model" in result
    assert "non_functional_requirements" in result


def test_extract_product_overview():
    """提取产品概述"""
    result = extract_prd_structured(SAMPLE_PRD)
    assert result["product_overview"] == "团队任务看板，支持拖拽管理任务状态"


def test_extract_target_users():
    """提取目标用户"""
    result = extract_prd_structured(SAMPLE_PRD)
    users = result["target_users"]

    assert len(users) == 2
    assert users[0]["name"] == "项目经理"
    assert "跟踪" in users[0]["description"]
    assert users[1]["name"] == "开发人员"


def test_extract_core_features():
    """提取核心功能"""
    result = extract_prd_structured(SAMPLE_PRD)
    features = result["core_features"]

    assert len(features) == 3
    assert features[0]["name"] == "任务创建"
    assert features[1]["name"] == "状态管理"
    assert features[2]["name"] == "指派功能"


def test_extract_page_structure():
    """提取页面结构"""
    result = extract_prd_structured(SAMPLE_PRD)
    pages = result["page_structure"]

    assert len(pages) == 2
    assert pages[0]["page"] == "任务看板页面"
    assert len(pages[0]["items"]) == 2  # 元素、操作两项
    assert pages[1]["page"] == "任务详情弹窗"


def test_extract_data_model():
    """提取数据模型"""
    result = extract_prd_structured(SAMPLE_PRD)
    models = result["data_model"]

    assert len(models) == 2
    assert models[0]["name"] == "任务"
    assert "title" in models[0]["fields"]
    assert "description" in models[0]["fields"]
    assert models[1]["name"] == "用户"


def test_extract_non_functional_requirements():
    """提取非功能需求"""
    result = extract_prd_structured(SAMPLE_PRD)
    nfr = result["non_functional_requirements"]

    assert len(nfr) == 2
    assert "10 人" in nfr[0]
    assert "2 秒" in nfr[1]


# ========================================================================
# PRD 标记处理
# ========================================================================


def test_handles_prd_markers():
    """正确处理 ---PRD_START--- 和 ---PRD_END--- 标记"""
    result = extract_prd_structured(SAMPLE_PRD)
    assert result["product_overview"] == "团队任务看板，支持拖拽管理任务状态"


def test_handles_no_prd_markers():
    """无标记时也能正常提取"""
    result = extract_prd_structured(SAMPLE_PRD_NO_MARKERS)
    assert result["product_overview"] == "个人博客系统"
    assert len(result["core_features"]) == 3


# ========================================================================
# 边界情况
# ========================================================================


def test_returns_none_for_empty_string():
    """空字符串返回 None"""
    assert extract_prd_structured("") is None


def test_returns_none_for_whitespace_only():
    """纯空白返回 None"""
    assert extract_prd_structured("   \n  \n  ") is None


def test_returns_none_for_only_markers():
    """只有标记无内容返回 None"""
    assert extract_prd_structured("---PRD_START---\n---PRD_END---") is None


def test_returns_none_for_plain_text():
    """纯文本无结构返回 None"""
    assert extract_prd_structured("这是一段普通文本，没有结构化内容") is None


def test_partial_extraction():
    """部分字段缺失时只提取存在的字段"""
    partial_prd = """## 产品概述
简单工具

## 核心功能
1. **功能一**：描述一
"""
    result = extract_prd_structured(partial_prd)

    assert result["product_overview"] == "简单工具"
    assert len(result["core_features"]) == 1
    # 缺失的字段不应出现
    assert "target_users" not in result
    assert "page_structure" not in result


# ========================================================================
# 格式变体
# ========================================================================


def test_chinese_colons():
    """中文冒号（：）也能正确解析"""
    prd = """## 产品概述
测试产品

## 目标用户
- **用户A**：用户A的描述

## 数据模型
- **实体X**：关键字段 [a, b, c]
"""
    result = extract_prd_structured(prd)
    assert result["target_users"][0]["name"] == "用户A"
    assert result["data_model"][0]["fields"] == ["a", "b", "c"]


def test_english_colons():
    """英文冒号（:）也能正确解析"""
    prd = """## 产品概述
Test product

## 目标用户
- **User A**: Description of user A

## 数据模型
- **Entity X**: Key fields [a, b, c]
"""
    result = extract_prd_structured(prd)
    assert result["target_users"][0]["name"] == "User A"
    assert result["data_model"][0]["fields"] == ["a", "b", "c"]


def test_numbered_list():
    """数字编号列表也能提取"""
    prd = """## 核心功能
1. **功能一**：描述一
2. **功能二**：描述二
3. **功能三**：描述三
"""
    result = extract_prd_structured(prd)
    assert len(result["core_features"]) == 3


def test_bullet_with_dash():
    """短横线列表能正确提取"""
    prd = """## 非功能需求
- 性能要求
- 安全要求
- 兼容性要求
"""
    result = extract_prd_structured(prd)
    assert len(result["non_functional_requirements"]) == 3


def test_bullet_with_asterisk():
    """星号列表能正确提取"""
    prd = """## 非功能需求
* 性能要求
* 安全要求
"""
    result = extract_prd_structured(prd)
    assert len(result["non_functional_requirements"]) == 2


# ========================================================================
# 页面结构提取
# ========================================================================


def test_page_structure_with_sub_items():
    """页面结构包含缩进子项"""
    prd = """## 页面结构
- **首页**
  - 元素：搜索栏、轮播图
  - 操作：搜索、点击
- **详情页**
  - 元素：内容区、评论区
  - 操作：收藏、评论
"""
    result = extract_prd_structured(prd)
    pages = result["page_structure"]

    assert len(pages) == 2
    assert pages[0]["page"] == "首页"
    assert len(pages[0]["items"]) == 2
    assert pages[1]["page"] == "详情页"


def test_page_structure_single_page():
    """单个页面的结构"""
    prd = """## 页面结构
- **登录页**
  - 元素：用户名输入框、密码输入框、登录按钮
  - 操作：输入、点击登录
"""
    result = extract_prd_structured(prd)
    pages = result["page_structure"]

    assert len(pages) == 1
    assert pages[0]["page"] == "登录页"
    assert len(pages[0]["items"]) == 2  # 元素、操作两项


# ========================================================================
# 数据模型提取
# ========================================================================


def test_data_model_with_fields():
    """数据模型提取字段列表"""
    prd = """## 数据模型
- **用户**：关键字段 [id, name, email]
- **订单**：关键字段 [id, user_id, amount, status]
"""
    result = extract_prd_structured(prd)
    models = result["data_model"]

    assert len(models) == 2
    assert models[0]["name"] == "用户"
    assert models[0]["fields"] == ["id", "name", "email"]
    assert models[1]["name"] == "订单"
    assert len(models[1]["fields"]) == 4


def test_data_model_without_field_list():
    """数据模型无字段列表时 fields 为空"""
    prd = """## 数据模型
- **实体A**：存储用户相关信息
"""
    result = extract_prd_structured(prd)
    models = result["data_model"]

    assert len(models) == 1
    assert models[0]["name"] == "实体A"
    assert models[0]["fields"] == []


# ========================================================================
# 端到端场景
# ========================================================================


def test_blog_prd_extraction():
    """博客 PRD 的完整提取"""
    result = extract_prd_structured(SAMPLE_PRD_NO_MARKERS)

    assert result["product_overview"] == "个人博客系统"
    assert len(result["target_users"]) == 1
    assert result["target_users"][0]["name"] == "博主"
    assert len(result["core_features"]) == 3
    assert result["core_features"][0]["name"] == "文章编辑"
    assert len(result["page_structure"]) == 1
    assert len(result["data_model"]) == 2
    assert len(result["non_functional_requirements"]) == 1


def test_task_board_prd_extraction():
    """任务看板 PRD 的完整提取"""
    result = extract_prd_structured(SAMPLE_PRD)

    # 验证所有字段都存在且有值
    assert result["product_overview"]
    assert len(result["target_users"]) == 2
    assert len(result["core_features"]) == 3
    assert len(result["page_structure"]) == 2
    assert len(result["data_model"]) == 2
    assert len(result["non_functional_requirements"]) == 2


# ========================================================================
# 与 OutputArtifact 集成
# ========================================================================


def test_extraction_result_can_be_used_in_artifact():
    """提取结果可以放入 OutputArtifact.structured"""
    from src.orchestrator.state import create_output_artifact

    result = extract_prd_structured(SAMPLE_PRD)
    artifact = create_output_artifact(
        content=SAMPLE_PRD,
        structured=result,
        status="draft",
        version=1,
    )

    assert artifact["structured"] is not None
    assert artifact["structured"]["product_overview"] == "团队任务看板，支持拖拽管理任务状态"
    assert len(artifact["structured"]["core_features"]) == 3


def test_structured_field_is_none_when_extraction_fails():
    """无法提取时 structured 字段为 None"""
    from src.orchestrator.state import create_output_artifact

    result = extract_prd_structured("plain text without structure")
    artifact = create_output_artifact(
        content="plain text without structure",
        structured=result,
        status="draft",
        version=1,
    )

    assert artifact["structured"] is None


# ========================================================================
# PRD 模板格式验证
# ========================================================================


def test_prd_template_format_validation():
    """验证 PRD 模板格式是否正确"""
    import re

    # 检查 PRD 模板格式
    assert "---PRD_START---" in SAMPLE_PRD
    assert "---PRD_END---" in SAMPLE_PRD

    # 检查章节格式
    sections = re.findall(r"^##\s+(.+)$", SAMPLE_PRD, re.MULTILINE)
    assert len(sections) == 6
    assert "产品概述" in sections
    assert "目标用户" in sections
    assert "核心功能（按优先级）" in sections
    assert "页面结构" in sections
    assert "数据模型" in sections
    assert "非功能需求" in sections


def test_prd_content_is_between_markers():
    """PRD 内容应该在标记之间"""
    start_marker = "---PRD_START---"
    end_marker = "---PRD_END---"

    start_pos = SAMPLE_PRD.find(start_marker)
    end_pos = SAMPLE_PRD.find(end_marker)

    # 内容在标记之间
    content = SAMPLE_PRD[start_pos + len(start_marker):end_pos].strip()
    assert len(content) > 0

    # 内容包含章节
    assert "## 产品概述" in content
    assert "## 目标用户" in content
    assert "## 核心功能" in content
    assert "## 页面结构" in content
    assert "## 数据模型" in content
    assert "## 非功能需求" in content


def test_prd_sections_have_content():
    """PRD 每个章节都应该有内容"""
    import re

    # 移除标记
    content = SAMPLE_PRD.replace("---PRD_START---", "").replace("---PRD_END---", "").strip()

    # 提取每个章节的内容
    sections = re.split(r"^##\s+", content, flags=re.MULTILINE)[1:]  # 跳过第一个空元素

    for section in sections:
        lines = section.strip().split("\n")
        section_name = lines[0].strip()
        section_content = "\n".join(lines[1:]).strip()
        assert len(section_content) > 0, f"章节 '{section_name}' 内容为空"


def test_prd_has_minimum_sections():
    """PRD 应该至少有 6 个章节"""
    import re

    sections = re.findall(r"^##\s+(.+)$", SAMPLE_PRD, re.MULTILINE)
    assert len(sections) >= 6


def test_prd_target_users_have_descriptions():
    """目标用户应该有描述"""
    result = extract_prd_structured(SAMPLE_PRD)
    for user in result["target_users"]:
        assert "name" in user
        assert "description" in user
        assert len(user["description"]) > 0


def test_prd_core_features_have_descriptions():
    """核心功能应该有描述"""
    result = extract_prd_structured(SAMPLE_PRD)
    for feature in result["core_features"]:
        assert "name" in feature
        assert "description" in feature
        assert len(feature["description"]) > 0


def test_prd_page_structure_has_items():
    """页面结构应该有元素和操作"""
    result = extract_prd_structured(SAMPLE_PRD)
    for page in result["page_structure"]:
        assert "page" in page
        assert "items" in page
        assert len(page["items"]) >= 2  # 至少有元素和操作


def test_prd_data_model_has_fields():
    """数据模型应该有字段"""
    result = extract_prd_structured(SAMPLE_PRD)
    for model in result["data_model"]:
        assert "name" in model
        assert "fields" in model
        assert len(model["fields"]) >= 1  # 至少有一个字段


# ========================================================================
# PRD 模板管理器测试
# ========================================================================


def test_list_templates():
    """列出所有模板"""
    from src.llm.templates import list_templates

    templates = list_templates()
    assert isinstance(templates, list)
    assert len(templates) >= 3  # 至少有 default, ecommerce, tool

    names = [t["name"] for t in templates]
    assert "default" in names
    assert "ecommerce" in names
    assert "tool" in names


def test_get_default_template():
    """获取默认模板"""
    from src.llm.templates import get_template

    template = get_template("default")
    assert template.name == "default"
    assert len(template.sections) >= 6
    assert len(template.rules) >= 3


def test_get_ecommerce_template():
    """获取电商模板"""
    from src.llm.templates import get_template

    template = get_template("ecommerce")
    assert template.name == "ecommerce"
    assert any("商品" in s.name for s in template.sections)
    assert any("交易" in s.name for s in template.sections)


def test_get_tool_template():
    """获取工具模板"""
    from src.llm.templates import get_template

    template = get_template("tool")
    assert template.name == "tool"
    assert any("输入输出" in s.name for s in template.sections)


def test_get_unknown_template_returns_default():
    """获取不存在的模板返回默认模板"""
    from src.llm.templates import get_template

    template = get_template("nonexistent")
    assert template.name == "default"


def test_template_render():
    """模板渲染输出包含关键内容"""
    from src.llm.templates import get_template

    template = get_template("default")
    rendered = template.render()

    assert "---PRD_START---" in rendered
    assert "---PRD_END---" in rendered
    assert "产品概述" in rendered
    assert "目标用户" in rendered
    assert "核心功能" in rendered


def test_register_custom_template():
    """注册自定义模板"""
    from src.llm.templates import get_template, register_template
    from src.llm.templates.manager import PrdSection, PrdTemplate

    custom = PrdTemplate(
        name="test_custom",
        description="测试自定义模板",
        sections=[
            PrdSection(name="概要", description="简要描述"),
        ],
        rules=["测试规则"],
    )

    register_template(custom)
    retrieved = get_template("test_custom")

    assert retrieved.name == "test_custom"
    assert len(retrieved.sections) == 1


def test_prompt_uses_template():
    """prompt 构建使用模板"""
    from src.llm.prompts.requirement import get_prompt

    prompt = get_prompt("default")
    assert "---PRD_START---" in prompt
    assert "---PRD_END---" in prompt
    assert "产品概述" in prompt


def test_prompt_backward_compatible():
    """REQUIREMENT_PROMPT 向后兼容"""
    from src.llm.prompts.requirement import REQUIREMENT_PROMPT

    assert "---PRD_START---" in REQUIREMENT_PROMPT
    assert "ASK_USER" in REQUIREMENT_PROMPT
