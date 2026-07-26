"""PRD 模板管理器

支持从 JSON/YAML 文件加载 PRD 模板，模板定义了：
1. 必填字段（sections）
2. 输出格式
3. 特殊说明
"""

from dataclasses import dataclass, field
from pathlib import Path

# 默认模板目录
_TEMPLATES_DIR = Path(__file__).parent / "defaults"


@dataclass
class PrdSection:
    """PRD 章节定义"""

    name: str  # 章节名（如 "产品概述"）
    description: str  # 章节说明（给 LLM 的指引）
    required: bool = True  # 是否必填
    format_hint: str = ""  # 格式提示（如 "- [类型]：[原因]"）


@dataclass
class PrdTemplate:
    """PRD 模板定义"""

    name: str  # 模板名（如 "default", "ecommerce"）
    description: str  # 模板描述
    sections: list[PrdSection] = field(default_factory=list)
    intro: str = ""  # 开头说明
    rules: list[str] = field(default_factory=list)  # 铁律/规则
    postscript: str = ""  # 结尾补充

    def render(self) -> str:
        """渲染模板为 PRD 格式说明（嵌入 prompt）"""
        parts = []

        if self.intro:
            parts.append(self.intro)

        parts.append("## PRD 格式\n")
        parts.append("你的整个回复只能包含：\n")
        parts.append("---PRD_START---")

        for section in self.sections:
            parts.append(f"## {section.name}")
            if section.description:
                parts.append(f"[{section.description}]")
            if section.format_hint:
                parts.append(section.format_hint)

        parts.append("---PRD_END---")

        if self.rules:
            parts.append("\n## 铁律")
            for rule in self.rules:
                parts.append(f"- {rule}")

        if self.postscript:
            parts.append(f"\n{self.postscript}")

        return "\n".join(parts)


# ========================================================================
# 内置模板
# ========================================================================

_DEFAULT_TEMPLATE = PrdTemplate(
    name="default",
    description="通用 PRD 模板，适用于大多数 Web 应用",
    sections=[
        PrdSection(
            name="产品概述",
            description="一句话说清楚这个产品是什么",
        ),
        PrdSection(
            name="目标用户",
            description="用户类型：原因",
            format_hint="- [用户类型]：[原因]",
        ),
        PrdSection(
            name="核心功能（按优先级）",
            description="功能名：描述",
            format_hint="1. [功能名]：[描述]",
        ),
        PrdSection(
            name="页面结构",
            description="页面名，包含元素和用户操作",
            format_hint="- **[页面名]**\n  - 元素：[...]\n  - 操作：[...]",
        ),
        PrdSection(
            name="数据模型",
            description="实体名和关键字段",
            format_hint="- **[实体]**：关键字段 [a, b, c]",
        ),
        PrdSection(
            name="非功能需求",
            description="性能、安全、兼容性等方面的要求",
            format_hint="- [...]",
        ),
    ],
    rules=[
        "追问不超过3轮。第3轮必须产出PRD，缺失信息用合理推断补全。",
        "不要输出技术实现。",
        "你的整个回复要么全是[ASK_USER]块，要么全是---PRD_START---块。不允许有其他内容。",
    ],
)

_ECOMMERCE_TEMPLATE = PrdTemplate(
    name="ecommerce",
    description="电商类应用 PRD 模板",
    sections=[
        PrdSection(
            name="产品概述",
            description="一句话说清楚这个产品是什么",
        ),
        PrdSection(
            name="目标用户",
            description="用户类型：原因",
            format_hint="- [用户类型]：[原因]",
        ),
        PrdSection(
            name="商品管理",
            description="商品展示、分类、搜索等功能",
            format_hint="1. [功能名]：[描述]",
        ),
        PrdSection(
            name="交易流程",
            description="购物车、下单、支付、退款等",
            format_hint="1. [功能名]：[描述]",
        ),
        PrdSection(
            name="用户中心",
            description="注册登录、个人中心、订单管理等",
            format_hint="1. [功能名]：[描述]",
        ),
        PrdSection(
            name="页面结构",
            description="页面名，包含元素和用户操作",
            format_hint="- **[页面名]**\n  - 元素：[...]\n  - 操作：[...]",
        ),
        PrdSection(
            name="数据模型",
            description="商品、订单、用户等实体",
            format_hint="- **[实体]**：关键字段 [a, b, c]",
        ),
        PrdSection(
            name="非功能需求",
            description="性能、安全、并发等方面的要求",
            format_hint="- [...]",
        ),
    ],
    rules=[
        "追问不超过3轮。第3轮必须产出PRD，缺失信息用合理推断补全。",
        "不要输出技术实现。",
        "你的整个回复要么全是[ASK_USER]块，要么全是---PRD_START---块。不允许有其他内容。",
    ],
)

_TOOL_TEMPLATE = PrdTemplate(
    name="tool",
    description="工具类应用 PRD 模板（如计算器、转换器、编辑器）",
    sections=[
        PrdSection(
            name="产品概述",
            description="一句话说清楚这个工具是做什么的",
        ),
        PrdSection(
            name="目标用户",
            description="用户类型：使用场景",
            format_hint="- [用户类型]：[使用场景]",
        ),
        PrdSection(
            name="核心功能",
            description="工具的主要功能点",
            format_hint="1. [功能名]：[描述]",
        ),
        PrdSection(
            name="输入输出",
            description="用户输入什么，得到什么结果",
            format_hint="- 输入：[...]\n- 输出：[...]",
        ),
        PrdSection(
            name="页面结构",
            description="界面布局和交互方式",
            format_hint="- **[区域名]**\n  - 元素：[...]\n  - 操作：[...]",
        ),
        PrdSection(
            name="非功能需求",
            description="性能、易用性等方面的要求",
            format_hint="- [...]",
        ),
    ],
    rules=[
        "追问不超过3轮。第3轮必须产出PRD，缺失信息用合理推断补全。",
        "不要输出技术实现。",
        "你的整个回复要么全是[ASK_USER]块，要么全是---PRD_START---块。不允许有其他内容。",
    ],
)

# 模板注册表
_TEMPLATES: dict[str, PrdTemplate] = {
    "default": _DEFAULT_TEMPLATE,
    "ecommerce": _ECOMMERCE_TEMPLATE,
    "tool": _TOOL_TEMPLATE,
}


def list_templates() -> list[dict[str, str]]:
    """列出所有可用模板"""
    return [
        {"name": t.name, "description": t.description}
        for t in _TEMPLATES.values()
    ]


def get_template(name: str = "default") -> PrdTemplate:
    """获取指定模板，不存在则返回默认模板"""
    return _TEMPLATES.get(name, _DEFAULT_TEMPLATE)


def register_template(template: PrdTemplate) -> None:
    """注册新模板"""
    _TEMPLATES[template.name] = template
