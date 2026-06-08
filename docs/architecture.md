# 架构说明

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 层 (FastAPI)                      │
│              WebSocket + REST API                        │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 Orchestrator (LangGraph)                 │
│                   状态图编排引擎                           │
└───┬───────┬───────┬───────┬───────┬───────┬─────────────┘
    │       │       │       │       │       │
┌───▼──┐┌───▼──┐┌───▼──┐┌───▼──┐┌───▼──┐┌───▼──┐
│ 需求  ││ 架构  ││ 后端  ││ 前端  ││ 测试  ││ 部署  │
│Agent ││Agent ││Agent ││Agent ││Agent ││Agent │
└───┬──┘└───┬──┘└───┬──┘└───┬──┘└───┬──┘└───┬──┘
    │       │       │       │       │       │
    └───────┴───────┴───┬───┴───────┴───────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                    LLM Provider                          │
│            DeepSeek V4 / MiniMax 2.7                     │
└─────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Sandbox Executor                       │
│              临时目录 + subprocess                        │
└─────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. Orchestrator（调度中心）

基于 LangGraph 的状态图，负责 Agent 之间的协作编排。

```python
# src/orchestrator/state.py
class ProjectState(TypedDict):
    user_idea: str           # 用户输入
    prd: str | None          # PRD 文档
    tech_plan: str | None    # 技术方案
    backend_code: str | None
    frontend_code: str | None
    test_report: str | None
    zip_path: str | None
    current_stage: Stage
    messages: list[dict]     # Agent 间消息
```

**状态流转**：
```
REQUIREMENT → ARCHITECTURE → BACKEND/FRONTEND (并行) → TESTING → DEPLOYMENT → DONE
```

### 2. Agents（智能体）

所有 Agent 继承 `BaseAgent`，实现 `run(state) -> state` 接口。

```python
class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str): ...
    def run(self, state: dict) -> dict: ...  # 核心方法
```

### 3. LLM Provider（模型层）

统一的 LLM 调用接口，根据 Agent 类型路由到不同模型。

```python
MODEL_MAP = {
    "requirement": "minimax:minimax-text-01",
    "architect": "deepseek:deepseek-chat",
    "backend": "deepseek:deepseek-chat",
    ...
}
```

### 4. Sandbox（沙箱）

安全的代码执行环境，支持文件读写和命令执行。

- 命令白名单检查
- 超时保护
- 临时目录自动清理

## 数据流

```
用户输入想法
    ↓
RequirementAgent.run(state)
    ↓ (prd)
ArchitectAgent.run(state)
    ↓ (tech_plan)
BackendAgent.run(state) ──┐
FrontendAgent.run(state) ─┤ (并行)
                          ↓
TesterAgent.run(state)
    ↓ (test_report)
DeployerAgent.run(state)
    ↓ (zip_path)
交付用户
```

## 配置管理

使用 pydantic-settings 集中管理：

```python
# src/utils/config.py
class Settings(BaseSettings):
    deepseek_api_key: str = ""
    minimax_api_key: str = ""
    sandbox_timeout: int = 60
    log_level: str = "INFO"
    ...
```

## 日志

结构化日志，支持 JSON 和文本格式：

```python
from src.utils.logger import agent_logger, llm_logger

agent_logger.info("Agent 开始处理")
llm_logger.debug("调用 LLM: model=deepseek")
```
