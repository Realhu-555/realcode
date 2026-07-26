# 素宣 Suxuan — 营销内容多 Agent 平台

> *一张白宣铺开，AI 蘸墨，写出千万种可能。*

基于 LangGraph 的营销内容自动化生成平台。用户输入产品信息，系统通过 **6 个协作 AI Agent** 自动完成**策略分析 → 三渠道并行生成（公众号/知乎/小红书）→ 审校**全流程。

## 核心流程

```
用户输入产品信息（引导表单 / 自由文本）
    ↓
┌─────────────┐
│   策略 Agent  │ ← 分析产品 → 输出内容策略 → 用户确认
│  (DeepSeek)  │
└──────┬──────┘
       ↓
┌───┴───┬───────┬──────────┐
│  公众号  │  知乎   │  小红书    │ ← 三路并行生成
│ Agent   │ Agent  │  Agent    │   公众号→DeepSeek
│ 深度长文  │ 专业回答 │ 种草笔记   │   知乎→DeepSeek
└───┬───┴───┬───┴────┬─────┘   小红书→MiniMax
    ↓       ↓        ↓
┌─────────────────────────┐
│      审校 Agent          │ ← 五项检查（调性/卖点/用户/事实/渠道）
│      (MiniMax)           │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│      导出                │ ← 复制到剪贴板 / 下载 Markdown
└─────────────────────────┘
```

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 编排框架 | **LangGraph** | StateGraph 驱动的 Agent 编排，支持条件分支 + 并行执行 |
| LLM | DeepSeek V4 + MiniMax 2.7 | **多模型智能路由**：深度内容→DeepSeek，轻松内容→MiniMax |
| 子系统 | 工具系统 / Prompt 系统 / 记忆系统 | 执行/描述分离 + Jinja2 模板化 + SQLite 品牌档案 |
| 后端 | Python 3.12+、FastAPI、WebSocket | 异步 API + 实时进度推送 |
| 前端 | Vue 3 + TypeScript + Naive UI + UnoCSS | 暗/亮双主题 SPA |
| 记忆 | SQLite | 品牌档案持久化 + 项目历史 |
| 部署 | Docker | 容器化部署 |

## 架构设计亮点

### 1. 工具系统 — 执行/描述分离

```python
# Tool 协议：给 AI 看的描述和执行逻辑完全分离
ToolDescription(name, description, parameters)  # 注入 system prompt
Tool.execute(ctx, **kwargs)                     # 实际逻辑

# 单例注册表 + Builder 模式
tool_registry.register(WebSearchTool()).register(ContentSaveTool())

# 按 Agent 权限过滤：Agent 看不到它无权使用的工具
tool_registry.build_descriptions(["content_save"])  # 策略 Agent 看不到这个
```

### 2. Prompt 系统 — 三阶段分离

```
PromptContext（纯数据）  →  TemplateRenderer（Jinja2 渲染）  →  Agent.run()（注入 LLM）
产品信息 + 策略 + 工具描述 + 品牌偏好   模板文件独立于代码        最终 system prompt
```

模板文件独立于 Python 代码，改 prompt 不需要改源码。

### 3. 多 Agent 编排 — LangGraph 状态图

四个判断标准全部满足，是真正的多 Agent 场景：
- ✅ **不同的 System Prompt**：公众号深度长文 / 知乎专业知识 / 小红书轻松种草
- ✅ **不同的工具集**：策略 Agent 有 web_search，审校 Agent 有 content_read
- ✅ **并行执行**：三渠道同时生成，总耗时 = max(三路) 而非 sum
- ✅ **不同的模型**：DeepSeek（深度内容）vs MiniMax（轻松内容 + 审校）

### 4. 记忆系统 — 品牌档案

用户第一次推广"A 产品"填完整表单。第二次推广"B 产品"时，系统自动检索已有品牌档案，预填调性和偏好。越用越省事。

## 项目结构

```
ai-dev-platform/
├── frontend/                # Vue 3 前端（SPA）
│   └── src/
│       ├── views/           # 3 个页面：创建/策略确认/内容预览
│       ├── components/      # 8 个组件：表单/策略卡/内容面板/进度时间线...
│       ├── stores/          # Pinia 状态管理
│       ├── composables/     # 可组合函数（useTheme/useExport/useAgentProgress）
│       └── api/             # Axios 客户端 + API 类型定义
├── src/
│   ├── agents/              # Agent 层（6 个 Agent）
│   │   └── base.py          # Agent 基类（支持工具调用 + PromptContext）
│   ├── tools/               # 工具系统
│   │   ├── protocol.py      # Tool/Description/Context/Result 协议
│   │   ├── registry.py      # 单例注册表（Builder 模式）
│   │   └── implementations/ # web_search / content_io
│   ├── prompt/              # Prompt 系统
│   │   ├── context.py       # PromptContext 多源数据组装
│   │   ├── renderer.py      # Jinja2 模板渲染器
│   │   └── templates/       # 5 个 Agent 模板（.md 文件）
│   ├── orchestrator/        # 编排层
│   │   ├── graph.py         # LangGraph 状态图
│   │   ├── state.py         # ContentProjectState 共享状态
│   │   └── long_term_memory.py  # 长期记忆（SQLite）
│   ├── llm/                 # LLM 调用层
│   │   ├── provider.py      # 统一 LLM Provider（多模型路由）
│   │   └── prompts/         # 历史 Prompt（逐步迁移到 src/prompt/）
│   ├── sandbox/             # 代码执行沙箱
│   ├── web/                 # FastAPI Web 服务
│   └── utils/               # 配置、日志、健康检查
├── tests/                   # 测试代码
├── docs/                    # 设计文档
│   └── 营销内容多Agent平台-系统设计.md
└── .env                     # API Key（不入 git）
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/Realhu-555/realcode.git
cd ai-dev-platform

# --- 后端 ---
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入 DeepSeek 和 MiniMax API Key

# 启动后端
python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8080 --reload

# --- 前端 ---
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/content-projects` | 创建营销内容项目（表单/自由模式） |
| GET | `/api/v1/content-projects/{id}` | 查询项目状态和所有产出 |
| POST | `/api/v1/content-projects/{id}/confirm-strategy` | 确认/修改策略 |
| GET | `/api/v1/content-projects/{id}/content/{channel}` | 获取指定渠道内容 |
| GET | `/api/v1/content-projects/{id}/review` | 获取审校报告 |
| GET | `/api/v1/content-projects/{id}/export` | 导出全部内容（Markdown） |
| POST | `/api/v1/brand-profiles` | 保存品牌档案 |
| GET | `/api/v1/brand-profiles` | 查询已有品牌档案 |
| WS | `/ws` | WebSocket 实时推送 Agent 执行进度 |

## 实施进度

- [x] Phase 1：子系统层 — 工具系统 + Prompt 系统 + 记忆系统 + Agent 基类改造
- [ ] Phase 2：Agent 实现 — 6 个 Agent（策略/公众号/知乎/小红书/审校/导出）
- [ ] Phase 3：编排 + API — LangGraph 集成 + FastAPI 路由 + WebSocket 进度推送
- [x] Phase 4：前端 — Vue 3 SPA 完整可用（创建/策略确认/内容预览）

## License

MIT
