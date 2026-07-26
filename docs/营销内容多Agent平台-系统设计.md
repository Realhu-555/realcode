# 营销内容多 Agent 平台 — 系统设计文档

> 基于 ai-dev-platform 改造
> 日期：2026-07-26
> 状态：设计阶段

---

## 目录

1. [项目概述](#一项目概述)
2. [多 Agent 必要性分析](#二多-agent-必要性分析)
3. [整体架构](#三整体架构)
4. [核心子系统层设计](#四核心子系统层设计)
5. [Agent 层设计](#五agent-层设计)
6. [编排流程](#六编排流程)
7. [数据模型](#七数据模型)
8. [API 接口](#八api-接口)
9. [前端设计](#九前端设计)
10. [改造实施计划](#十改造实施计划)

---

## 一、项目概述

### 1.1 应用场景

市场运营人员输入产品信息和投放渠道，多 Agent 并行生成不同渠道的营销物料，经统一审校后一键导出。

### 1.2 核心流程

```
用户输入产品信息（引导式表单 / 自由文本）
    ↓
策略 Agent 分析产品 → 输出内容策略 → 用户确认
    ↓
三路并行：公众号长文 + 知乎回答 + 小红书笔记
    ↓
审校 Agent 统一检查 → 标注问题 → 生成修改建议
    ↓
一键导出 Markdown
```

### 1.3 与现有 ai-dev-platform 的对应关系

| 原有 Agent | 新 Agent | 变化说明 |
|-----------|---------|---------|
| Requirement | 策略 Agent | 追问确认逻辑复用 |
| Architect | — | 移除，内容生成不需要技术架构设计 |
| Backend（并行） | 公众号 Agent | 代码生成 → 公众号长文生成 |
| Frontend（并行） | 知乎 Agent | 代码生成 → 知乎回答生成 |
| — | 小红书 Agent | 新增，三路并行 |
| Tester | 审校 Agent | 检查对象从代码变为内容 |
| Deployer | 导出 Agent | 从打包 zip 变为导出 Markdown |
| Preview | — | 移除 |

### 1.4 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 编排框架 | LangGraph | 复用现有 state graph |
| LLM | DeepSeek V4 + MiniMax 2.7 | 多模型智能路由，复用现有 LLMProvider |
| 模板渲染 | Jinja2 | 新增，替代静态 prompt 字符串 |
| 后端 | Python 3.12+、FastAPI、WebSocket | 复用 |
| 前端 | Vue 3 + TypeScript + Element Plus | 复用 |
| 数据库 | SQLite | 复用，新增 brand_profiles 和 content_projects 表 |
| 部署 | Docker | 复用 |

---

## 二、多 Agent 必要性分析

判断标准：真正需要多 Agent 的场景必须满足以下**至少两条**：

| 条件 | 含义 |
|------|------|
| ① 不同的 System Prompt | 每个 Agent 的角色、知识领域、行为约束不同 |
| ② 不同的工具集 | 不同 Agent 能调用不同的工具 |
| ③ 需要并行执行 | 多路独立工作后合并结果 |
| ④ 不同的模型需求 | 有的要强推理，有的要低成本 |

### 本项目的必要性验证

| 条件 | 满足？ | 理由 |
|------|:--:|------|
| ① 不同 System Prompt | ✅ | 公众号要求深度长文、知乎要求专业知识、小红书要求轻松种草——三个渠道的写作角色完全不同 |
| ② 不同工具集 | ✅ | 策略 Agent 有 web_search 工具，渠道 Agent 没有；审校 Agent 有 brand_guideline_query 工具，渠道 Agent 没有 |
| ③ 需要并行执行 | ✅ | 三篇内容独立生成，并行执行，总耗时 = max(三路) 而非 sum(三路) |
| ④ 不同模型需求 | ✅ | 公众号/知乎用 DeepSeek（深度内容需要强推理），小红书/审校用 MiniMax（轻松内容和检查不需要强推理，省钱） |

**结论：四项条件全部满足，是真正的多 Agent 场景。**

---

## 三、整体架构

### 3.1 分层结构

```
┌─────────────────────────────────────────────────┐
│  Web 层       │ FastAPI + WebSocket + Vue 3 前端  │
├─────────────────────────────────────────────────┤
│  编排层       │ LangGraph StateGraph + State      │
├──────────────┬──────────────────────────────────┤
│  Agent 层    │ 策略 / 公众号 / 知乎 / 小红书 /    │
│              │ 审校 / 导出（6 个 Agent）           │
├──────────────┼──────────────────────────────────┤
│  子系统层    │ 工具系统 │ Prompt 系统 │ 记忆系统   │
├──────────────┴──────────────────────────────────┤
│  基础设施层  │ LLMProvider / Config / Sandbox      │
└─────────────────────────────────────────────────┘
```

### 3.2 模块分层

| 层次 | 模块 | 职责 |
|------|------|------|
| 工具协议 | `src/tools/protocol.py` | Tool 协议定义（接口 + 上下文 + 输出） |
| 工具实现 | `src/tools/registry.py` + `src/tools/implementations/` | 工具注册表 + 具体实现 |
| Prompt | `src/prompt/context.py` + `src/prompt/renderer.py` | Prompt 上下文组装 + 模板渲染 |
| 记忆 | `src/orchestrator/long_term_memory.py` | 长期记忆（SQLite） |
| 编排 | `src/orchestrator/graph.py` | Agent 编排（LangGraph） |

---

## 四、核心子系统层设计

### 4.1 工具系统

#### 4.1.1 设计原则

- **执行和描述分离**：`ToolDescription`（给 AI 看）和 `Tool.execute()`（实际逻辑）独立。改 prompt 不影响工具实现，改工具实现不影响 prompt
- **ToolContext 统一注入**：所有工具通过同一个上下文对象获取运行时资源，不各自 `import config`
- **单例注册表 + Builder 模式**：工具注册一次，各 Agent 按权限获取
- **system_reminder 后处理**：工具执行后可向对话注入提醒

#### 4.1.2 工具清单

| 工具 ID | 使用者 | 用途 | 优先级 |
|---------|--------|------|:--:|
| `web_search` | 策略 Agent | 搜索竞品信息、行业趋势、目标用户画像 | MVP |
| `content_save` | 三个渠道 Agent | 保存草稿到本地 | MVP |
| `content_read` | 审校 Agent | 读取三篇草稿内容 | MVP |
| `content_list` | 审校/导出 Agent | 列出当前项目的所有产出 | MVP |
| `brand_guideline_query` | 审校 Agent | 查询品牌调性规则 | P1 |
| `image_suggest` | 三个渠道 Agent | 建议配图方案 | P2 |

#### 4.1.3 工具接口定义

```python
# src/tools/protocol.py
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from enum import Enum

class ToolKind(Enum):
    SEARCH = "search"
    READ = "read"
    WRITE = "write"

@dataclass
class ToolDescription:
    """给 AI 看的工具说明——和执行逻辑分离"""
    name: str                          # "web_search"
    description: str                   # "搜索互联网获取竞品信息和行业趋势"
    parameters: dict[str, Any]         # JSON Schema（参数定义）

@dataclass
class ToolContext:
    """工具执行上下文——统一注入所有运行时资源"""
    session_id: str
    working_dir: str
    project_state: dict[str, Any]      # 只读访问当前项目状态
    brand_profile: dict[str, Any] | None  # 品牌档案

@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    error: str | None = None
    system_reminder: str | None = None # 注入到 AI 对话的提醒

@runtime_checkable
class Tool(Protocol):
    """所有工具的接口协议"""
    tool_id: str
    kind: ToolKind
    description: ToolDescription

    async def execute(self, ctx: ToolContext, **kwargs) -> ToolResult:
        ...
```

#### 4.1.4 工具注册表

```python
# src/tools/registry.py
class ToolRegistry:
    """单例工具注册表——Builder 模式"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> "ToolRegistry":
        """注册一个工具，返回 self 支持链式调用"""
        self._tools[tool.tool_id] = tool
        return self

    def build_descriptions(self, agent_tool_ids: list[str]) -> list[ToolDescription]:
        """为指定 Agent 生成工具描述列表（注入 system prompt 用）
        
        只返回该 Agent 有权限的工具描述——
        Agent 看不到它无权使用的工具。
        """
        return [
            self._tools[tid].description 
            for tid in agent_tool_ids 
            if tid in self._tools
        ]

    def get(self, tool_id: str) -> Tool | None:
        return self._tools.get(tool_id)

# 全局单例
tool_registry = ToolRegistry()
```

#### 4.1.5 工具注册（启动时）

```python
# src/tools/__init__.py
from src.tools.registry import tool_registry
from src.tools.implementations.web_search import WebSearchTool
from src.tools.implementations.content_io import ContentSaveTool, ContentReadTool, ContentListTool

tool_registry \
    .register(WebSearchTool()) \
    .register(ContentSaveTool()) \
    .register(ContentReadTool()) \
    .register(ContentListTool())
```

#### 4.1.6 工具设计对照

| 设计模式 | 本项目实现 |
|---------|-----------|
| Tool 协议（execute + description） | `Tool` Protocol（execute + description 分离） |
| 工具分类和标识 | `Tool.kind` + `Tool.tool_id` |
| 统一上下文注入 | `ToolContext` |
| 按 Agent 过滤工具 | `registry.build_descriptions(agent_tool_ids)` |
| 后处理提醒注入 | `ToolResult.system_reminder` |

---

### 4.2 Prompt 系统

#### 4.2.1 设计原则

- **内容、渲染、注入三阶段分离**：PromptContext（纯数据）→ TemplateRenderer（纯渲染）→ Agent.run()（注入到 LLM 调用）
- **模板文件独立于代码**：改 prompt 不需要改 Python，运营人员都能调
- **工具感知的条件渲染**：Agent 看不到它无权使用的工具描述
- **多源输入统一聚合**：产品信息、品牌调性、上游策略、用户偏好、工具描述 → 全部汇入 PromptContext → 一次渲染

#### 4.2.2 PromptContext — 统一组装点

```python
# src/prompt/context.py
from dataclasses import dataclass, field
from datetime import date
from src.tools.protocol import ToolDescription

@dataclass
class PromptContext:
    """统一的 prompt 组装上下文——所有内容来源的聚合点
    """
    # === Agent 身份 ===
    agent_name: str                        # "公众号内容创作者"
    role_instructions: str                 # 角色定义（从模板文件加载）

    # === 工具信息 ===
    tools: list[ToolDescription] = field(default_factory=list)

    # === 产品信息（来自用户输入）===
    product_name: str = ""
    product_description: str = ""
    target_users: str = ""
    key_selling_points: list[str] = field(default_factory=list)
    brand_tone: str = ""                   # 专业 / 轻松 / 极客
    competitors: list[str] = field(default_factory=list)

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
            "strategy": self.strategy,
            "other_channels": self.other_channel_contents,
            "preferences": self.user_preferences,
            "current_date": self.current_date,
        }

    def _format_tools(self) -> str:
        """将工具描述格式化为 prompt 可用的文本块"""
        if not self.tools:
            return "（无可用工具）"
        lines = []
        for t in self.tools:
            params_desc = t.parameters.get("properties", {})
            lines.append(f"- **{t.name}**: {t.description}")
            for pname, pinfo in params_desc.items():
                required = "（必填）" if pname in t.parameters.get("required", []) else ""
                lines.append(f"  - `{pname}`: {pinfo.get('description', '')}{required}")
        return "\n".join(lines)
```

#### 4.2.3 模板文件

模板存放在 `src/prompt/templates/`，使用 Jinja2 语法：

**策略 Agent 模板 (`celve.md`)**：

```markdown
你是营销策略专家，擅长分析产品定位和内容策略。

## 你的任务

根据用户提供的产品信息，制定一份内容营销策略，包括：
1. 目标用户画像（他们是谁、关心什么、在哪获取信息）
2. 核心信息提炼（一句话核心信息 + 3-5 个关键卖点）
3. 各渠道内容策略：
   - 微信公众号：深度长文，侧重行业洞察和产品价值
   - 知乎：专业知识回答，侧重技术原理和实践案例
   - 小红书：轻松种草笔记，侧重使用场景和效果展示
4. 关键词和标签建议

{% if tools %}
## 可用工具
{{ tools }}
{% endif %}

{% if preferences %}
## 用户偏好
{{ preferences }}
{% endif %}

## 规范
- 如果用户提供的信息不足以制定策略，主动追问
- 策略要具体可执行，不要空泛的"做好内容"
- 考虑当前日期 {{ current_date }} 的市场环境
```

**公众号 Agent 模板 (`gzh.md`)**：

```markdown
你是微信公众号内容创作者，擅长撰写深度长文，兼顾专业性和可读性。

## 写作风格
- 公众号深度长文，1500-3000 字
- 开头用痛点或故事引发共鸣
- 中间分段论述，每段有小标题
- 结尾呼应开头，给出行动建议
- 语言风格：{{ brand.tone }}

## 产品信息
- 产品名：{{ product.name }}
- 产品描述：{{ product.description }}
- 目标用户：{{ product.target_users }}
- 核心卖点：{{ product.key_selling_points | join("、") }}

## 内容策略
{{ strategy }}

{% if tools %}
## 可用工具
{{ tools }}
{% endif %}

## 规范
- 每个核心卖点单独一个章节展开
- 使用子标题（##）组织文章结构
- 文中自然融入 1-2 个产品使用场景
- 不要写成广告软文，要提供真实价值
- 不要编造数据，不确定的信息标注"仅供参考"
```

**知乎 Agent 模板 (`zhihu.md`)**：

```markdown
你是知乎专业领域回答者，擅长用专业知识建立权威感。

## 写作风格
- 知乎问答风格，1000-2000 字
- 开门见山给出核心观点
- 用原理、数据、案例支撑观点
- 善用列表和加粗突出重点
- 语言风格：{{ brand.tone }}，更高一些的专业度

## 产品信息
- 产品名：{{ product.name }}
- 产品描述：{{ product.description }}
- 目标用户：{{ product.target_users }}
- 核心卖点：{{ product.key_selling_points | join("、") }}

## 内容策略
{{ strategy }}

{% if tools %}
## 可用工具
{{ tools }}
{% endif %}

## 规范
- 以一个具体的技术问题或行业困惑作为引言
- 回答要有"为什么"而不仅仅是"是什么"
- 适当引用行业报告数据增强可信度（标注来源）
- 结尾引导讨论："你觉得呢？欢迎在评论区分享你的经验"
- 不要编造数据，不确定的信息标注"需要进一步验证"
```

**小红书 Agent 模板 (`xhs.md`)**：

```markdown
你是小红书内容创作者，擅长轻松种草风格，吸引目标用户关注。

## 写作风格
- 小红书笔记风格，500-1000 字
- 标题要有吸引力：emoji + 痛点/效果 + 关键词
- 正文口语化、分段短、善用 emoji
- 场景化描述：用户在使用产品前后的对比
- 语言风格：轻松、真诚，像朋友推荐

## 产品信息
- 产品名：{{ product.name }}
- 产品描述：{{ product.description }}
- 目标用户：{{ product.target_users }}
- 核心卖点：{{ product.key_selling_points | join("、") }}

## 内容策略
{{ strategy }}

{% if tools %}
## 可用工具
{{ tools }}
{% endif %}

## 规范
- 标题格式：# 小红书标题
- 正文开头直接说痛点或场景
- 每个卖点用 2-3 句话说明，不要长篇大论
- 结尾加 3-5 个相关标签
- 禁止使用"最"字级绝对化用语
- 配图建议单列一段（标注 [建议配图：xxx]）
```

**审校 Agent 模板 (`shenjiao.md`)**：

```markdown
你是品牌内容审核官，负责检查所有渠道内容的品牌一致性和质量。

## 你的任务

检查以下三篇内容的质量和一致性：

{% for channel, content in other_channels.items() %}
### {{ channel }}内容
{{ content }}{% if not loop.last %}

---
{% endif %}
{% endfor %}

## 检查清单
1. **品牌调性一致**：三篇内容的语言风格是否都符合"{{ brand.tone }}"调性？
2. **核心卖点覆盖**：{% for sp in product.key_selling_points %}"{{ sp }}"{% if not loop.last %}、{% endif %}{% endfor %}是否在三篇内容中都得到体现？
3. **目标用户匹配**：每篇内容是否针对正确的目标用户群体？
4. **事实准确性**：是否存在虚构的数据、夸大的承诺、错误的引用？
5. **渠道适配性**：每篇内容是否符合对应渠道的特点和用户习惯？

## 输出格式
对于每个检查项，给出：
- ✅ 通过 / ⚠️ 需改进 / ❌ 有问题
- 具体问题和修改建议
- 问题内容原文引用（用 > 标注）

最后给出整体评级：优秀 / 良好 / 需修改 / 不合格
```

#### 4.2.4 模板渲染器

```python
# src/prompt/renderer.py
from jinja2 import Environment, BaseLoader, TemplateNotFound
from pathlib import Path

class PromptRenderer:
    """Jinja2 模板渲染器"""

    def __init__(self, template_dir: str | None = None):
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")
        self.env = Environment(
            loader=BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template_dir = Path(template_dir)
        self._cache: dict[str, str] = {}

    def load_template(self, name: str) -> str:
        """加载模板文件（带缓存）"""
        if name not in self._cache:
            path = self.template_dir / name
            if not path.exists():
                raise FileNotFoundError(f"模板文件不存在: {path}")
            self._cache[name] = path.read_text(encoding="utf-8")
        return self._cache[name]

    def render(self, template_name_or_content: str, variables: dict) -> str:
        """渲染模板
        
        Args:
            template_name_or_content: 模板文件名或直接的模板内容
            variables: 模板变量（来自 PromptContext.to_template_vars()）
        """
        # 如果传入的是文件名（以 .md 结尾），先加载
        if template_name_or_content.endswith(".md"):
            content = self.load_template(template_name_or_content)
        else:
            content = template_name_or_content

        template = self.env.from_string(content)
        return template.render(**variables)

# 全局渲染器
renderer = PromptRenderer()
```

#### 4.2.5 Agent 中使用 Prompt 系统的示例

```python
# src/agents/gongzhonghao.py
from src.agents.base import BaseAgent
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer
from src.tools.registry import tool_registry
from src.llm.provider import LLMProvider

class GongzhonghaoAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="gongzhonghao", system_prompt="")
        self.llm = LLMProvider()

    def build_prompt_context(self, state: dict) -> PromptContext:
        """从 ProjectState 构建 PromptContext"""
        strategy = extract_upstream_content(state.get("strategy"))
        return PromptContext(
            agent_name="公众号内容创作者",
            role_instructions=renderer.load_template("gzh.md"),
            tools=tool_registry.build_descriptions(["content_save"]),
            product_name=state.get("product_name", ""),
            product_description=state.get("product_description", ""),
            target_users=state.get("target_users", ""),
            key_selling_points=state.get("key_selling_points", []),
            brand_tone=state.get("brand_tone", "专业"),
            strategy=strategy,
            user_preferences=self._get_user_preferences(state),
        )

    def run(self, state: dict) -> dict:
        ctx = self.build_prompt_context(state)

        # 渲染 system prompt（模板 + 变量 → 最终字符串）
        system_prompt = renderer.render(ctx.role_instructions, ctx.to_template_vars())

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "策略已制定，请基于策略撰写微信公众号长文。"},
        ]

        content = self.llm.chat(messages, agent_type="backend")

        return self._build_result(state, content)
```

#### 4.2.6 Prompt 系统对照

| 组件 | 本项目实现 | 说明 |
|------|-----------|------|
| `PromptContext` | `PromptContext` dataclass | 多源内容统一聚合点 |
| 模板引擎 | `PromptRenderer` (Jinja2) | 模板文件独立于代码 |
| 模板文件 | `celve.md` / `gzh.md` 等 | 改 prompt 不需要改代码 |
| 工具感知 | `{% if tools %}` Jinja2 条件 | 按 Agent 权限条件渲染模板 |
| 模板模式 | 模板文件直接包含完整 prompt | 一个文件 = 一个 agent 的完整角色定义 |

---

### 4.3 记忆系统

#### 4.3.1 短期记忆（复用，不改）

现有的 `ShortTermMemory` 设计已经很好：时间衰减 + 访问次数 boosting + 相关性分数。直接复用。

#### 4.3.2 长期记忆改造

现有表需要调整：

| 现有表 | 改为 | 用途 |
|--------|------|------|
| `projects` | `content_projects` | 记录每次生成的营销内容项目 |
| `lessons` | `brand_profiles` | 用户每个品牌的调性/卖点/目标用户，可复用 |
| `user_preferences` | 保留（字段不变） | 用户的内容风格偏好，置信度累计 |

**新增品牌档案表**：

```sql
CREATE TABLE IF NOT EXISTS brand_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                -- 品牌名称
    description TEXT,                  -- 品牌描述
    target_users TEXT,                 -- 目标用户画像
    key_selling_points TEXT,           -- 核心卖点 (JSON array)
    tone TEXT,                         -- 品牌调性
    competitors TEXT,                  -- 竞品 (JSON array)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

**新增内容项目表**：

```sql
CREATE TABLE IF NOT EXISTS content_projects (
    id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_description TEXT,
    strategy TEXT,                     -- 策略内容
    gzh_content TEXT,                  -- 公众号内容
    zhihu_content TEXT,                -- 知乎内容
    xhs_content TEXT,                  -- 小红书内容
    review_report TEXT,                -- 审校报告
    status TEXT DEFAULT 'draft',       -- draft / strategy_confirmed / generating / review / completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

**核心价值**：

用户第一次输入"推广 RAG 问答系统"需要填完整表单。第二次输入"推广 ai-dev-platform"时，系统从 `brand_profiles` 找到用户之前设置的品牌调性是"专业、技术向"，自动预填表单。**越用越省事。**

#### 4.3.3 记忆注入到 Prompt

```python
def get_brand_context(state: dict) -> str:
    """从长期记忆中提取品牌上下文，注入到 PromptContext"""
    brand_profiles = get_brand_profiles(state)
    if not brand_profiles:
        return ""

    lines = ["## 品牌档案（来自历史记录）"]
    for profile in brand_profiles[:3]:
        lines.append(f"- {profile['name']}: {profile['description'][:100]}...")
        lines.append(f"  调性: {profile['tone']}")
        lines.append(f"  卖点: {profile['key_selling_points']}")

    return "\n".join(lines)
```

---

## 五、Agent 层设计

### 5.1 Agent 基类改造

```python
# src/agents/base.py（改造后）
from abc import ABC, abstractmethod
from typing import Any
from src.prompt.context import PromptContext
from src.prompt.renderer import PromptRenderer
from src.tools.registry import ToolRegistry

class BaseAgent(ABC):
    """所有 Agent 的基类——支持工具调用和 PromptContext"""

    def __init__(
        self,
        name: str,
        system_prompt: str,           # 保留向后兼容，但新 Agent 传 ""
        tools: list[str] | None = None,  # 该 Agent 可用的工具 ID 列表
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.tool_ids = tools or []
        self.renderer = PromptRenderer()

    @abstractmethod
    def build_prompt_context(self, state: dict[str, Any]) -> PromptContext:
        """从 ProjectState 构建 PromptContext——子类必须实现"""
        pass

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 任务"""
        pass

    def build_system_prompt(self, state: dict[str, Any]) -> str:
        """构建最终 system prompt——从 PromptContext 渲染"""
        ctx = self.build_prompt_context(state)
        return self.renderer.render(ctx.role_instructions, ctx.to_template_vars())

    async def call_tool(self, tool_id: str, ctx: Any, **kwargs) -> Any:
        """调用工具——从 ToolRegistry 查找并执行"""
        from src.tools.registry import tool_registry
        tool = tool_registry.get(tool_id)
        if tool is None:
            raise ValueError(f"工具不存在: {tool_id}")
        if tool_id not in self.tool_ids:
            raise PermissionError(f"Agent {self.name} 无权使用工具: {tool_id}")
        return await tool.execute(ctx, **kwargs)
```

### 5.2 策略 Agent

| 属性 | 值 |
|------|-----|
| name | `celve` |
| model | DeepSeek V4 |
| 工具 | `web_search` |
| 输入 | 产品名称、产品描述、目标用户、核心卖点、品牌调性、竞品 |
| 输出 | 内容策略（目标用户画像 + 核心信息 + 各渠道策略 + 关键词） |
| 行为 | 信息不足时主动追问用户（复用 RequirementAgent 的 ASK_USER 机制） |

### 5.3 公众号 Agent

| 属性 | 值 |
|------|-----|
| name | `gongzhonghao` |
| model | DeepSeek V4 |
| 工具 | `content_save` |
| 输入 | 产品信息 + 品牌调性 + 策略 |
| 输出 | 1500-3000 字微信公众号长文（Markdown 格式） |
| 风格 | 深度长文，痛点引入 → 章节展开 → 行动建议 |

### 5.4 知乎 Agent

| 属性 | 值 |
|------|-----|
| name | `zhihu` |
| model | DeepSeek V4 |
| 工具 | `content_save` |
| 输入 | 产品信息 + 品牌调性 + 策略 |
| 输出 | 1000-2000 字知乎专业回答（Markdown 格式） |
| 风格 | 开门见山 → 原理/数据/案例 → 互动结尾 |

### 5.5 小红书 Agent

| 属性 | 值 |
|------|-----|
| name | `xiaohongshu` |
| model | MiniMax 2.7 |
| 工具 | `content_save` |
| 输入 | 产品信息 + 品牌调性 + 策略 |
| 输出 | 500-1000 字小红书种草笔记（含标签） |
| 风格 | 口语化、场景化、轻松种草 |

### 5.6 审校 Agent

| 属性 | 值 |
|------|-----|
| name | `shenjiao` |
| model | MiniMax 2.7 |
| 工具 | `content_read`、`brand_guideline_query` (P1) |
| 输入 | 三篇渠道内容 + 品牌调性 + 核心卖点 |
| 输出 | 审校报告（五项检查清单 + 问题标注 + 修改建议 + 整体评级） |
| 检查项 | 品牌调性一致、核心卖点覆盖、目标用户匹配、事实准确性、渠道适配性 |

### 5.7 导出 Agent

| 属性 | 值 |
|------|-----|
| name | `export` |
| model | 无需 LLM |
| 工具 | `content_list`、`content_read` |
| 输入 | 审校后的三篇内容 + 策略 |
| 输出 | 一键导出为 Markdown 文件 / 复制到剪贴板 |

#### 5.7.1 导出方式对比

| 方式 | 适用场景 | 实现难度 |
|------|---------|:--:|
| 复制到剪贴板 | 用户手动粘贴到公众号后台/知乎编辑器 | 低 |
| 下载 Markdown 文件 | 存档、二次编辑 | 低 |
| 直接发布 API（P2） | 自动发布到微信公众号/知乎 | 高（需各平台授权） |

MVP 阶段先支持**复制到剪贴板 + 下载 Markdown**。

---

## 六、编排流程

### 6.1 LangGraph 状态图

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │   策略      │ ← 可追问用户
                    │   Agent     │
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                 ┌──┤ 用户确认？  │
                 │  └─────────────┘
                 │ ask          │ continue
                 ↓              ↓
              ┌─────┐   ┌───────┴───────┐
              │ END │   │   并行生成      │
              └─────┘   │ ┌─────┐┌─────┐│
                        │ │公众号││知乎 ││┌─────┐│
                        │ │Agent││Agent│││小红书││
                        │ └──┬──┘└──┬──┘││Agent││
                        └────┼─────┼───┘└──┬──┘│
                             ↓     ↓        ↓
                        ┌─────────────────────┐
                        │      审校 Agent      │ ← 所有内容到齐后执行
                        └──────────┬──────────┘
                                   ↓
                        ┌─────────────────────┐
                        │      导出 Agent      │
                        └──────────┬──────────┘
                                   ↓
                              ┌─────────┐
                              │   END   │
                              └─────────┘
```

### 6.2 与现有代码的差异

```python
# 新的 src/orchestrator/graph.py
def create_content_graph(agents: dict[str, Any]) -> Any:
    graph = StateGraph(ContentProjectState)

    graph.add_node("celve", agents["celve"].run)
    graph.add_node("gongzhonghao", agents["gongzhonghao"].run)
    graph.add_node("zhihu", agents["zhihu"].run)
    graph.add_node("xiaohongshu", agents["xiaohongshu"].run)
    graph.add_node("shenjiao", agents["shenjiao"].run)
    graph.add_node("export", agents["export"].run)

    graph.set_entry_point("celve")

    # 策略 → 确认或继续
    graph.add_conditional_edges(
        "celve",
        _route_after_celve,
        {"ask_user": END, "continue": "gongzhonghao"},
    )

    # 三路并行（关键！）
    # 从策略确认后，同时分发到三个渠道 Agent
    graph.add_edge("celve", "gongzhonghao")  # 条件路由为 "continue" 时
    graph.add_edge("celve", "zhihu")          # 需要改为 fan-out
    graph.add_edge("celve", "xiaohongshu")

    # 三个都完成后，汇聚到审校
    graph.add_edge("gongzhonghao", "shenjiao")
    graph.add_edge("zhihu", "shenjiao")
    graph.add_edge("xiaohongshu", "shenjiao")

    # 审校 → 导出 → 结束
    graph.add_edge("shenjiao", "export")
    graph.add_edge("export", END)

    return graph.compile()
```

**注意**：LangGraph 中 `add_edge(A, B)` 和 `add_edge(A, C)` 不会自动并行。需要使用 `Send` API 实现 fan-out。这是改造时需要注意的技术细节。

### 6.3 共享状态

```python
# src/orchestrator/state.py
class Stage(str, Enum):
    STRATEGY = "strategy"
    GENERATING = "generating"
    REVIEW = "review"
    DONE = "done"
    ERROR = "error"

class ContentProjectState(TypedDict):
    """营销内容项目的共享状态"""

    # === 用户输入 ===
    input_mode: str                    # "form" | "free"
    product_name: str
    product_description: str
    target_users: str
    key_selling_points: list[str]
    brand_tone: str
    competitors: list[str]
    user_idea: str                     # 自由模式下用户直接输入的完整描述

    # === Agent 产出 ===
    strategy: OutputArtifact | None    # 策略
    gzh_content: OutputArtifact | None # 公众号内容
    zhihu_content: OutputArtifact | None # 知乎内容
    xhs_content: OutputArtifact | None # 小红书内容
    review_report: OutputArtifact | None # 审校报告

    # === 状态管理 ===
    current_stage: Stage
    error_message: str | None
    ask_user: str | None               # 策略 Agent 追问用户的问题
    messages: list[dict]               # WebSocket 推送消息
    
    # === 记忆 ===
    short_term_memory: dict | None
    long_term_memory_path: str | None
    brand_profile_id: str | None       # 关联的品牌档案
```

---

## 七、数据模型

### 7.1 用户输入表单（引导模式）

```python
@dataclass
class ContentFormInput:
    product_name: str                  # 产品名称 *
    product_description: str           # 一句话描述 *
    target_users: str                  # 目标用户 *
    key_selling_points: list[str]      # 核心卖点（3-5个）*
    brand_tone: str                    # 品牌调性：专业 / 轻松 / 极客 *
    competitors: list[str]             # 竞品名称（可选）
    additional_notes: str              # 补充说明（可选）
```

### 7.2 API 请求/响应

```python
# 创建项目请求
class CreateProjectRequest(BaseModel):
    mode: str = "form"                 # "form" | "free"
    # 表单模式字段
    product_name: str | None = None
    product_description: str | None = None
    target_users: str | None = None
    key_selling_points: list[str] | None = None
    brand_tone: str | None = None
    competitors: list[str] | None = None
    # 自由模式字段
    user_idea: str | None = None

# 策略确认请求
class ConfirmStrategyRequest(BaseModel):
    project_id: str
    confirmed: bool                    # True=继续，False=需要修改
    feedback: str | None = None        # 修改意见

# 项目状态响应
class ProjectStatusResponse(BaseModel):
    project_id: str
    stage: str
    strategy: dict | None
    contents: dict[str, dict | None]   # {"gzh": ..., "zhihu": ..., "xhs": ...}
    review_report: dict | None
    created_at: str
    updated_at: str
```

---

## 八、API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/content-projects` | 创建营销内容项目（表单/自由模式） |
| GET | `/api/v1/content-projects/{id}` | 查询项目状态和所有产出 |
| POST | `/api/v1/content-projects/{id}/confirm-strategy` | 确认/修改策略 |
| GET | `/api/v1/content-projects/{id}/content/{channel}` | 获取指定渠道内容 |
| GET | `/api/v1/content-projects/{id}/export` | 导出全部内容（Markdown） |
| GET | `/api/v1/content-projects/{id}/review` | 获取审校报告 |
| WS | `/ws` | WebSocket 实时推送 Agent 执行进度 |
| POST | `/api/v1/brand-profiles` | 保存品牌档案 |
| GET | `/api/v1/brand-profiles` | 查询已有品牌档案（表单预填） |

---

## 九、前端设计

### 9.1 页面流程

```
引导式表单（默认）     ←→  自由模式（一键切换）
    ↓                          ↓
    [提交]
    ↓
策略展示页面（可追问确认/修改）
    ↓ [确认]
等待生成页面（三个渠道并行，WebSocket 实时进度）
    ↓
内容预览页面
├── 公众号 Tab
├── 知乎 Tab
├── 小红书 Tab
└── 审校报告 Tab
    ↓
导出页面（复制 / 下载 Markdown）
```

### 9.2 表单页设计

```
┌─────────────────────────────────────────────────┐
│  创建营销内容                   [自由模式 ▸]     │
│                                                  │
│  产品名称 *                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ RAG 智能问答系统                          │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  一句话描述 *                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ 企业级知识库问答助手，上传文档即用         │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  目标用户 *                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ 技术团队负责人、CTO、技术总监              │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  核心卖点 *（3-5个）                             │
│  ┌──────────────────────────────────────────┐   │
│  │ + 多格式文档支持                          │   │
│  │ + 引用可追溯                              │   │
│  │ + 安全防护（Prompt注入检测）               │   │
│  │ + 管理后台（Vue3）                        │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  品牌调性 *    ○ 专业  ● 轻松  ○ 极客           │
│                                                  │
│  竞品名称（可选）                                │
│  ┌──────────────────────────────────────────┐   │
│  │ ChatPDF、AnythingLLM                      │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  [从品牌档案加载 ▾]            [提交 →]          │
└─────────────────────────────────────────────────┘
```

### 9.3 策略确认页设计

```
┌─────────────────────────────────────────────────┐
│  📋 内容策略                         [修改 →]     │
│                                                  │
│  ## 目标用户画像                                 │
│  技术团队负责人（30-45岁），关注团队效率和        │
│  技术选型，主要信息获取渠道：知乎、技术博客...    │
│                                                  │
│  ## 核心信息                                     │
│  "让团队知识不再沉睡——一键部署的企业级 RAG 问答"  │
│                                                  │
│  ## 各渠道策略                                   │
│  - 公众号：深度解读 RAG 技术趋势 + 产品价值       │
│  - 知乎：回答"自建RAG vs 开源方案怎么选"         │
│  - 小红书：碎片化知识管理痛点 + 使用场景          │
│                                                  │
│  ✅ 确认策略，开始生成内容                        │
│  📝 我要修改（输入反馈）                          │
└─────────────────────────────────────────────────┘
```

### 9.4 内容预览页设计

```
┌─────────────────────────────────────────────────┐
│  [公众号] [知乎] [小红书] [审校报告]              │
│                                                  │
│  # RAG技术选型指南：为什么企业需要自己的          │
│  # 知识库问答系统                                │
│                                                  │
│  ## 2026年，知识管理不再是"建个Wiki"              │
│  过去十年，企业知识管理的标准答案是"建个Wiki"...  │
│                                                  │
│  ## 什么是RAG？为什么它是AI时代的答案            │
│  RAG（检索增强生成）的核心思路很简单...           │
│                                                  │
│  ## 三个关键选择：自建 vs 开源 vs SaaS            │
│  ...                                            │
│                                                  │
│  [📋 复制内容] [📥 下载 Markdown] [🔄 重新生成]  │
└─────────────────────────────────────────────────┘
```

---

## 十、改造实施计划

### Phase 1：子系统层搭建（1-2 天）

**目标**：工具系统 + Prompt 系统 + 记忆系统改造完成，可独立测试。

1. 创建 `src/tools/protocol.py` — Tool 协议定义
2. 创建 `src/tools/registry.py` — 单例注册表
3. 实现 MVP 工具 — `web_search`、`content_save`、`content_read`、`content_list`
4. 创建 `src/prompt/templates/*.md` — 五个模板文件
5. 创建 `src/prompt/context.py` — PromptContext 数据类
6. 创建 `src/prompt/renderer.py` — Jinja2 渲染器
7. 改造 `src/orchestrator/long_term_memory.py` — 新增 brand_profiles 和 content_projects 表
8. 改造 `src/agents/base.py` — 支持工具调用和 PromptContext

**验证标准**：
- ToolRegistry 可注册和查询工具
- PromptRenderer 可用模板 + 变量渲染出完整的 system prompt
- 长期记忆可读写品牌档案

### Phase 2：Agent 实现（1-2 天）

**目标**：6 个 Agent 实现完成，可独立测试。

1. 实现策略 Agent — 含 ASK_USER 追问逻辑
2. 实现公众号 Agent — 含 content_save 工具调用
3. 实现知乎 Agent
4. 实现小红书 Agent — MiniMax 模型
5. 实现审校 Agent — 五项检查清单
6. 实现导出 Agent — 复制 + 下载

**验证标准**：
- 每个 Agent 可独立调用，输入 mock 状态，输出正确格式内容
- 策略 Agent 信息不足时正确触发追问

### Phase 3：编排 + API（1-2 天）

**目标**：LangGraph 编排完成 + FastAPI 接口就绪。

1. 改造 `src/orchestrator/graph.py` — 新的 content graph
2. 改造 `src/orchestrator/state.py` — ContentProjectState
3. 新增 API 路由 — content-projects + brand-profiles
4. WebSocket 推送 Agent 进度

**验证标准**：
- 提交表单 → 策略生成 → 确认 → 三路并行生成 → 审校 → 导出，全流程走通
- API 可查询每个步骤的状态和中间产出

### Phase 4：前端（2-3 天）

**目标**：Vue 3 前端完整可用。

1. 引导式表单页面（含自由模式切换）
2. 策略确认页面
3. 内容预览页面（Tab 切换 + 审校报告）
4. 导出功能（复制 + 下载）
5. WebSocket 实时进度显示
6. 品牌档案加载/保存

**验证标准**：
- 浏览器可走完整流程
- WebSocket 进度实时更新
- 复制和下载功能正常

---

## 附录 A：设计理念对照总表

| 设计理念 | 本项目实现 |
|---------|-----------|
| 执行/描述分离 | `Tool` Protocol + `ToolDescription` dataclass |
| 统一上下文注入 | `ToolContext` |
| Builder + 注册表 | `ToolRegistry.register().build_descriptions()` |
| 工具感知模板 | `{% if tools %}` Jinja2 条件 |
| PromptContext 多源聚合 | `PromptContext` dataclass |
| 模板文件独立 | 明文 .md 文件 |
| 品牌档案记忆 | `brand_profiles` table |
| 工具后处理提醒 | `ToolResult.system_reminder` |
| 多模型路由 | `LLMProvider.MODEL_MAP` |

## 附录 B：文件变更清单

```
新增文件：
  src/tools/__init__.py
  src/tools/protocol.py
  src/tools/registry.py
  src/tools/implementations/__init__.py
  src/tools/implementations/web_search.py
  src/tools/implementations/content_io.py
  src/prompt/__init__.py
  src/prompt/context.py
  src/prompt/renderer.py
  src/prompt/templates/celve.md
  src/prompt/templates/gzh.md
  src/prompt/templates/zhihu.md
  src/prompt/templates/xhs.md
  src/prompt/templates/shenjiao.md
  src/agents/celve.py
  src/agents/gongzhonghao.py
  src/agents/zhihu.py
  src/agents/xiaohongshu.py
  src/agents/shenjiao.py
  src/agents/export.py

改造文件：
  src/agents/base.py        ← 支持工具调用 + PromptContext
  src/orchestrator/graph.py  ← 新的 content graph
  src/orchestrator/state.py  ← ContentProjectState
  src/orchestrator/long_term_memory.py ← brand_profiles + content_projects 表
  src/llm/provider.py        ← 加 chat_with_tools 方法（可选）
  src/web/server.py          ← 新 API 路由

移除文件：
  src/agents/architect.py
  src/agents/backend.py
  src/agents/frontend.py
  src/orchestrator/preview.py（如有）
  src/llm/prompts/requirement.py（改为动态模板）
```

---

> **设计完成。** 本设计覆盖了工具系统（Tool 协议 + 注册表）、Prompt 系统（PromptContext + 模板渲染）、记忆系统（品牌档案 + 内容项目）三大核心子系统的改进方案，以及具体的 4 阶段实施计划。
