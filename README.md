# AI Dev Platform

多 Agent 协作的全自动 Web 应用开发平台。用户用自然语言描述想法，系统自动完成需求分析→架构设计→代码生成→测试→打包。

## 快速开始

### 环境要求

- Python 3.12+
- Docker（可选，用于沙箱执行）

### 安装

```bash
git clone <repo-url>
cd ai-dev-platform

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 填写 API Keys
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率
pytest tests/ -v --cov=src --cov-report=html

# 仅运行单元测试（快速）
pytest tests/ -v -k "not (deployer or frontend or tester)"
```

### 代码检查

```bash
# Lint 检查
ruff check src/ tests/

# 格式检查
ruff format --check src/ tests/

# 类型检查
mypy src/ --ignore-missing-imports

# 一键检查（推荐）
pre-commit run --all-files
```

### 启动 Web 服务

```bash
uvicorn src.web.server:app --reload --host 0.0.0.0 --port 8080
```

## 项目结构

```
ai-dev-platform/
├── src/
│   ├── orchestrator/    # 调度中心（LangGraph 状态图）
│   ├── agents/          # 各专职 Agent
│   ├── sandbox/         # 代码执行沙箱
│   ├── llm/             # LLM Provider + Prompts
│   ├── web/             # Web 界面
│   └── utils/           # 配置、日志、工具
├── tests/               # 测试代码
├── docs/                # 文档
├── pyproject.toml       # 项目配置
└── docker-compose.yml   # Docker 服务
```

## Agent 角色

| Agent | 模型 | 职责 |
|-------|------|------|
| RequirementAgent | MiniMax 2.7 | 需求分析、追问澄清 |
| ArchitectAgent | DeepSeek V4 | 技术架构设计 |
| BackendAgent | DeepSeek V4 | 后端代码生成 |
| FrontendAgent | MiniMax 2.7 | 前端代码生成 |
| TesterAgent | MiniMax 2.7 | 测试验证 |
| DeployerAgent | MiniMax 2.7 | 打包部署 |

## Docker 使用

```bash
# 运行测试
docker compose run test

# 启动 Web 服务（开发）
docker compose up web

# 生产环境
docker compose up production
```

## 开发规范

详见 [CLAUDE.md](CLAUDE.md)

- 代码风格：Ruff + MyPy
- 提交规范：`<type>(<scope>): <description>`
- 测试要求：核心模块覆盖率 ≥70%

## License

MIT
