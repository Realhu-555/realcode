# AI Dev Platform — 需求规格 & 技术方案

> 给 Claude Code 的执行文档。按顺序实现。
>
> **更新记录：**
> - 2026-05-04：新增「Agent 状态机重构」章节（借鉴 claw-code 架构），待实现

---

## 一、产品概述

一个多 Agent 协作的全自动 Web 应用开发平台。不懂技术的用户只需用自然语言描述想法（如"我要一个团队任务看板"），系统自动完成需求分析 → 架构设计 → 前后端代码生成 → 测试 → 打包交付。

## 二、核心工作流程

```
用户输入想法
  → 需求分析 Agent 追问澄清 → 产出 PRD
  → 架构师 Agent 设计技术方案 → 产出 API 文档 + 数据库设计
  → 前端 Agent + 后端 Agent 并行生成代码
  → 测试 Agent 验证 → 修 Bug
  → 打包 zip → 交付用户
```

## 三、Agent 角色定义

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| RequirementAgent | 追问用户、产出 PRD | 用户一句话 | 结构化 PRD |
| ArchitectAgent | 技术选型、DB/API 设计 | PRD | 技术方案文档 |
| BackendAgent | 生成 FastAPI 代码 | 技术方案 | 可运行后端代码 |
| FrontendAgent | 生成 React 代码 | 技术方案 | 可运行前端代码 |
| TesterAgent | 生成测试、运行验证 | 前后端代码 | 测试报告 |
| DeployerAgent | 打包 zip | 完整项目 | zip 文件 |

## 四、技术栈

- **协调框架**: LangGraph（状态图驱动的 Agent 编排）
- **LLM 层**: 统一调用 OpenAI / Anthropic / DeepSeek
- **代码沙箱**: 本地临时目录 + subprocess（MVP 阶段不用 Docker）
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: React + TypeScript + Tailwind CSS
- **通信**: Agent 间通过共享状态 + 消息列表协作

## 五、Phase 1 实现范围（6 个任务）

MVP 目标：用户输入想法 → 需求分析 Agent 追问 → 产出 PRD 文档。

### Task 1.1: 项目骨架
**创建文件和目录：**

```
ai-dev-platform/
├── src/
│   ├── orchestrator/
│   │   ├── __init__.py      # 调度中心：Agent 编排
│   │   ├── graph.py         # LangGraph 状态图定义
│   │   └── state.py         # 共享状态定义
│   ├── agents/
│   │   ├── __init__.py      # Agent 模块
│   │   ├── base.py          # Agent 抽象基类
│   │   └── requirement.py   # 需求分析 Agent
│   ├── sandbox/
│   │   ├── __init__.py      # 代码沙箱
│   │   └── executor.py      # 本地临时目录 + subprocess 执行器
│   ├── llm/
│   │   ├── __init__.py      # LLM 调用层
│   │   ├── provider.py      # 统一 LLM Provider（OpenAI/Anthropic/DeepSeek）
│   │   └── prompts/
│   │       ├── __init__.py
│   │       └── requirement.py  # 需求分析 Agent 的 System Prompt
│   ├── web/
│   │   └── __init__.py      # Web API（Phase 3 实现）
│   └── utils/
│       ├── __init__.py
│       └── config.py        # 配置类（环境变量读取）
├── tests/
│   └── __init__.py
├── requirements.txt
├── .gitignore
└── README.md
```

**requirements.txt 内容：**
```
langgraph>=0.2.0
langchain>=0.3.0
langchain-openai>=0.2.0
openai>=1.50.0
pydantic>=2.0
pydantic-settings>=2.0
python-dotenv>=1.0
pytest>=8.0
pytest-asyncio>=0.24.0
```

**.gitignore 内容：**
```
__pycache__/
.env
venv/
*.pyc
.claude/
```

### Task 1.2: Agent 基类 + LLM Provider
**文件：src/agents/base.py**

```python
"""Agent 抽象基类"""
from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    """所有 Agent 的基类"""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
    
    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 任务，输入共享状态，返回更新后的状态"""
        pass
```

**文件：src/llm/provider.py**

统一 LLM 调用层，支持 OpenAI / Anthropic / DeepSeek 三家。核心逻辑：

```python
"""统一 LLM Provider"""
import os
from openai import OpenAI


class LLMProvider:
    """统一的 LLM 调用接口"""
    
    # 不同任务用不同模型（成本控制 + 能力匹配）
    MODEL_MAP = {
        "requirement": "minimax:minimax-text-01",     # 中文对话多，MiniMax 中文强
        "architect": "deepseek:deepseek-chat",         # 技术推理要求高
        "backend": "deepseek:deepseek-chat",           # 代码质量要求最高
        "frontend": "minimax:minimax-text-01",         # 分担 DeepSeek 压力
        "tester": "minimax:minimax-text-01",           # 测试用例生成
        "deployer": "minimax:minimax-text-01",
        "documenter": "minimax:minimax-text-01",
    }
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com"
        )
        self.minimax_client = OpenAI(
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            base_url="https://api.minimax.chat/v1"
        )
    
    def chat(self, messages: list[dict], agent_type: str = "requirement") -> str:
        """
        核心方法：发消息给 LLM，返回文本。
        messages 格式: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        agent_type 决定用哪个模型。
        """
        model_key = self.MODEL_MAP.get(agent_type, "deepseek:deepseek-chat")
        provider, model = model_key.split(":", 1)
        return self._call_openai_compatible(messages, model, provider)
    
    def _call_openai_compatible(self, messages, model, provider):
        """OpenAI 兼容接口（DeepSeek / MiniMax / OpenAI）"""
        if provider == "deepseek":
            client = self.deepseek_client
        elif provider == "minimax":
            client = self.minimax_client
        else:
            client = self.openai_client
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content
```

### Task 1.3: 共享状态 + LangGraph 图

**文件：src/orchestrator/state.py**

```python
"""共享状态定义"""
from typing import TypedDict, Optional, Annotated
from enum import Enum
import operator


class Stage(str, Enum):
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DONE = "done"
    ERROR = "error"


class ProjectState(TypedDict):
    """多 Agent 共享的全局状态"""
    # 用户输入
    user_idea: str
    # 各阶段产出
    prd: Optional[str]           # 需求分析 → PRD 文档
    tech_plan: Optional[str]      # 架构师 → 技术方案
    frontend_code: Optional[str]  # 前端代码
    backend_code: Optional[str]   # 后端代码
    test_report: Optional[str]    # 测试报告
    zip_path: Optional[str]       # 打包路径
    # 流程控制
    current_stage: Stage
    error_message: Optional[str]
    # Agent 间消息（接力棒）
    messages: Annotated[list[dict], operator.add]
    # 多轮对话
    ask_user: Optional[str]       # 需要问用户的问题（暂停点）
```

**文件：src/orchestrator/graph.py**

```python
"""LangGraph 状态图 — Agent 编排核心"""
from langgraph.graph import StateGraph, END
from src.orchestrator.state import ProjectState, Stage


def create_graph(agents: dict) -> StateGraph:
    """
    创建 Agent 编排图。
    agents 字典: {"requirement": RequirementAgent实例, ...}
    """
    graph = StateGraph(ProjectState)
    
    # 注册所有 Agent 节点
    graph.add_node("requirement", agents["requirement"].run)
    graph.add_node("architect", agents["architect"].run)
    graph.add_node("backend", agents["backend"].run)
    graph.add_node("frontend", agents["frontend"].run)
    graph.add_node("tester", agents["tester"].run)
    graph.add_node("deployer", agents["deployer"].run)
    
    # 设置起点
    graph.set_entry_point("requirement")
    
    # 条件路由：根据当前阶段决定下一步
    graph.add_conditional_edges(
        "requirement",
        _route_after_requirement,
        {
            "ask_user": END,        # 需要追问 → 暂停等用户
            "continue": "architect", # PRD 完成 → 架构师
        }
    )
    
    graph.add_edge("architect", "backend")
    graph.add_edge("architect", "frontend")
    graph.add_edge("backend", "tester")
    graph.add_edge("frontend", "tester")
    graph.add_edge("tester", "deployer")
    graph.add_edge("deployer", END)
    
    return graph.compile()


def _route_after_requirement(state: ProjectState) -> str:
    """判断需求分析后往哪走"""
    if state.get("ask_user"):
        return "ask_user"    # 有追问 → 暂停
    return "continue"         # PRD 完成 → 继续
```

### Task 1.4: 需求分析 Agent

**文件：src/llm/prompts/requirement.py**

```python
REQUIREMENT_PROMPT = """你是一个资深产品经理，专门帮助非技术用户把模糊想法变成清晰的需求文档。

## 你的工作流程

### 第一步：判断信息充分性
看用户的描述，检查这些信息有没有：
1. 目标用户是谁？
2. 核心功能是什么？（至少列3个）
3. 有没有特殊的业务规则？

如果任何一项不清楚 → 追问用户。每次只问 1-2 个最关键的问题。

### 第二步：追问（最多3轮）
追问格式（严格遵守）：
---
ASK_USER: 你的问题内容
---
ASK_USER 后面的内容会直接展示给用户，所以问题要通俗易懂，不要用技术术语。

### 第三步：产出 PRD
当信息足够时，输出结构化 PRD。格式如下：

---PRD_START---
## 产品概述
[一句话说清楚这个产品是什么]

## 目标用户
- [用户类型1]：[他们为什么需要这个]
- [用户类型2]：[他们为什么需要这个]

## 核心功能（按优先级排列）
1. [功能名]：[描述]（优先级：高/中/低）
2. [功能名]：[描述]（优先级：高/中/低）
...

## 页面结构
- **[页面1名称]**
  - 包含元素：[列出页面上有什么]
  - 用户操作：[列出用户能做什么]
- **[页面2名称]**
  - ...

## 数据模型概要
- **[实体1]**：[存储什么数据]
  - 关键字段：[field1, field2, ...]
- **[实体2]**：[存储什么数据]
  - 关键字段：[field1, field2, ...]

## 非功能需求
- [性能、安全、兼容性等方面的要求]
---PRD_END---

## 注意事项
- 不要替用户做假设，不清楚的一定要问
- 追问最多3轮，第3轮还没说清楚就用合理推断补全
- 不要输出任何技术实现细节（那是架构师的事）
- 用通俗语言，目标读者是不懂技术的人
"""
```

**文件：src/agents/requirement.py**

```python
"""需求分析 Agent"""
from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.llm.prompts.requirement import REQUIREMENT_PROMPT


class RequirementAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="requirement", system_prompt=REQUIREMENT_PROMPT)
        self.llm = LLMProvider()
        self.round = 0  # 追问轮次
    
    def run(self, state: dict) -> dict:
        self.round += 1
        
        # 组装消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"用户想法：{state['user_idea']}"}
        ]
        
        # 如果有历史对话，加上
        if state.get("messages"):
            for msg in state["messages"]:
                if msg.get("from") == "requirement":
                    messages.append({"role": "assistant", "content": msg["content"]})
                elif msg.get("to") == "requirement":
                    messages.append({"role": "user", "content": msg["content"]})
        
        # 调用 LLM
        response = self.llm.chat(messages, agent_type="requirement")
        
        # 判断是否追问
        if "ASK_USER:" in response:
            question = response.split("ASK_USER:")[1].strip()
            return {
                **state,
                "ask_user": question,
                "current_stage": "requirement",
                "messages": [{
                    "from": "requirement",
                    "type": "question",
                    "content": question
                }]
            }
        
        # 存入状态
        return {
            **state,
            "prd": response,
            "ask_user": None,
            "current_stage": "architecture",
            "messages": [{
                "from": "requirement",
                "to": "architect",
                "type": "output",
                "content": response
            }]
        }
```

### Task 1.5: 本地沙箱执行器

**文件：src/sandbox/executor.py**

```python
"""本地沙箱执行器（MVP 阶段代替 Docker）"""
import tempfile
import subprocess
import shutil
from pathlib import Path


class SandboxExecutor:
    """在临时目录中执行代码，完成后自动清理"""
    
    def __init__(self):
        self.work_dir = None
    
    def create(self, project_name: str) -> Path:
        """创建临时工作目录"""
        self.work_dir = Path(tempfile.mkdtemp(prefix=f"{project_name}_"))
        return self.work_dir
    
    def write_file(self, relative_path: str, content: str):
        """在沙箱中写文件"""
        file_path = self.work_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
    def run_command(self, command: str, timeout: int = 60) -> tuple[str, int]:
        """在沙箱中执行命令"""
        result = subprocess.run(
            command,
            shell=True,
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout + result.stderr, result.returncode
    
    def cleanup(self):
        """清理临时目录"""
        if self.work_dir and self.work_dir.exists():
            shutil.rmtree(self.work_dir)
    
    def pack_zip(self, output_path: str) -> str:
        """打包为 zip"""
        zip_path = str(Path(output_path).with_suffix('.zip'))
        shutil.make_archive(
            str(Path(output_path).with_suffix('')),
            'zip',
            self.work_dir
        )
        return zip_path
```

### Task 1.6: 端到端测试 — 想法 → PRD

**文件：tests/test_e2e_requirement.py**

```python
"""端到端测试：需求分析 Agent"""
import pytest
from src.agents.requirement import RequirementAgent
from src.orchestrator.state import Stage


def test_requirement_agent_asks_when_vague():
    """模糊输入应该触发追问"""
    agent = RequirementAgent()
    state = {
        "user_idea": "我要做一个看板",
        "prd": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }
    
    result = agent.run(state)
    
    # 信息不够 → 应该追问
    assert result["ask_user"] is not None
    assert "ASK_USER:" not in (result["ask_user"] or "")  # 标记已被解析掉


def test_requirement_agent_produces_prd_when_clear():
    """清晰输入应该产出 PRD"""
    agent = RequirementAgent()
    state = {
        "user_idea": "我要做一个个人博客，能写文章、按标签分类、有评论区",
        "prd": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }
    
    result = agent.run(state)
    
    # 信息够 → 应该产出 PRD 或追问（取决于 LLM 判断）
    if result.get("ask_user"):
        # LLM 觉得需要追问，也算正常
        assert len(result["ask_user"]) > 0
    else:
        # 产出了 PRD
        assert result["prd"] is not None
        assert "PRD_START" in result["prd"] or "产品概述" in result["prd"]
        assert result["current_stage"] == Stage.ARCHITECTURE


def test_multiround_clarification():
    """多轮追问后产出 PRD"""
    agent = RequirementAgent()
    
    # 第一轮：模糊输入
    state = {
        "user_idea": "我要做一个任务管理工具",
        "prd": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }
    
    result = agent.run(state)
    assert result["ask_user"] is not None  # 应该追问
    
    # 模拟用户回答
    state2 = {
        **result,
        "ask_user": None,
        "messages": result["messages"] + [{
            "from": "user",
            "to": "requirement",
            "type": "answer",
            "content": "团队内部用，能创建任务、指派给同事、拖拽改变状态为待办/进行中/已完成"
        }]
    }
    
    agent2 = RequirementAgent()
    result2 = agent2.run(state2)
    
    # 第二轮，信息更充分了
    if result2.get("ask_user"):
        # 可能还有追问，继续回答
        state3 = {
            **result2,
            "ask_user": None,
            "messages": result2["messages"] + [{
                "from": "user",
                "to": "requirement",
                "type": "answer",
                "content": "不需要登录，3-5 人的小团队用，就这三个状态够了"
            }]
        }
        agent3 = RequirementAgent()
        result3 = agent3.run(state3)
        assert result3["prd"] is not None or result3["ask_user"] is not None
    else:
        assert result2["prd"] is not None
```

---

## 七、Agent 状态机重构（借鉴 claw-code 架构）

> 灵感来源：claw-code（Rust, 47 模块）Worker 状态机 + 故障分类。
> 目标：用状态机替代现有的正则匹配 + 轮次硬编码，彻底解决"需求 Agent 追问死循环"问题。

### 7.1 现状问题

现有 `RequirementAgent.run()` 靠正则硬猜 LLM 输出意图：
- `if "ASK_USER:" in response` → 追问？
- `if 问号/请问 in response` → 兜底猜
- `if prev_rounds >= 1` → 硬编码只允许 1 轮追问

**根本缺陷：** LLM 输出不可靠，用正则猜"LLM 想干嘛"必然出错。

### 7.2 状态定义

**文件：`src/agents/states.py`**

```python
"""Agent 状态机核心 — 可复用于所有 Agent"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional


class AgentState(Enum):
    """Agent 生命周期状态"""
    IDLE = auto()          # 等待任务
    ANALYZING = auto()     # 调 LLM 分析
    CLARIFYING = auto()    # 需要追问，发给用户
    WAITING_USER = auto()   # 等待用户回答
    PRD_WRITING = auto()    # 汇总产出 PRD
    COMPLETED = auto()      # 完成，转下一阶段
    ERROR = auto()          # 异常终止（可重试）
    FATAL = auto()          # 不可恢复错误


class AgentEvent(Enum):
    """Agent 生命周期事件"""
    TASK_ASSIGNED = auto()
    LLM_RESPONDED = auto()
    NEEDS_CLARIFICATION = auto()     # LLM 输出含追问标记
    PRD_READY = auto()               # LLM 输出了 PRD 内容
    USER_REPLIED = auto()             # 用户回答了追问
    MAX_RETRIES_REACHED = auto()      # 重试超过上限
    MAX_CLARIFICATIONS_REACHED = auto()  # 追问超过上限
    WAITING_TIMEOUT = auto()          # 用户等待超时
    LLM_ERROR = auto()
    FATAL_ERROR = auto()


@dataclass
class StateMachine:
    """
    状态机上下文。
    每个 Agent 实例持有一个 StateMachine，跟 ProjectState（跨 Agent 共享状态）分开。
    """
    state: AgentState = AgentState.IDLE
    clarification_count: int = 0
    retry_count: int = 0
    max_clarifications: int = 3     # 最多追问 3 轮
    max_retries: int = 1           # LLM 调用最多重试 1 次
    timeout_minutes: int = 30       # 用户等待超时 30 分钟
    last_question: Optional[str] = None   # 最近一次追问内容
    context: dict = field(default_factory=dict)  # 状态机内部上下文

    # 迁移表：(当前状态, 事件) → 下一状态
    _TRANSITIONS: dict[tuple[AgentState, AgentEvent], AgentState] = {
        # 正常流程
        (AgentState.IDLE,          AgentEvent.TASK_ASSIGNED):         AgentState.ANALYZING,
        (AgentState.ANALYZING,      AgentEvent.LLM_RESPONDED):        AgentState.ANALYZING,
        (AgentState.ANALYZING,      AgentEvent.NEEDS_CLARIFICATION):  AgentState.CLARIFYING,
        (AgentState.ANALYZING,      AgentEvent.PRD_READY):            AgentState.PRD_WRITING,
        (AgentState.ANALYZING,      AgentEvent.LLM_ERROR):            AgentState.ERROR,
        (AgentState.ANALYZING,      AgentEvent.FATAL_ERROR):          AgentState.FATAL,
        (AgentState.CLARIFYING,     AgentEvent.MAX_CLARIFICATIONS_REACHED): AgentState.PRD_WRITING,
        (AgentState.CLARIFYING,     AgentEvent.USER_REPLIED):          AgentState.ANALYZING,
        (AgentState.WAITING_USER,   AgentEvent.USER_REPLIED):         AgentState.ANALYZING,
        (AgentState.WAITING_USER,   AgentEvent.WAITING_TIMEOUT):       AgentState.PRD_WRITING,
        (AgentState.PRD_WRITING,    AgentEvent.PRD_READY):            AgentState.COMPLETED,
        (AgentState.PRD_WRITING,    AgentEvent.LLM_ERROR):            AgentState.ERROR,
        (AgentState.ERROR,          AgentEvent.MAX_RETRIES_REACHED):  AgentState.FATAL,
        (AgentState.ERROR,          AgentEvent.LLM_RESPONDED):        AgentState.ANALYZING,
    }

    def transition(self, event: AgentEvent) -> AgentState:
        """执行状态迁移。未知迁移 → FATAL。"""
        key = (self.state, event)
        if key in self._TRANSITIONS:
            self.state = self._TRANSITIONS[key]
        else:
            self.state = AgentState.FATAL
        return self.state

    def can_handle(self, event: AgentEvent) -> bool:
        """当前状态 + 事件是否构成合法迁移"""
        return (self.state, event) in self._TRANSITIONS

    @property
    def is_terminal(self) -> bool:
        return self.state in (AgentState.COMPLETED, AgentState.FATAL)

    def reset(self):
        self.state = AgentState.IDLE
        self.clarification_count = 0
        self.retry_count = 0
        self.context.clear()
        self.last_question = None
```

### 7.3 状态迁移图

```
用户想法 ──→ [IDLE] ── TASK_ASSIGNED ──→ [ANALYZING]
                                          │
                            ┌─────────────┼─────────────┐
                            │ LLM 出追问   │ LLM 出 PRD   │ LLM 报错
                            ▼             ▼             ▼
                     [CLARIFYING]   [PRD_WRITING]   [ERROR]
                            │                           │
              ┌──────────────┴──┐            MAX_RETRIES
              │ 追问+1，发用户   │                  │
              ▼                 ▼                  ▼
        次数<3?           次数≥3?           [FATAL]
          │                  │
          ▼                  ▼
   [WAITING_USER]    [PRD_WRITING]
          │                  │
   用户回复→ANALYZING   用户超时→PRD_WRITING
          │                  │
          └──────────────────┘
                      │
                      ▼
               [PRD_WRITING]
                      │ PRD 汇总完成
                      ▼
                [COMPLETED]
```

### 7.4 超时 & 上限约束

| 约束项 | 值 | 触发行为 |
|--------|------|---------|
| 追问上限 | 3 轮 | 第 3 轮结束后强制进入 `PRD_WRITING`，不等用户 |
| LLM 重试 | 1 次 | 调用失败自动重试，超限 → `FATAL` |
| 用户等待超时 | 30 分钟 | 超时自动用已有信息出 PRD |

### 7.5 改造 RequirementAgent

**文件：`src/agents/requirement.py`（重构）**

```python
"""需求分析 Agent — 状态机版本"""
import re
from src.agents.base import BaseAgent
from src.agents.states import AgentState, AgentEvent, StateMachine
from src.llm.provider import LLMProvider
from src.llm.prompts.requirement import REQUIREMENT_PROMPT


_ASK_PATTERN = re.compile(
    r"---ASK_USER:?\s*(.*?)(?:---|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_PRD_PATTERN = re.compile(
    r"---PRD_START---.*?---PRD_END---",
    re.DOTALL | re.IGNORECASE,
)


class RequirementAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="requirement", system_prompt=REQUIREMENT_PROMPT)
        self.llm = LLMProvider()
        # 状态机实例，生命周期 = 一个完整的需求分析任务
        self.sm = StateMachine()

    def run(self, state: dict) -> dict:
        """
        状态机驱动：每次 run() 执行一次状态推进，
        直到需要外部输入（追问用户）或完成（PRD 产出）才返回。
        """
        # ── 入口：判断触发事件 ──────────────────────────
        if self.sm.state == AgentState.IDLE:
            event = AgentEvent.TASK_ASSIGNED
        elif state.get("user_reply"):
            event = AgentEvent.USER_REPLIED
            self.sm.context["user_reply"] = state["user_reply"]
        else:
            return self._error_result(state, "未知入口状态")

        # ── 状态推进循环 ────────────────────────────────
        while not self.sm.is_terminal:
            self.sm.transition(event)

            if self.sm.state == AgentState.ANALYZING:
                event = self._do_analyze(state)

            elif self.sm.state == AgentState.CLARIFYING:
                self.sm.clarification_count += 1
                if self.sm.clarification_count >= self.sm.max_clarifications:
                    self.sm.transition(AgentEvent.MAX_CLARIFICATIONS_REACHED)
                    event = AgentEvent.PRD_READY  # 强制切到写 PRD
                else:
                    break  # 需要外部输入：追问发出去

            elif self.sm.state == AgentState.WAITING_USER:
                break  # 需要外部输入：等用户回复

            elif self.sm.state == AgentState.PRD_WRITING:
                event = self._do_prd_write(state)

            elif self.sm.state == AgentState.COMPLETED:
                return self._build_success_result(state)

            elif self.sm.state in (AgentState.ERROR, AgentState.FATAL):
                return self._error_result(state)

        # ── 需要外部输入：返回追问 ──────────────────────
        return self._build_ask_result(state)

    # ── 内部方法 ──────────────────────────────────────

    def _do_analyze(self, state: dict) -> AgentEvent:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"用户想法：{state['user_idea']}"},
        ]
        if state.get("messages"):
            for msg in state["messages"]:
                if msg.get("from") == "requirement":
                    messages.append({"role": "assistant", "content": msg["content"]})
                elif msg.get("to") == "requirement":
                    messages.append({"role": "user", "content": msg["content"]})

        try:
            response = self.llm.chat(messages, agent_type="requirement")
            self.sm.retry_count = 0
        except Exception:
            self.sm.retry_count += 1
            if self.sm.retry_count >= self.sm.max_retries:
                self.sm.transition(AgentEvent.MAX_RETRIES_REACHED)
                return AgentEvent.LLM_ERROR
            return AgentEvent.LLM_ERROR  # 重试

        if _ASK_PATTERN.search(response):
            self.sm.last_question = self._extract_question(response)
            return AgentEvent.NEEDS_CLARIFICATION
        elif _PRD_PATTERN.search(response):
            self.sm.context["prd_draft"] = response
            return AgentEvent.PRD_READY
        else:
            # 既没有追问也没有 PRD → 兜底：当作 PRD 继续
            self.sm.context["prd_draft"] = response
            return AgentEvent.PRD_READY

    def _do_prd_write(self, state: dict) -> AgentEvent:
        # 把多轮对话上下文汇总，让 LLM 输出最终 PRD
        context = self.sm.context.get("user_reply", "")
        prompt = (
            f"基于以下多轮对话信息，产出最终 PRD：\n\n{context}\n\n"
            "现在请直接输出完整 PRD 文档，用 ---PRD_START--- ... ---PRD_END--- 包裹。"
        )
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        try:
            response = self.llm.chat(messages, agent_type="requirement")
            self.sm.context["prd_draft"] = response
            self.sm.transition(AgentEvent.PRD_READY)
            return AgentEvent.PRD_READY
        except Exception:
            return AgentEvent.LLM_ERROR

    def _extract_question(self, text: str) -> str:
        m = _ASK_PATTERN.search(text)
        if m:
            return m.group(1).strip()
        # 兜底：找第一个问号之后的文字
        qm = re.search(r"[？?]\\s*(.+)", text)
        if qm:
            return qm.group(1).strip()
        return text.strip()

    def _build_ask_result(self, state: dict) -> dict:
        return {
            **state,
            "ask_user": self.sm.last_question,
            "current_stage": "requirement",
            "messages": state.get("messages", []) + [{
                "from": "requirement",
                "type": "question",
                "content": self.sm.last_question or "",
            }],
        }

    def _build_success_result(self, state: dict) -> dict:
        return {
            **state,
            "prd": self.sm.context.get("prd_draft", ""),
            "ask_user": None,
            "current_stage": "architecture",
            "messages": state.get("messages", []) + [{
                "from": "requirement",
                "to": "architect",
                "type": "output",
                "content": self.sm.context.get("prd_draft", ""),
            }],
        }

    def _error_result(self, state: dict) -> dict:
        return {
            **state,
            "error_message": f"RequirementAgent 进入 {self.sm.state.name} 状态",
            "current_stage": "error",
        }
```

### 7.6 改造 BaseAgent

```python
"""Agent 抽象基类"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """所有 Agent 的基类"""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 任务，输入共享状态，返回更新后的状态"""
        pass

    def reset(self):
        """重置 Agent 内部状态（供流水线复用）"""
        pass
```

### 7.7 LangGraph 路由适配

```python
# src/orchestrator/graph.py

def _route_after_requirement(state: ProjectState) -> str:
    """改造后：基于 Agent 状态机判断下一步"""
    agent = state.get("_requirement_agent")  # 状态机实例
    if agent is None:
        # 兼容旧逻辑
        return "continue" if not state.get("ask_user") else END

    if agent.state == AgentState.COMPLETED:
        return "continue"
    elif agent.state in (AgentState.ERROR, AgentState.FATAL):
        return "error"
    else:
        return END  # WAITING_USER / CLARIFYING / ANALYZING → 暂停
```

### 7.8 新增测试用例

**文件：`tests/test_requirement_state_machine.py`**

```python
"""状态机专项测试"""
import pytest
from src.agents.requirement import RequirementAgent
from src.agents.states import AgentState, AgentEvent, StateMachine


def test_state_machine_transitions():
    """验证迁移表正确"""
    sm = StateMachine()
    assert sm.state == AgentState.IDLE

    sm.transition(AgentEvent.TASK_ASSIGNED)
    assert sm.state == AgentState.ANALYZING

    sm.state = AgentState.ERROR
    sm.transition(AgentEvent.MAX_RETRIES_REACHED)
    assert sm.state == AgentState.FATAL


def test_clarification_limit():
    """追问超过 3 轮强制出 PRD"""
    sm = StateMachine(max_clarifications=3)
    sm.state = AgentState.ANALYZING

    for i in range(3):
        sm.clarification_count = i
        sm.transition(AgentEvent.NEEDS_CLARIFICATION)
        assert sm.state == AgentState.CLARIFYING
        sm.transition(AgentEvent.USER_REPLIED)
        assert sm.state == AgentState.ANALYZING

    # 第 3 轮结束
    sm.clarification_count = 3
    sm.transition(AgentEvent.NEEDS_CLARIFICATION)
    sm.transition(AgentEvent.MAX_CLARIFICATIONS_REACHED)
    assert sm.state == AgentState.PRD_WRITING


def test_timeout_triggers_prd():
    """等待超时强制出 PRD"""
    sm = StateMachine()
    sm.state = AgentState.WAITING_USER

    sm.transition(AgentEvent.WAITING_TIMEOUT)
    assert sm.state == AgentState.PRD_WRITING


def test_llm_retry_once():
    """LLM 报错重试 1 次"""
    sm = StateMachine(max_retries=1)
    sm.state = AgentState.ANALYZING

    sm.transition(AgentEvent.LLM_ERROR)
    assert sm.state == AgentState.ERROR
    assert sm.retry_count == 1

    sm.transition(AgentEvent.LLM_ERROR)
    sm.transition(AgentEvent.MAX_RETRIES_REACHED)
    assert sm.state == AgentState.FATAL
```

---

## 六、给 Claude Code 的执行指令

**第一步：初始化项目**
```
创建 ~/ai-dev-platform 目录，按上面 Task 1.1 的结构创建所有文件和目录。
先创建目录，再往里填文件。
```

**第二步：实现 Task 1.2**
```
按上面的代码创建 src/agents/base.py 和 src/llm/provider.py。
```

后面依此类推，一个 Task 一个 Task 来。
