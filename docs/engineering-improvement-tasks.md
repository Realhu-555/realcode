# AI Dev Platform — 工程化改进任务书

> **版本**: v1.0
> **创建日期**: 2026-06-06
> **目标**: 将当前 MVP 项目提升至生产级工程化水平

---

## 一、改进目标

| 目标 | 指标 |
|------|------|
| 代码质量 | ruff/mypy 零报错 |
| 测试覆盖 | 核心模块 ≥70% |
| CI 自动化 | push/PR 自动触发测试+lint |
| 环境可复现 | 任何机器 `pip install -e ".[dev]"` 即可开发 |
| 安全性 | 沙箱隔离执行代码 |

---

## 二、任务清单

### 阶段 1：基础规范（预计 1-2 天）

#### Task 1.1: 升级依赖管理

**目标**: 用 `pyproject.toml` 替代 `requirements.txt`，支持版本锁定

**当前状态**:
```
requirements.txt  # 无版本锁定，依赖漂移风险
```

**目标状态**:
```
pyproject.toml    # PEP 621 标准，开发/生产依赖分离
poetry.lock 或 uv.lock  # 版本锁定（可选）
```

**具体任务**:
- [x] 创建 `pyproject.toml`，定义项目元数据 ✅ 2026-06-06
- [x] 分离 `dependencies` 和 `[project.optional-dependencies] dev` ✅
- [ ] 删除 `requirements.txt`（或保留为兼容）
- [ ] 更新 `CLAUDE.md` 中的安装命令

**验收标准**:
```bash
pip install -e ".[dev]"  # 应成功安装所有依赖
pytest tests/ -v         # 测试通过
```

**参考配置**:
```toml
[project]
name = "ai-dev-platform"
version = "0.1.0"
description = "多 Agent 协作的全自动 Web 应用开发平台"
requires-python = ">=3.12"
license = {text = "MIT"}
dependencies = [
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "openai>=1.50.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0",
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "websockets>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "pre-commit>=3.7.0",
    "python-json-logger>=2.0.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

---

#### Task 1.2: 配置 Ruff Linter

**目标**: 统一代码风格，自动修复常见问题

**具体任务**:
- [x] 在 `pyproject.toml` 中添加 `[tool.ruff]` 配置 ✅ 2026-06-06
- [x] 运行 `ruff check src/ --fix` 自动修复 ✅
- [x] 运行 `ruff format src/` 格式化 ✅
- [x] 修复所有 remaining 问题 ✅

**配置**:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "W",    # pycodestyle warnings
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**验收标准**:
```bash
ruff check src/ tests/  # 零报错
ruff format --check src/ tests/  # 无未格式化文件
```

---

#### Task 1.3: 配置 MyPy 类型检查

**目标**: 强制类型注解，提前发现类型错误

**具体任务**:
- [x] 在 `pyproject.toml` 中添加 `[tool.mypy]` 配置 ✅ 2026-06-06
- [x] 逐步修复类型错误（先从核心模块开始） ✅
- [x] 创建 `py.typed` 标记文件 ✅

**配置**:
```toml
[tool.mypy]
python_version = "3.12"
strict = false  # 初期宽松，逐步收紧
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true  # 第三方库暂不检查

# 按模块逐步启用 strict
[[tool.mypy.overrides]]
module = ["src.orchestrator.*", "src.agents.*"]
disallow_untyped_defs = true
```

**验收标准**:
```bash
mypy src/  # 零错误（或仅忽略的警告）
```

---

#### Task 1.4: 配置 Pre-commit Hooks

**目标**: 提交前自动检查，防止问题流入仓库

**具体任务**:
- [x] 创建 `.pre-commit-config.yaml` ✅ 2026-06-06
- [ ] 安装 hooks: `pre-commit install`（环境限制暂跳过）
- [ ] 测试 hooks 工作正常

**配置**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, pydantic-settings]
        args: [--ignore-missing-imports]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=500]
```

**验收标准**:
```bash
pre-commit run --all-files  # 全部通过
git commit -m "test"  # 触发 hooks 检查
```

---

### 阶段 2：测试与 CI（预计 2-3 天）

#### Task 2.1: 增强测试配置

**目标**: 覆盖率统计、并行测试、更好的测试组织

**具体任务**:
- [ ] 在 `pyproject.toml` 中配置 pytest
- [ ] 添加 pytest-cov 覆盖率统计
- [ ] 创建 `conftest.py` 共享 fixtures
- [ ] 运行完整测试套件，记录基线覆盖率

**配置**:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
]
markers = [
    "slow: 慢速测试（需要 LLM 调用）",
    "integration: 集成测试",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "tests/*",
    "src/web/*",  # Web 层暂不覆盖
]

[tool.coverage.report]
fail_under = 70
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

**验收标准**:
```bash
pytest tests/ -v --cov=src --cov-report=html
# 生成 htmlcov/index.html，打开查看覆盖率
```

---

#### Task 2.2: 补充单元测试

**目标**: 核心模块测试覆盖率 ≥70%

**需要补充测试的模块**:
- [ ] `src/llm/provider.py` — LLM Provider 单元测试
- [ ] `src/agents/base.py` — Agent 基类测试
- [ ] `src/agents/states.py` — 状态机测试（已有部分）
- [ ] `src/orchestrator/state.py` — 状态定义测试
- [ ] `src/sandbox/executor.py` — 沙箱执行器测试

**测试文件结构**:
```
tests/
├── unit/
│   ├── test_llm_provider.py
│   ├── test_agent_base.py
│   ├── test_states.py
│   └── test_sandbox.py
├── integration/
│   └── test_requirement_flow.py
├── e2e/
│   └── test_e2e_requirement.py  # 已有
├── conftest.py
└── __init__.py
```

**验收标准**:
```bash
pytest tests/unit/ -v --cov=src
# 每个单元测试文件独立通过
# 核心模块覆盖率 ≥70%
```

---

#### Task 2.3: 创建 GitHub Actions CI

**目标**: push/PR 自动触发测试+lint+类型检查

**具体任务**:
- [ ] 创建 `.github/workflows/ci.yml`
- [ ] 配置 Python 3.12 环境
- [ ] 添加缓存加速
- [ ] 添加覆盖率上报（可选：Codecov）

**配置**:
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install dependencies
        run: pip install ruff mypy pydantic pydantic-settings
      
      - name: Ruff check
        run: ruff check src/ tests/
      
      - name: Ruff format check
        run: ruff format --check src/ tests/
      
      - name: MyPy
        run: mypy src/

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
```

**验收标准**:
```bash
# push 到 GitHub 后，Actions 页面显示绿色 ✓
# PR 自动触发检查
```

---

#### Task 2.4: 创建 Docker 开发环境

**目标**: 容器化开发，沙箱安全执行

**具体任务**:
- [ ] 创建 `Dockerfile`（开发+生产多阶段）
- [ ] 创建 `docker-compose.yml`（本地开发）
- [ ] 创建 `.dockerignore`
- [ ] 测试容器内测试运行

**Dockerfile**:
```dockerfile
# 开发阶段
FROM python:3.12-slim AS development

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# 复制代码
COPY src/ src/
COPY tests/ tests/

# 默认运行测试
CMD ["pytest", "tests/", "-v"]
```

**docker-compose.yml**:
```yaml
version: "3.8"

services:
  app:
    build:
      context: .
      target: development
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
    env_file:
      - .env
    environment:
      - LOG_LEVEL=DEBUG
      - PYTHONUNBUFFERED=1
    command: pytest tests/ -v --cov=src
    
  # 可选：Web 服务
  web:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src
    env_file:
      - .env
    command: uvicorn src.web.main:app --reload --host 0.0.0.0
```

**.dockerignore**:
```
.git
.github
__pycache__
*.pyc
.env
venv/
.venv/
htmlcov/
.coverage
.mypy_cache/
.ruff_cache/
```

**验收标准**:
```bash
docker compose run app  # 测试通过
docker compose up web   # Web 服务启动
```

---

### 阶段 3：配置与日志（预计 1-2 天）

#### Task 3.1: 统一配置管理

**目标**: 用 pydantic-settings 集中管理所有配置，支持校验和默认值

**具体任务**:
- [ ] 重构 `src/utils/config.py`
- [ ] 添加所有配置项（LLM、沙箱、日志等）
- [ ] 更新 `.env.example` 作为模板
- [ ] 替换所有 `os.getenv` 调用

**配置类**:
```python
# src/utils/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal

class Settings(BaseSettings):
    """应用全局配置"""
    
    # ── LLM 配置 ──────────────────────────────────────
    deepseek_api_key: str = Field(..., env="DEEPSEEK_API_KEY")
    minimax_api_key: str = Field(..., env="MINIMAX_API_KEY")
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    
    # ── 沙箱配置 ──────────────────────────────────────
    sandbox_timeout: int = Field(60, env="SANDBOX_TIMEOUT")
    sandbox_max_memory: str = Field("512m", env="SANDBOX_MAX_MEMORY")
    
    # ── 日志配置 ──────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", env="LOG_LEVEL"
    )
    log_format: Literal["json", "text"] = Field("text", env="LOG_FORMAT")
    
    # ── 应用配置 ──────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = Field(
        "development", env="APP_ENV"
    )
    debug: bool = Field(False, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局单例
settings = Settings()
```

**.env.example**:
```bash
# LLM API Keys
DEEPSEEK_API_KEY=your_deepseek_key_here
MINIMAX_API_KEY=your_minimax_key_here
OPENAI_API_KEY=your_openai_key_here

# 沙箱配置
SANDBOX_TIMEOUT=60
SANDBOX_MAX_MEMORY=512m

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=text

# 应用配置
APP_ENV=development
DEBUG=false
```

**验收标准**:
```bash
# 缺少必填项时启动报错
python -c "from src.utils.config import settings"
# 输出配置信息
python -c "from src.utils.config import settings; print(settings.model_dump())"
```

---

#### Task 3.2: 添加结构化日志

**目标**: 统一日志格式，支持 JSON 输出便于日志收集

**具体任务**:
- [ ] 创建 `src/utils/logger.py`
- [ ] 替换所有 `print` 为 `logger.info/debug`
- [ ] 在关键节点添加日志（Agent 调用、LLM 请求等）

**实现**:
```python
# src/utils/logger.py
import logging
import sys
from typing import Optional

from src.utils.config import settings


def setup_logger(
    name: str,
    level: Optional[str] = None,
    format_type: Optional[str] = None,
) -> logging.Logger:
    """创建结构化 Logger"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level or settings.log_level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    handler = logging.StreamHandler(sys.stdout)
    
    if (format_type or settings.log_format) == "json":
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"},
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# 预定义 logger
agent_logger = setup_logger("agent")
llm_logger = setup_logger("llm")
orchestrator_logger = setup_logger("orchestrator")
```

**使用示例**:
```python
# src/agents/requirement.py
from src.utils.logger import agent_logger, llm_logger

class RequirementAgent(BaseAgent):
    def run(self, state: dict) -> dict:
        agent_logger.info(f"RequirementAgent 开始处理: {state['user_idea'][:50]}...")
        
        # LLM 调用
        llm_logger.debug(f"调用 LLM: model=requirement, messages_count={len(messages)}")
        response = self.llm.chat(messages, agent_type="requirement")
        llm_logger.debug(f"LLM 响应: {response[:100]}...")
        
        agent_logger.info(f"RequirementAgent 完成: ask_user={result.get('ask_user') is not None}")
        return result
```

**验收标准**:
```bash
# 文本格式
LOG_FORMAT=text pytest tests/ -v
# 输出: 2026-06-06 10:00:00 | agent | INFO | RequirementAgent 开始处理...

# JSON 格式
LOG_FORMAT=json pytest tests/ -v
# 输出: {"timestamp": "2026-06-06T10:00:00", "name": "agent", "level": "info", ...}
```

---

#### Task 3.3: 创建开发者文档

**目标**: 新成员能快速上手，减少口头传递

**具体任务**:
- [ ] 更新 `README.md`（安装、运行、测试）
- [ ] 创建 `docs/development.md`（开发指南）
- [ ] 创建 `docs/architecture.md`（架构说明）

**README.md 结构**:
```markdown
# AI Dev Platform

多 Agent 协作的全自动 Web 应用开发平台

## 快速开始

### 环境要求
- Python 3.12+
- Docker（可选，用于沙箱执行）

### 安装
```bash
git clone <repo-url>
cd ai-dev-platform
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
cp .env.example .env      # 填写 API Keys
pip install -e ".[dev]"
```

### 运行测试
```bash
pytest tests/ -v --cov=src
```

### 代码检查
```bash
ruff check src/
ruff format --check src/
mypy src/
```

### 启动 Web 服务（Phase 3）
```bash
uvicorn src.web.main:app --reload
```

## 开发指南
详见 [docs/development.md](docs/development.md)

## 架构说明
详见 [docs/architecture.md](docs/architecture.md)
```

---

### 阶段 4：安全与监控（预计 3-5 天）

#### Task 4.1: 沙箱安全加固

**目标**: 限制资源使用，防止恶意代码逃逸

**具体任务**:
- [ ] 添加资源限制（CPU、内存、磁盘）
- [ ] 添加网络隔离（可选）
- [ ] 添加执行超时保护
- [ ] 添加文件系统只读挂载（可选）

**增强实现**:
```python
# src/sandbox/executor.py
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxConfig:
    """沙箱配置"""
    timeout: int = 60           # 秒
    max_memory_mb: int = 512    # MB
    max_cpu_time: int = 30      # 秒
    max_file_size_mb: int = 100 # MB
    allowed_commands: tuple[str, ...] = ("python", "pip", "npm", "node")


class SecureSandboxExecutor:
    """安全沙箱执行器"""
    
    def __init__(self, config: SandboxConfig | None = None):
        self.config = config or SandboxConfig()
        self.work_dir: Path | None = None
    
    def run_command(self, command: str, timeout: int | None = None) -> tuple[str, int]:
        """执行命令（带资源限制）"""
        
        # 命令白名单检查
        base_cmd = command.split()[0] if command else ""
        if base_cmd not in self.config.allowed_commands:
            return f"命令不允许: {base_cmd}", 1
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=timeout or self.config.timeout,
            )
            return result.stdout + result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return f"执行超时（{self.config.timeout}秒）", -1
        except Exception as e:
            return f"执行错误: {str(e)}", -2
```

**验收标准**:
```bash
# 超时测试
timeout 5 python -c "import time; time.sleep(10)"  # 应被中断
# 内存限制测试（需要 cgroup 或 Docker）
```

---

#### Task 4.2: 添加健康检查

**目标**: 支持监控和容器探针

**具体任务**:
- [ ] 创建 `src/utils/health.py`
- [ ] 添加 `/health` 端点（FastAPI 路由）
- [ ] 检查 LLM 连接、磁盘空间等

**实现**:
```python
# src/utils/health.py
from dataclasses import dataclass
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """健康检查结果"""
    status: HealthStatus
    checks: dict[str, Any]
    version: str = "0.1.0"


async def check_health() -> HealthCheck:
    """执行健康检查"""
    checks = {}
    overall = HealthStatus.HEALTHY
    
    # 检查 LLM 连接
    try:
        from src.utils.config import settings
        checks["llm_config"] = {
            "deepseek": bool(settings.deepseek_api_key),
            "minimax": bool(settings.minimax_api_key),
        }
    except Exception as e:
        checks["llm_config"] = {"error": str(e)}
        overall = HealthStatus.DEGRADED
    
    # 检查磁盘空间
    import shutil
    usage = shutil.disk_usage("/")
    free_gb = usage.free / (1024**3)
    checks["disk"] = {
        "free_gb": round(free_gb, 2),
        "status": "ok" if free_gb > 1 else "low",
    }
    if free_gb < 1:
        overall = HealthStatus.DEGRADED
    
    return HealthCheck(status=overall, checks=checks)
```

---

#### Task 4.3: 添加 Metrics 收集（可选）

**目标**: 追踪关键指标，便于优化

**需要追踪的指标**:
- [ ] Agent 执行次数、耗时
- [ ] LLM 调用次数、token 消耗
- [ ] 错误率、重试次数
- [ ] 端到端任务完成时间

**简单实现**:
```python
# src/utils/metrics.py
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Metrics:
    """简易指标收集器"""
    
    agent_calls: dict[str, int] = field(default_factory=dict)
    agent_durations: dict[str, list[float]] = field(default_factory=dict)
    llm_calls: dict[str, int] = field(default_factory=dict)
    errors: dict[str, int] = field(default_factory=dict)
    
    def record_agent_call(self, agent_name: str, duration: float) -> None:
        """记录 Agent 调用"""
        self.agent_calls[agent_name] = self.agent_calls.get(agent_name, 0) + 1
        self.agent_durations.setdefault(agent_name, []).append(duration)
    
    def record_llm_call(self, model: str, tokens: int = 0) -> None:
        """记录 LLM 调用"""
        self.llm_calls[model] = self.llm_calls.get(model, 0) + 1
    
    def record_error(self, error_type: str) -> None:
        """记录错误"""
        self.errors[error_type] = self.errors.get(error_type, 0) + 1
    
    def summary(self) -> dict[str, Any]:
        """生成摘要"""
        avg_durations = {}
        for agent, durations in self.agent_durations.items():
            avg_durations[agent] = {
                "count": len(durations),
                "avg_ms": sum(durations) / len(durations) * 1000,
            }
        
        return {
            "agent_calls": self.agent_calls,
            "agent_durations": avg_durations,
            "llm_calls": self.llm_calls,
            "errors": self.errors,
        }


# 全局实例
metrics = Metrics()
```

---

## 三、任务依赖关系

```
阶段 1（基础规范）
├── Task 1.1 (pyproject.toml) ─────────┐
├── Task 1.2 (Ruff) ──────────────────┤
├── Task 1.3 (MyPy) ──────────────────┼──→ 阶段 2（测试与 CI）
└── Task 1.4 (Pre-commit) ────────────┘    │
                                           ├── Task 2.1 (pytest 配置)
阶段 3（配置与日志）                        ├── Task 2.2 (单元测试)
├── Task 3.1 (配置管理) ──────────────┼──→ Task 2.3 (GitHub Actions)
├── Task 3.2 (结构化日志) ────────────┤    └── Task 2.4 (Docker)
└── Task 3.3 (开发者文档) ────────────┘
                                           │
阶段 4（安全与监控） ←──────────────────────┘
├── Task 4.1 (沙箱加固)
├── Task 4.2 (健康检查)
└── Task 4.3 (Metrics)
```

---

## 四、验收清单

### 阶段 1 完成后
- [ ] `pip install -e ".[dev]"` 成功
- [ ] `ruff check src/` 零报错
- [ ] `ruff format --check src/` 通过
- [ ] `mypy src/` 零错误
- [ ] `pre-commit run --all-files` 通过

### 阶段 2 完成后
- [ ] `pytest tests/ -v --cov=src --cov-report=html` 覆盖率 ≥70%
- [ ] GitHub Actions 显示绿色 ✓
- [ ] `docker compose run app` 测试通过

### 阶段 3 完成后
- [ ] `python -c "from src.utils.config import settings"` 正常
- [ ] 日志输出格式统一
- [ ] README.md 更新完整

### 阶段 4 完成后
- [ ] 沙箱超时测试通过
- [ ] `/health` 端点返回正确状态
- [ ] Metrics 可查询

---

## 五、时间估算

| 阶段 | 任务数 | 预计耗时 | 依赖 |
|------|--------|---------|------|
| 阶段 1 | 4 | 1-2 天 | 无 |
| 阶段 2 | 4 | 2-3 天 | 阶段 1 |
| 阶段 3 | 3 | 1-2 天 | 阶段 1 |
| 阶段 4 | 3 | 3-5 天 | 阶段 2, 3 |
| **总计** | **14** | **7-12 天** | - |

---

## 六、风险与注意事项

1. **依赖兼容性**: 升级依赖可能导致 API 变化，需逐步验证
2. **测试覆盖率**: 初期 70% 目标合理，避免过度测试配置代码
3. **CI 运行时间**: GitHub Actions 免费额度有限，优化缓存
4. **Docker 镜像大小**: 选择 slim 基础镜像，多阶段构建
5. **团队习惯**: 工具引入需团队共识，避免强制推行

---

**文档维护**: 此任务书随项目演进更新，完成后打勾并记录实际耗时。
