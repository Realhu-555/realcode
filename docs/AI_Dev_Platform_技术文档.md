# AI Dev Platform — 项目技术文档

> 项目名称：AI Dev Platform（多Agent协作全自动Web应用开发平台）
> 作者：realhu（胡贞虎）
> 项目路径：H:\ai-dev-platform\
> 技术栈：Python 3.12 + LangGraph + FastAPI + DeepSeek V4 + MiniMax M2.7
> 开发状态：Phase 1-6 全部完成，47个测试全通过
> 最后更新：2026-06-10

---

## 一、项目概述

### 1.1 项目定位

AI Dev Platform 是一个多Agent协作的全自动Web应用开发平台。不懂技术的用户只需用自然语言描述想法（如"我要一个团队任务看板"），系统自动完成需求分析→架构设计→前后端代码生成→测试→打包交付的全流程。

### 1.2 核心价值

传统软件开发需要产品经理、架构师、前端、后端、测试等多个角色协作。本平台用6个AI Agent替代这些角色，用户只需要描述想法，系统自动完成从需求到可运行代码的全流程交付。

### 1.3 项目规模

- 源文件：21个Python文件
- 测试文件：13个测试文件
- 总测试用例：47个，全部通过
- 开发周期：1天（借助Claude Code AI辅助编码）
- 代码行数：约3000行（不含测试）

---

## 二、系统架构

### 2.1 整体分层

系统分为四层：

**Web层（FastAPI）**
- REST API + WebSocket实时推送
- 前端通过WebSocket连接服务端，发送需求、接收进度和中间产出
- 每个阶段的产出（PRD、技术方案、代码、测试报告）实时推送给前端展示

**Orchestrator层（LangGraph）**
- 基于LangGraph的状态图引擎
- 负责6个Agent之间的协作编排
- 支持条件分支（需求追问vs继续执行）和并行执行（前后端同时生成代码）

**Agent层（6个专职Agent）**
- RequirementAgent — 需求分析，追问用户，产出PRD
- ArchitectAgent — 技术架构设计，产出技术方案
- BackendAgent — 后端代码生成（FastAPI）
- FrontendAgent — 前端代码生成（React）
- TesterAgent — 测试验证，产出测试报告
- DeployerAgent — 打包交付，产出zip文件

**基础设施层**
- LLMProvider — 统一LLM调用接口（DeepSeek V4 + MiniMax M2.7）
- SandboxExecutor — 本地代码执行沙箱
- 共享状态（ProjectState）— Agent间数据传递的唯一通道

### 2.2 数据流

```
用户输入想法
    ↓
RequirementAgent 追问澄清 → 产出PRD
    ↓
ArchitectAgent 设计技术方案 → 产出API文档+数据库设计
    ↓
BackendAgent + FrontendAgent 并行生成代码
    ↓
TesterAgent 审查代码 → 产出测试报告
    ↓
DeployerAgent 打包zip → 交付用户
```

### 2.3 状态流转路径

```
REQUIREMENT → ARCHITECTURE → BACKEND/FRONTEND（并行）→ TESTING → DEPLOYMENT → DONE
```

特殊路径：
- RequirementAgent追问时：REQUIREMENT → END（等待用户回答）→ REQUIREMENT（从断点恢复）
- 任何Agent出错时：当前阶段 → ERROR

---

## 三、核心模块详解

### 3.1 共享状态（ProjectState）

文件：src/orchestrator/state.py

ProjectState是所有Agent共享的全局状态对象，定义为TypedDict。Agent之间不直接通信，全部通过读写ProjectState协作。

核心字段：

user_idea: str — 用户输入的原始想法，全程保留
prd: str | None — RequirementAgent产出的PRD文档
tech_plan: str | None — ArchitectAgent产出的技术方案
backend_code: str | None — BackendAgent生成的后端代码
frontend_code: str | None — FrontendAgent生成的前端代码
test_report: str | None — TesterAgent的测试报告
zip_path: str | None — DeployerAgent的打包路径
current_stage: Annotated[Stage, _latest_stage] — 当前阶段
error_message: str | None — 错误信息
messages: Annotated[list[dict], operator.add] — Agent间消息列表
ask_user: str | None — 追问内容（触发流程暂停）

**关键设计：Reducer机制**

当LangGraph中有并行分支时，多个Agent可能同时写入同一个state字段。用Annotated类型加reducer函数定义冲突解决策略：

- messages用operator.add reducer — 并行分支的消息追加合并，不会覆盖
- current_stage用自定义_latest_stage reducer — 取最新写入的值

### 3.2 LangGraph状态图

文件：src/orchestrator/graph.py

用StateGraph定义Agent的执行顺序和条件分支：

节点注册：每个Agent的run()方法注册为一个节点
入口节点：requirement（需求分析）
条件边：requirement → _route_after_requirement() → ask_user则END，continue则architect
普通边：architect → backend + frontend（并行），backend + frontend → tester，tester → deployer，deployer → END

**条件边的路由函数**

```python
def _route_after_requirement(state: ProjectState) -> str:
    if state.get("ask_user"):
        return "ask_user"  # 终止，等用户回答
    return "continue"      # 继续到架构设计
```

**并行执行**

ArchitectAgent完成后，通过两条add_edge同时触发BackendAgent和FrontendAgent。两者都完成后，LangGraph自动汇聚到TesterAgent。

### 3.3 Agent基类

文件：src/agents/base.py

所有Agent继承BaseAgent抽象基类，实现统一的run(state) -> state接口：

```python
class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str): ...
    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]: ...
```

**设计意图**：统一接口保证LangGraph能以相同方式调用所有Agent。加新Agent只需继承BaseAgent，实现run方法，注册到graph里，不改其他Agent代码。

### 3.4 RequirementAgent（需求分析）

文件：src/agents/requirement.py

这是项目最复杂的Agent，负责追问用户澄清需求，产出PRD文档。核心难点是控制LLM输出——LLM不保证按格式输出，需要多层防御。

**三层防线控制LLM输出**

第一层 — Prompt约束：
System Prompt严格定义两种输出格式。追问用[ASK_USER]...[/ASK_USER]标签，PRD用---PRD_START---标记。不允许混搭，不允许加多余文字。

第二层 — 正则解析：
_ASK_PATTERN匹配标签格式的追问（支持多种变体：[ASK_USER]、---ASK_USER:、ASK_USER:）。
_QUESTION_PATTERN兜底检测没有标签但含问号、提问词的输出。短文本（<500字）+追问特征=提问。

第三层 — 强制截断：
追踪prev_rounds（从messages列表统计历史追问次数）。超过1轮就修改System Prompt追加"必须产出PRD，禁止再追问"指令。代码层面也强制忽略ASK_USER输出——即使LLM还输出追问，也当PRD处理。

**为什么需要强制截断**：实测MiniMax M2.7不跟对话历史，已经回答过的问题还会重复问。硬限制是必要的工程手段。

**MiniMax推理块清理**

MiniMax M2.7输出会包含<think>...</think>推理块，用正则自动剥离后再做格式检测，避免推理内容干扰ASK_USER解析。

### 3.5 ArchitectAgent（架构设计）

文件：src/agents/architect.py

读取state['prd']，调用LLM生成技术方案。输出包含技术选型、API设计、数据库设计、项目结构。

**错误处理**：PRD缺失时写入error_message并设current_stage为error，不抛异常。

### 3.6 BackendAgent / FrontendAgent（代码生成）

文件：src/agents/backend.py、src/agents/frontend.py

两个Agent结构几乎相同——读取state['tech_plan']，调用LLM生成代码。设计为可并行执行。

**并行写入不冲突**：BackendAgent写state['backend_code']，FrontendAgent写state['frontend_code']，各写各的字段。current_stage都设为"testing"，但有_latest_stage reducer，取最后一个写入的值。

### 3.7 TesterAgent（测试验证）

文件：src/agents/tester.py

读取state['tech_plan'] + state['backend_code'] + state['frontend_code']（三个字段），拼成完整上下文让LLM审查代码并生成测试报告。

**汇聚点设计**：TesterAgent是并行分支的汇聚点，必须等BackendAgent和FrontendAgent都完成后才执行。LangGraph通过图的拓扑结构保证这一点。

### 3.8 DeployerAgent（打包交付）

文件：src/agents/deployer.py

最复杂的Agent之一——不只是调LLM，还要操作文件系统。

执行流程：
1. 创建沙箱临时目录
2. 解析BackendAgent的多文件输出（正则提取### path/file格式的文件标记）
3. 解析FrontendAgent的多文件输出
4. 写入PRD、技术方案、测试报告
5. 调LLM生成部署说明
6. 打包zip到Web可访问的持久化目录
7. finally块清理沙箱临时目录

**文件解析**：BackendAgent和FrontendAgent的输出是多个文件用### path/file和```code```标记组织的。DeployerAgent用正则解析这种格式，拆成{文件路径: 内容}字典，逐个写入沙箱。

**安全打包**：zip文件名做路径替换（反斜杠→下划线），防止路径注入。

---

## 四、LLM Provider 设计

文件：src/llm/provider.py

### 4.1 统一接口

三个client（DeepSeek/MiniMax/OpenAI）都用OpenAI SDK，只改base_url。换模型不改业务代码。

```python
self.deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
self.minimax_client = OpenAI(
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url="https://api.minimax.chat/v1",
)
```

### 4.2 模型路由

MODEL_MAP按Agent类型路由不同模型：

requirement → deepseek:v4-pro（需求分析多用DeepSeek，中文推理强）
architect → deepseek:v4-pro（技术推理要求高）
backend → deepseek:v4-pro（代码质量要求最高）
frontend → minimax:MiniMax-M2.7（分担DeepSeek压力）
tester → minimax:MiniMax-M2.7（测试用例生成）
deployer → minimax:MiniMax-M2.7（部署文档生成）

**选型理由**：DeepSeek推理能力强，适合架构设计和代码生成。MiniMax中文对话好，适合需求分析和文档生成。两个模型形成互补，分担API压力，降低整体成本。

### 4.3 容错机制

空响应自动重试：LLM返回空内容时，自动重试一次。
推理块清理：MiniMax输出的<think>...</think>用正则自动剥离。
temperature统一0.7：需求分析需要一定创造性，代码生成需要准确性，取折中值。

---

## 五、沙箱执行器

文件：src/sandbox/executor.py

### 5.1 设计目标

在隔离的临时环境中执行代码，不影响宿主系统。MVP阶段用轻量方案（临时目录+subprocess），不引入Docker。

### 5.2 核心能力

创建临时工作目录：tempfile.mkdtemp，带项目名前缀
文件读写：write_file / read_file，在沙箱内操作
命令执行：subprocess.run，支持超时
文件打包：shutil.make_archive生成zip
自动清理：cleanup()删除临时目录，DeployerAgent在finally块中调用

### 5.3 安全措施

命令白名单：只允许python/pip/node/npm/npx，其他命令直接拒绝
超时保护：默认60秒，防止死循环
自动清理：任务完成或异常退出都清理临时目录

---

## 六、Web服务设计

文件：src/web/server.py

### 6.1 技术选型

FastAPI + WebSocket。选FastAPI因为原生async支持（大量并发LLM调用场景）、自带Swagger文档、Pydantic数据校验。选WebSocket因为需要服务端实时推送Agent进度。

### 6.2 连接管理

ConnectionManager类管理WebSocket连接：
connect：接受连接，生成uuid4().hex作为client_id
disconnect：清理连接和对应的流水线状态
send：向指定client_id发送JSON消息

### 6.3 流水线执行

run_pipeline：启动/重新开始流水线。初始化ProjectState，从stage_index=0开始执行。
resume_pipeline：用户回答追问后恢复流水线。从_pipelines字典取出之前的state，注入用户答案，从断点继续。

**中断恢复机制**：

RequirementAgent追问用户时：
1. 服务端把当前state和执行阶段存到_pipelines字典
2. 推{type: 'clarify', question: '...'}给前端
3. 用户回答后发{action: 'answer'}
4. 服务端从_pipelines取出state，注入用户答案
5. 从断点继续执行

**每阶段执行后检查追问**：如果state['ask_user']有值，暂停流水线，保存状态，推送追问给前端。

### 6.4 状态序列化

_serialize_state函数提取当前阶段可展示的内容，截断过长文本（PRD/技术方案2000字符，测试报告1000字符），防止WebSocket消息过大。

### 6.5 前端

Cursor风格UI（奶油背景#f2f1ed、橙色按钮#f54e00）。通过WebSocket发送idea，接收progress/update/clarify/done/error五种消息类型，实时展示各阶段产出。

---

## 七、测试策略

### 7.1 测试分层

单元测试：测试单个组件（BaseAgent、LLMProvider、SandboxExecutor、State）
集成测试：测试Agent间的协作（Requirement→Architect、完整流水线）
E2E测试：端到端测试，模拟完整用户流程

### 7.2 测试工具

pytest + pytest-asyncio
conftest.py提供共享fixtures：sandbox（已初始化的沙箱）、base_state（基础ProjectState）

### 7.3 测试数据

E2E测试用mock的LLM响应，不实际调用API。避免测试依赖外部服务，保证可重复性。

### 7.4 测试覆盖

47个测试覆盖：
- LLM Provider：mock响应、空响应重试、推理块清理
- 状态管理：Stage枚举、reducer机制
- 各Agent：输入校验、输出格式、错误处理
- 沙箱：文件读写、命令执行、超时、白名单、清理
- Graph：图编译、条件路由
- E2E：完整流水线（需求→架构→代码→测试→部署）

---

## 八、Prompt设计哲学

### 8.1 每个Agent的Prompt结构

统一结构：角色定义→输入说明→输出格式→注意事项。

角色定义：明确身份（"你是一个资深技术架构师"）
输入说明：告诉LLM会收到什么（"一份产品需求文档"）
输出格式：用标签约束格式（---TECH_PLAN_START---）
注意事项：强调约束（"不要写具体代码，只设计接口"）

### 8.2 输出格式控制

每个Agent用独特的标签包裹输出：
RequirementAgent：[ASK_USER]或---PRD_START---
ArchitectAgent：---TECH_PLAN_START---
BackendAgent：---BACKEND_START---
FrontendAgent：---FRONTEND_START---
TesterAgent：---TEST_REPORT_START---
DeployerAgent：---DEPLOY_START---

DeployerAgent用正则解析这些标签内的### path/file格式，提取多个文件。

### 8.3 LLM输出不稳定的工程应对

LLM不保证100%按格式输出。工程上的应对：
正则兜底：多套正则匹配不同格式变体
强制截断：计数器限制追问轮次
推理块剥离：清理MiniMax的<think>标签
错误不炸：解析失败返回错误状态，不抛异常

---

## 九、技术决策记录

**决策1：用LangGraph而不是LangChain Chain**
原因：Chain是线性调用，遇到分支和并行很别扭。LangGraph是状态图模型，天然支持条件分支、并行执行和状态回溯。

**决策2：Agent间通过共享状态通信而不是消息传递**
原因：共享状态更直观——每个Agent只关心自己读什么字段、写什么字段。加新Agent不需要改其他Agent的代码。

**决策3：DeepSeek和MiniMax双模型路由**
原因：成本优化。DeepSeek推理强但贵，MiniMax中文好且便宜。按任务类型分配模型，兼顾效果和成本。

**决策4：MVP阶段用临时目录+subprocess而不是Docker**
原因：快速验证。Docker引入额外复杂度，MVP阶段不需要。后续升级到Docker容器隔离。

**决策5：RequirementAgent硬限制追问轮次**
原因：实测MiniMax不跟对话历史，已经回答过的问题还会重复问。硬限制是必要的工程手段，不能完全依赖Prompt约束。

**决策6：current_stage用Annotated reducer**
原因：并行分支（BackendAgent和FrontendAgent）同时写入current_stage时，需要取最新值而不是覆盖。LangGraph的reducer机制天然解决这个问题。

**决策7：DeployerAgent解析多文件输出用正则**
原因：LLM输出多个文件时，用### path/file和```code```标记是Prompt约定的格式。正则解析简单直接，不需要复杂的结构化输出。

---

## 十、已知限制与改进方向

### 10.1 已知限制

错误恢复粗糙：Agent执行失败直接报错终止，没有重试或降级策略
并行是假并行：Python GIL限制下LangGraph的并行节点实际是并发而非并行
Prompt工程靠经验：每个Agent的System Prompt是手调的，没有系统化评测
状态持久化缺失：_pipelines存内存里，服务重启就丢
沙箱安全有限：MVP阶段用临时目录+subprocess，不是真正的容器隔离

### 10.2 改进方向

错误恢复：Agent执行加retry和fallback模型
真并行：用asyncio.gather或多进程实现真正的并行执行
Prompt评测：引入promptfoo做A/B测试，量化Prompt效果
状态持久化：用Redis替代内存字典
沙箱升级：Docker容器隔离
可观测性：集成LangSmith做调用链追踪
配置热更新：改配置不重启服务

---

## 十一、项目结构

```
ai-dev-platform/
├── src/
│   ├── orchestrator/
│   │   ├── graph.py         # LangGraph状态图定义
│   │   └── state.py         # 共享状态定义（ProjectState + Stage枚举）
│   ├── agents/
│   │   ├── base.py          # Agent抽象基类
│   │   ├── requirement.py   # 需求分析Agent（最复杂，三层防线）
│   │   ├── architect.py     # 架构设计Agent
│   │   ├── backend.py       # 后端代码生成Agent
│   │   ├── frontend.py      # 前端代码生成Agent
│   │   ├── tester.py        # 测试验证Agent
│   │   └── deployer.py      # 打包交付Agent（文件操作+LLM）
│   ├── llm/
│   │   ├── provider.py      # 统一LLM调用（DeepSeek/MiniMax/OpenAI）
│   │   └── prompts/
│   │       ├── requirement.py  # 需求分析Prompt
│   │       ├── architect.py    # 架构设计Prompt
│   │       ├── backend.py      # 后端代码Prompt
│   │       ├── frontend.py     # 前端代码Prompt
│   │       ├── tester.py       # 测试验证Prompt
│   │       └── deployer.py     # 部署打包Prompt
│   ├── sandbox/
│   │   └── executor.py      # 本地沙箱执行器
│   ├── web/
│   │   ├── server.py        # FastAPI + WebSocket服务
│   │   └── static/
│   │       └── index.html   # 前端UI（Cursor风格）
│   └── utils/
│       ├── config.py        # 配置管理（pydantic-settings）
│       ├── logger.py        # 结构化日志
│       └── health.py        # 健康检查
├── tests/
│   ├── conftest.py          # 共享fixtures
│   ├── test_state.py        # 状态管理测试
│   ├── test_base_agent.py   # Agent基类测试
│   ├── test_llm_provider.py # LLM Provider测试
│   ├── test_sandbox.py      # 沙箱测试
│   ├── test_graph.py        # 状态图测试
│   ├── test_e2e_requirement.py  # 需求分析E2E
│   ├── test_e2e_architect.py    # 架构设计E2E
│   ├── test_e2e_backend.py      # 后端Agent E2E
│   ├── test_e2e_frontend.py     # 前端Agent E2E
│   ├── test_e2e_tester.py       # 测试Agent E2E
│   ├── test_e2e_deployer.py     # 部署Agent E2E
│   └── test_e2e_full_flow.py    # 完整流水线E2E
├── docs/
│   ├── architecture.md      # 架构说明
│   └── PROGRESS.md          # 开发进度
├── SPEC.md                  # 需求规格说明书（1021行）
├── CLAUDE.md                # Claude Code项目规范
├── PROGRESS.md              # 开发进度日志
├── pyproject.toml           # 项目配置+依赖
└── .env                     # API Keys（不入git）
```

---

## 十二、启动方式

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 启动Web服务
uvicorn src.web.server:app --host 0.0.0.0 --port 8080 --reload

# 访问
# 主页：http://localhost:8080
# API文档：http://localhost:8080/docs
# WebSocket：ws://localhost:8080/ws
```
