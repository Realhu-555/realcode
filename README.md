# AI Dev Platform — 多 Agent 智能开发流水线

基于 LangGraph 的自动化软件开发平台。用户输入自然语言需求，系统通过 6 个分工协作的 AI Agent 自动完成**需求分析 → 架构设计 → 代码生成 → 测试 → 部署**全流程。

## 核心架构

```
用户输入想法
    ↓
┌─────────────┐
│  Requirement │ ← 需求分析 Agent（可追问用户补充细节）
│    Agent     │
└──────┬──────┘
       ↓
┌─────────────┐
│  Architect   │ ← 架构设计 Agent（输出技术方案）
│    Agent     │
└──┬───────┬──┘
   ↓       ↓
┌──────┐ ┌──────┐
│Backend│ │Frontend│ ← 并行开发（后端 + 前端）
│Agent  │ │Agent   │
└──┬───┘ └──┬───┘
   ↓        ↓
┌─────────────┐
│   Tester    │ ← 测试 Agent（生成测试用例 + 执行）
│    Agent    │
└──────┬──────┘
       ↓
┌─────────────┐
│  Deployer   │ ← 部署 Agent（打包 + 输出可下载产物）
│    Agent    │
└─────────────┘
```

## 技术栈

- **编排框架**: LangGraph（状态图驱动的 Agent 编排）
- **LLM**: DeepSeek V4（推理/代码生成）+ MiniMax 2.7（文档/测试）多模型智能路由
- **后端**: Python 3.12+、FastAPI、WebSocket
- **前端**: Vue 3 + TypeScript + Element Plus
- **沙箱**: 本地代码执行沙箱（安全隔离）
- **部署**: Docker

## 项目亮点

### 1. 多模型智能路由
按任务场景动态分配模型——推理密集型用 DeepSeek（架构设计、代码生成），中文对话型用 MiniMax（需求理解、文档生成），平衡成本与质量。

### 2. LangGraph 状态图编排
用 LangGraph 的 StateGraph 管理 6 个 Agent 的执行流程。支持条件分支（需求分析后可追问用户）、并行执行（前后端同时开发）、状态持久化。

### 3. 共享状态架构
所有 Agent 读写同一个 ProjectState（TypedDict），包含需求文档、技术方案、代码、测试报告等。信息在 Agent 间自动流转，不存在信息孤岛。

### 4. 安全沙箱
代码在隔离的本地沙箱中执行，限制文件系统访问和网络权限。

## 项目结构

```
ai-dev-platform/
├── src/
│   ├── agents/          # 6 个专职 Agent
│   │   ├── base.py      # Agent 抽象基类
│   │   ├── requirement.py   # 需求分析
│   │   ├── architect.py     # 架构设计
│   │   ├── backend.py       # 后端代码生成
│   │   ├── frontend.py      # 前端代码生成
│   │   ├── tester.py        # 测试用例生成
│   │   └── deployer.py      # 打包部署
│   ├── orchestrator/    # 编排层
│   │   ├── graph.py     # LangGraph 状态图
│   │   └── state.py     # 共享状态定义（ProjectState）
│   ├── llm/             # LLM 调用层
│   │   ├── provider.py  # 统一 LLM Provider（多模型路由）
│   │   └── prompts/     # 各 Agent 的 Prompt 模板
│   ├── sandbox/         # 代码执行沙箱
│   ├── web/             # FastAPI Web 服务
│   └── utils/           # 配置、日志、健康检查
├── tests/               # 测试代码
├── docs/                # 项目文档
├── pyproject.toml       # 项目配置
└── .env                 # API Key（不入 git）
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/Realhu-555/ai-dev-platform.git
cd ai-dev-platform

# 安装依赖
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 DeepSeek 和 MiniMax API Key

# 启动服务
python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8080 --reload

# 访问 http://localhost:8080
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/projects | 提交项目需求（自然语言描述） |
| GET  | /api/v1/projects/{id} | 查询项目状态和中间产出 |
| GET  | /api/v1/projects/{id}/prd | 获取需求文档（PRD） |
| GET  | /api/v1/projects/{id}/tech-plan | 获取技术方案 |
| GET  | /api/v1/projects/{id}/code | 获取生成的代码 |
| GET  | /api/v1/projects/{id}/test-report | 获取测试报告 |
| GET  | /api/v1/projects/{id}/download | 下载打包产物 |
| WS   | /ws | WebSocket 实时推送 Agent 执行进度 |

## 技术文档

- [技术架构文档](docs/AI_Dev_Platform_技术文档.md)

## License

MIT
