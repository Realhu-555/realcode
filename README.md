# 素宣 Suxuan — 营销内容多 Agent 平台

> *一张白宣铺开，AI 蘸墨，写出千万种可能。*

基于 LangGraph 的营销内容自动化生成平台。用户输入产品信息，系统通过 **6 个协作 AI Agent** 自动完成 **策略分析 → 三渠道并行生成（公众号/知乎/小红书）→ 审校 → 导出**全流程。

## 核心流程

```
用户输入（表单/自由文本 + 可选图片）
    ↓
┌──────────────────────┐
│   策略 Agent           │ ← 分析产品 + 图片 → 输出策略 → 用户确认
│   (DeepSeek V4)        │    信息不足时主动追问
└──────┬───────────────┘
       ↓
┌───┴───┬───────┬──────────┐
│  公众号  │  知乎   │  小红书    │ ← 三路并行生成（全 DeepSeek V4）
│  深度长文  │ 专业回答 │ 种草笔记   │
│ 1500-3000 │1000-2000│ 500-1000  │
└───┬───┴───┬───┴────┬─────┘
    ↓       ↓        ↓
┌─────────────────────────┐
│      审校 Agent          │ ← 五项检查清单（调性/卖点/用户/事实/渠道适配）
│      (DeepSeek V4)       │    输出整体评级 + 逐项改进建议
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│      导出                │ ← Markdown 一键导出 / 复制
└─────────────────────────┘
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 编排框架 | **LangGraph** — StateGraph 驱动，条件分支 + 并行 fan-out |
| LLM | **DeepSeek V4** — 全部 Agent 统一模型 |
| 视觉理解 | **MiMo V2.5**（小米）— 图片→文字描述，注入策略分析 |
| 工具系统 | execution/description 分离 + 单例注册表 + Builder 模式 |
| Prompt 系统 | **Jinja2 模板化** — 模板文件独立于代码，改 prompt 不碰源码 |
| 后端 | Python 3.12+ / FastAPI / WebSocket |
| 前端 | Vue 3 + TypeScript + Naive UI + UnoCSS |
| 记忆 | SQLite — 品牌档案 + 项目历史 |

## 架构亮点

### 1. 工具系统

Tool 协议把 **给 AI 看的描述** 和 **实际执行逻辑** 完全分离，Agent 只能看到它有权限使用的工具。

### 2. Prompt 系统

三阶段分离：`PromptContext`（纯数据组装）→ `TemplateRenderer`（Jinja2 渲染）→ `Agent.run()`（注入 LLM）。模板文件是 `.md` 明文，运营也能调。

### 3. 多模态视觉

用户上传产品截图 → MiMo V2.5 图片理解 → 文字描述注入策略分析。视觉模型和推理模型各司其职，不给纯文本模型塞图片。

### 4. 多 Agent 编排

四项条件全部满足，是真正的多 Agent 场景：
- ✅ 不同 System Prompt：公众号深度长文 / 知乎专业知识 / 小红书轻松种草
- ✅ 不同工具集：策略 Agent 有 web_search，渠道 Agent 有 content_save，审校 Agent 有 content_read
- ✅ 并行执行：三渠道同时生成，总耗时 = max(三路)
- ✅ 不同模型需求：可灵活切换（当前全部 DeepSeek V4）

## 项目结构

```
ai-dev-platform/
├── frontend/                 # Vue 3 前端
│   └── src/
│       ├── views/            # 3 个页面：创建/策略确认/内容预览
│       ├── components/       # 8 个组件
│       ├── stores/           # Pinia 状态管理
│       ├── composables/      # 可组合函数（useTheme/useExport/useImageUpload...）
│       └── api/              # Axios 客户端
├── src/
│   ├── agents/               # 6 个业务 Agent
│   │   ├── celve.py          #   策略分析（ASK_USER 追问）
│   │   ├── gongzhonghao.py   #   公众号长文
│   │   ├── zhihu.py          #   知乎回答
│   │   ├── xiaohongshu.py    #   小红书笔记
│   │   ├── shenjiao.py       #   审校报告
│   │   └── export.py         #   Markdown 导出
│   ├── tools/                # 工具系统
│   │   ├── protocol.py       #   Tool/Description/Context/Result 协议
│   │   ├── registry.py       #   单例注册表
│   │   └── implementations/  #   web_search / content_io
│   ├── prompt/               # Prompt 系统
│   │   ├── context.py        #   PromptContext 多源数据组装
│   │   ├── renderer.py       #   Jinja2 模板渲染器
│   │   └── templates/        #   5 个 Agent 模板（.md）
│   ├── vision/               # 多模态视觉理解（MiMo V2.5）
│   ├── orchestrator/         # 编排层
│   │   ├── graph.py          #   LangGraph 状态图
│   │   ├── state.py          #   ContentProjectState
│   │   └── long_term_memory.py # 长期记忆（SQLite）
│   ├── llm/provider.py       # 统一 LLM Provider
│   ├── web/server.py         # FastAPI Web 服务
│   └── utils/                # 配置/日志/健康检查
├── tests/
├── docs/
│   └── 营销内容多Agent平台-系统设计.md
└── .env                      # API Key（不入 git）
```

## 快速开始

```bash
git clone https://github.com/Realhu-555/realcode.git
cd ai-dev-platform

# 后端
pip install -e ".[dev]"
echo "DEEPSEEK_API_KEY=sk-..." >> .env    # 必须
echo "MIMO_API_KEY=sk-..." >> .env        # 可选（图片理解）
python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8080 --reload

# 前端
cd frontend && npm install && npm run dev
# → http://localhost:5173
```

> **没有 API Key？** 前端内置 mock 数据，打开 http://localhost:5173 填表单提交即可看到完整效果。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/content-projects` | 创建项目（表单/自由模式 + 可选图片） |
| GET | `/api/v1/content-projects/{id}` | 查询项目状态和所有产出 |
| POST | `/api/v1/content-projects/{id}/confirm-strategy` | 确认/修改策略 |
| GET | `/api/v1/content-projects/{id}/content/{channel}` | 获取渠道内容 |
| GET | `/api/v1/content-projects/{id}/review` | 获取审校报告 |
| GET | `/api/v1/content-projects/{id}/export` | 导出 Markdown |

## License

MIT
