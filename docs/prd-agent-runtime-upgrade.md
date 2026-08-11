# PRD — 素宣 Agent Runtime 能力升级（评测 + 可观测性 + 错误恢复）

> 版本：v0.1（草案）
> 日期：2026-08-10
> 作者：realhu / 小莫
> 状态：待评审
> 关联文档：docs/design-agent-orchestration.md、docs/approval-gate-spec.md

---

## 1. 背景与目标

### 1.1 背景

素宣（Suxuan）已具备完整的 6 Agent 营销内容流水线（策略 → 三渠道并行生成 → 审校 → 导出），
编排、审批门、记忆、工具系统均已落地。但当前系统是"功能平台"——能跑通流程，但缺少
**证明它能稳定跑好的能力**。

对齐 Agent Runtime / Harness 岗位的能力模型（Model + Harness = Agent），本次升级为素宣补齐
Harness 层面的四个核心能力：

1. **评测（Eval）**：用指标证明 Agent 完成任务的可靠性
2. **可观测性（Observability）**：看得见每次运行的轨迹、成本和失败点
3. **错误恢复（Recovery）**：LLM/工具调用失败时系统能自己爬起来
4. **上下文管理（Context）**：Token 花销有预算、有监控、有策略

### 1.2 目标

- 建立离线评测系统：一批固定场景，跑完产出指标报告（成功率、工具调用正确率、延迟、成本）
- 全链路可观测：每次运行都有完整轨迹 + Token 成本账单 + 失败定位
- 自动恢复：LLM 调用失败指数退避重试，工具失败可配置重试，关键节点可断点续跑
- Token 预算：每次调用前估算，超限告警并触发截断/压缩策略

### 1.3 非目标

- 不做模型训练、不做 KV Cache、不做分布式调度
- 不做 Prompt 调优本身（只做监控和记录，调优是后续迭代）
- 不做多租户、不做生产级高可用（仍是单机项目，但模块设计要为扩展留口）

---

## 2. 现状盘点

### 2.1 已有能力（本次复用的基础）

| 模块 | 现状 | 复用方式 |
|------|------|----------|
| Agent 编排 | LangGraph StateGraph：策略→追问分支→三路并行→审校→导出 | 不动主链路，只加横切能力 |
| 状态管理 | ContentProjectState（TypedDict + Reducer），ContentStage 枚举 | 扩展字段（cost/trace_id） |
| 审批门 | ApprovalGate：approve/revise/redo，asyncio 等待 + WebSocket 回调 | 不动 |
| 工具系统 | execution/description 分离 + 单例注册表 + 权限隔离 | 在注册表层挂载调用统计 |
| 轨迹追踪 | TraceTracker（trace.py）：记录 LLM 调用、工具结果、final | 扩展 cost 字段 + stage 字段 |
| 记忆 | SQLite 品牌档案 + 项目历史 | 复用存储，新增 eval/run 表 |
| 场景测试 | tests/output/ 多场景 live 测试（summary.json + trace） | 升级为正式评测场景集 |
| 沙箱 | sandbox/executor.py | 评测时的代码执行隔离 |

### 2.2 差距清单（对照 JD）

| JD 要求 | 现状 | 差距 |
|---------|------|------|
| 任务成功率指标 | 无 | 缺评测 runner + 指标计算 |
| 工具调用正确率 | 无 | 缺工具级结果判定（成功/失败/预期匹配） |
| 执行轨迹 | TraceTracker 有雏形 | 缺阶段标注、缺 Token 明细 |
| 延迟 | 无 | 缺每步耗时统计 |
| 成本 | 无 | 缺 Token 计量（输入/输出/按 Agent 维度） |
| 失败定位 | error 状态只有 message | 缺失败节点/工具定位 + 轨迹回放 |
| 错误恢复 | 无 | 缺重试机制、断点续跑 |
| Token 预算 | 无 | 缺调用前估算 + 超限策略 |

---

## 3. 用户故事

- US1：作为开发者，我想对一批固定场景批量跑流水线，得到"成功率 80%、平均耗时 90s、平均成本 0.3 元"的报告，用来判断系统是否可靠。
- US2：作为开发者，我想看到某次失败运行的完整轨迹（哪个 Agent、哪一步、调了什么工具、报了什么错），用来快速定位根因。
- US3：作为开发者，我想看到每次运行花了多少 Token、多少钱，按 Agent 和阶段拆分，用来发现成本黑洞。
- US4：作为使用者，我希望临时网络抖动导致 LLM 调用失败时，系统自动重试而不是直接报错退出。
- US5：作为开发者，我希望流水线因超时/崩溃中断后，能基于已保存的状态从断点继续，而不是从头重跑。

---

## 4. 功能需求

### FR1 评测系统（Eval）— P0

**FR1.1 场景集管理**
- 新增 `src/eval/scenarios/` 目录，每个场景一个 JSON/MD 文件
- 场景字段：`name`、`input_mode`（form/free）、`product_info`、`expected`（可选：期望的策略要点/内容关键词）、`tags`
- 迁移现有 tests/output/ 的场景样例为正式场景集，至少 5 个场景（form 3 + free 2）
- 场景支持"无人工介入模式"：评测运行时自动跳过 ApprovalGate 等待（默认 approve）

**FR1.2 评测 Runner**
- 新增 `src/eval/runner.py`：`run_eval(scenario, config) -> EvalResult`
- 支持单场景跑 N 次（默认 1 次，可配置）取平均
- 支持批量：`python -m src.eval.runner --scenarios all --repeat 3`
- 每次运行复用现有流水线入口（graph），但注入评测配置（无人工等待、超时上限）

**FR1.3 指标定义**
- `success_rate`：任务成功率（完整走到 END 且产出非空 / 总运行数）
- `tool_accuracy`：工具调用正确率（工具执行无异常且结果非空 / 总调用数）
- `latency`：总耗时、每阶段耗时（p50/p95 可选）
- `cost`：总 Token（输入/输出分开）、估算金额、按 Agent 维度拆分
- `trace_completeness`：轨迹完整性（llm_call/tool_results/final 步骤是否齐全）
- 指标计算集中在 `src/eval/metrics.py`，输出统一结构

**FR1.4 报告输出**
- 输出目录 `tests/eval_output/<timestamp>/`：
  - `summary.json`：全部场景指标汇总
  - `report.md`：人类可读报告（场景 × 指标 表 + 失败详情）
  - `runs/<scenario>/trace.json`：单次运行完整轨迹
- 失败场景必须附带：失败节点、失败原因、涉及工具/LLM 调用片段

### FR2 可观测性（Observability）— P0

**FR2.1 Token 成本统计**
- 新增 `src/observability/cost_tracker.py`
- 在 LLM Provider 层（src/llm/provider.py）挂点：每次调用记录 model、prompt_tokens、completion_tokens、耗时
- 支持按 Agent 维度、阶段维度聚合；金额按模型单价配置（config 里加 `model_pricing`）
- 运行结束写入 run 记录（SQLite 新表 `run_metrics`）

**FR2.2 轨迹增强**
- 扩展 TraceStep：增加 `stage`（strategy/generating/review...）、`cost`（该步 Token 明细）、`duration_ms`
- TraceTracker 增加 `summary()` 输出统计信息（现有方法，补全）
- 轨迹文件增加元信息头：`trace_id`、`scenario`、`start/end time`、`total_cost`

**FR2.3 失败定位**
- 新增 `src/observability/failure.py`：从 State 的 error_message + 轨迹中提取失败信息
- 输出结构化失败对象：`{stage, node, tool_name, error_type, message, trace_snippet}`
- 失败对象写入 summary.json / report.md

**FR2.4 Web 展示（可选，P1）**
- 前端新增"运行报告"页：展示最近 N 次运行的成功率、成本、失败列表
- 依赖后端新增 API：`GET /api/runs`、`GET /api/runs/{id}`、`GET /api/runs/{id}/trace`

### FR3 错误恢复（Recovery）— P0/P1

**FR3.1 LLM 调用重试（P0）**
- 在 provider 层包装重试：`async_retry(coro, max_retries=3, base_delay=1.0, max_delay=8.0)`
- 指数退避 + 抖动（jitter），只对可重试错误重试（网络错误、5xx、超时；4xx 不重试）
- 重试次数、每次延迟写入轨迹（trace 中记录 retry 事件）

**FR3.2 工具调用重试（P0）**
- 工具注册表增加 `retry_policy` 配置（默认不重试，个别工具可配 max_retries）
- 重试仅限幂等工具（如 web_search、content_read；content_save 类不重试，避免重复写入）

**FR3.3 断点续跑（P1）**
- 基于 LangGraph 持久化：启用 checkpointer（内存/SQLite 实现），保存每次 checkpoint
- 中断恢复入口：`python -m src.eval.runner --resume <run_id>` 或 API `POST /api/runs/{id}/resume`
- 恢复时从最后一个完成的 checkpoint 继续，跳过已完成阶段
- 与 ApprovalGate 兼容：恢复后若处于等待审批状态，继续等待

### FR4 上下文与 Token 预算（Context）— P1/P2

**FR4.1 Token 预算监控（P1）**
- config 增加 `context_budget`：每 Agent 每轮最大 prompt_tokens（默认如 12000）
- provider 层调用前估算（tiktoken 或近似公式），超限触发 `ContextBudgetExceeded` 告警事件
- 告警事件进入轨迹，不阻断运行（P1 先记录，P2 再做截断动作）

**FR4.2 上下文压缩（P2）**
- 当历史消息超过预算时，将早期消息摘要后替换（`src/context/compressor.py`）
- 摘要采用"保留关键信息"策略：用户输入原样保留，中间过程消息压缩，最近 N 轮保留原文
- 压缩动作写入轨迹（记录压缩前后 Token 数）

---

## 5. 技术方案

### 5.1 新增目录结构

```
src/
├── eval/                    # 评测系统
│   ├── __init__.py
│   ├── runner.py            # 评测运行器（批量/单场景/恢复）
│   ├── metrics.py           # 指标计算
│   ├── scenarios/           # 场景集（JSON）
│   └── report.py            # summary.json + report.md 生成
├── observability/
│   ├── __init__.py
│   ├── cost_tracker.py      # Token 成本统计
│   └── failure.py           # 失败定位与结构化
├── recovery/
│   ├── __init__.py
│   ├── retry.py             # 指数退避重试（LLM/工具通用）
│   └── checkpoint.py        # 断点持久化（P1）
└── context/
    ├── __init__.py
    ├── token_budget.py      # 预算估算与监控
    └── compressor.py        # 上下文压缩（P2）
```

### 5.2 关键设计决策

1. **横切不动主链路**：评测/观测/恢复都以装饰器/挂点方式接入（provider 层、工具注册表、graph 外层），
   不修改 6 个 Agent 的业务逻辑。降低回归风险。
2. **评测复用真实入口**：评测 runner 调用的就是生产 graph，只是注入"无人工等待"配置。
   保证评测结果代表真实能力。
3. **指标先行**：先定指标结构（schema），再写采集代码。所有采集点输出统一格式，报告生成不依赖具体字段。
4. **可重试性声明**：工具在注册时声明 `idempotent: bool`，只有幂等工具允许自动重试。防止重试造成副作用。
5. **SQLite 为 run 记录中心**：新增表 `run_metrics`（run_id, scenario, success, total_cost, latency, error_info, trace_path），
   为 Web 展示和后续分析留数据基础。

### 5.3 数据流

```
场景集 JSON → EvalRunner → 生产 graph（注入评测配置）
                                │
        provider 层挂点 ──→ CostTracker（Token/耗时）
        工具注册表挂点 ──→ ToolStats（调用数/成败）
        TraceTracker ──→ 轨迹（stage/cost/retry 事件）
                                │
                    ┌───────────┴───────────┐
              失败 → failure.py（定位）  成功 → metrics.py（指标）
                    └───────────┬───────────┘
                        summary.json + report.md + run_metrics 表
```

---

## 6. 验收标准

- AC1：`python -m src.eval.runner --scenarios all` 能跑完全部场景，产出 summary.json + report.md，
  且包含 success_rate、tool_accuracy、latency、cost 四项指标
- AC2：评测运行中 ApprovalGate 不阻塞（自动通过），恢复人工模式时行为不变
- AC3：人为模拟 LLM 网络错误（如把 API 地址改成不通的），流水线自动重试 3 次后成功，轨迹中可见 retry 事件
- AC4：运行完成后，trace.json 中每一步都有 stage、duration_ms、cost 字段
- AC5：失败运行时，report 中能定位到失败节点和失败原因，且附带轨迹片段
- AC6：run_metrics 表正确记录每次运行，可查询最近运行列表（API 层 P1 验收）
- AC7：Token 超预算时，轨迹中出现 ContextBudgetExceeded 事件且运行不崩溃
- AC8（P1）：进程中断后，`--resume` 能从断点继续，不重复已完成的 Agent 阶段

---

## 7. 迭代计划

| 迭代 | 范围 | 估时 |
|------|------|------|
| P0-1 | FR1 评测系统（场景集 + runner + metrics + report） | 1 个 Task |
| P0-2 | FR2.1-FR2.3 可观测性（成本 + 轨迹增强 + 失败定位） | 1 个 Task |
| P0-3 | FR3.1-FR3.2 重试机制（LLM + 工具） | 1 个 Task |
| P0 验收 | AC1-AC7 全绿，跑真实场景出报告 | — |
| P1-1 | FR3.3 断点续跑（checkpoint） | 1 个 Task |
| P1-2 | FR2.4 Web 运行报告页 + API | 1 个 Task |
| P1-3 | FR4.1 Token 预算监控 | 1 个 Task |
| P2-1 | FR4.2 上下文压缩 | 1 个 Task |

---

## 8. 风险与依赖

| 风险 | 影响 | 对策 |
|------|------|------|
| 挂点改动影响主链路 | 流水线回归 | 评测/观测全部走挂点，不动 Agent 业务代码；P0 每 Task 跑现有 pytest |
| LangGraph 版本对 checkpointer 支持差异 | 断点续跑延期 | P1 先做调研，用最小示例验证后再集成 |
| DeepSeek API 计费字段格式变化 | 成本统计失真 | CostTracker 对未知字段容错，缺失时按 0 计并标记 unknown |
| 重试导致重复副作用 | 内容重复写入 | 仅幂等工具可重试，content_save 类强制不重试 |
