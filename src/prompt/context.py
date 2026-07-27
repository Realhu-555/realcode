"""Prompt 上下文组装

设计理念：
- 内容、渲染、注入三阶段分离
- PromptContext（纯数据）→ TemplateRenderer（纯渲染）→ Agent.run()（注入 LLM）
- 多源输入统一聚合：产品信息、品牌调性、上游策略、工具描述 → 全部汇入 → 一次渲染
"""

from dataclasses import dataclass, field
from datetime import date

from src.tools.protocol import ToolDescription


@dataclass
class PromptContext:
    """统一的 prompt 组装上下文 —— 所有内容来源的聚合点

    收集来自用户输入、上游 Agent 输出、工具注册表、长期记忆的数据，
    统一传递给模板渲染器。

    使用方式：
        ctx = PromptContext(
            agent_name="公众号内容创作者",
            role_instructions=renderer.load_template("gzh.md"),
            tools=registry.build_descriptions(["content_save"]),
            product_name="RAG 智能问答系统",
            ...
        )
        prompt = renderer.render(ctx.role_instructions, ctx.to_template_vars())
    """

    # === Agent 身份 ===
    agent_name: str = ""                    # "公众号内容创作者"
    role_instructions: str = ""             # 角色定义（从模板文件加载）

    # === 工具信息 ===
    tools: list[ToolDescription] = field(default_factory=list)

    # === 产品信息（来自用户输入）===
    product_name: str = ""
    product_description: str = ""
    target_users: str = ""
    key_selling_points: list[str] = field(default_factory=list)
    brand_tone: str = ""                   # 专业 / 轻松 / 极客
    competitors: list[str] = field(default_factory=list)

    # === 图片输入（MiMo V2.5 视觉理解结果）===
    image_descriptions: str = ""           # 上传图片的文字描述

    # === 上游产出 ===
    strategy: str | None = None            # 策略 Agent 的输出（渠道 Agent 用）

    # === 审校 Agent 专用 ===
    other_channel_contents: dict[str, str] | None = None  # 其他渠道的内容

    # === 记忆 ===
    user_preferences: str = ""             # 长期记忆中提取的用户偏好

    # === 环境 ===
    current_date: str = field(default_factory=lambda: date.today().isoformat())

    def to_template_vars(self) -> dict:
        """转为 Jinja2 模板变量"""
        return {
            "agent_name": self.agent_name,
            "tools": self._format_tools(),
            "product": {
                "name": self.product_name,
                "description": self.product_description,
                "target_users": self.target_users,
                "key_selling_points": self.key_selling_points,
                "competitors": self.competitors,
            },
            "brand": {
                "tone": self.brand_tone,
            },
            "strategy": self.strategy or "",
            "other_channels": self.other_channel_contents or {},
            "preferences": self.user_preferences,
            "images": self.image_descriptions,
            "current_date": self.current_date,
        }

    def _format_tools(self) -> str:
        """将工具描述格式化为 prompt 可用的 Markdown 文本块"""
        if not self.tools:
            return "（无可用工具）"
        lines = []
        for t in self.tools:
            params_desc = t.parameters.get("properties", {})
            lines.append(f"- **{t.name}**: {t.description}")
            required_params = t.parameters.get("required", [])
            for pname, pinfo in params_desc.items():
                tag = "（必填）" if pname in required_params else ""
                lines.append(f"  - `{pname}`: {pinfo.get('description', '')}{tag}")
        return "\n".join(lines)
