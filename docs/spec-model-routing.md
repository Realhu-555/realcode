# SPEC — 多模型接入与动态切换模块（Model Routing & Failover）

> 给实现方的执行文档。按 Task 顺序实现，每完成一个 Task 必须跑测试全绿再进下一个。
>
> 版本：v1.0 | 日期：2026-08-11 | 作者：realhu / 小莫
> 关联：docs/prd-agent-runtime-upgrade.md（P1 新增）

---

## 一、背景与目标

### 1.1 背景

当前 `src/llm/provider.py` 的 MODEL_MAP 硬编码模型（所有 Agent 固定 deepseek-v4-pro），
存在三个问题：

1. **换模型要改代码**：加模型、换模型必须动 provider.py，不可配置
2. **用户无选择权**：前端无法让用户选择用哪个模型
3. **无故障转移**：主模型挂掉/限流，系统直接失败，没有备用方案

### 1.2 目标

- 模型注册表配置化：新增/修改模型只改 YAML，不改代码
- 统一调用接口：所有 Provider（DeepSeek / MiniMax / OpenRouter / 任意 OpenAI 兼容）走同一套接口
- 用户级路由：前端可选择模型，用户选择 > Agent 默认
- Failover 自动切换：主模型失败自动切备用链，事件可追溯
- 前端提供模型配置与选择 UI

### 1.3 非目标

- 不做模型训练、微调、KV Cache
- 不做多租户模型配额管理（单机版够用）
- 不做模型间自动"最优选择"（只做手动路由 + 故障切换，不做智能路由）

---

## 二、现状分析

| 现状 | 问题 |
|------|------|
| `provider.py` MODEL_MAP: agent_type -> "provider:model" 硬编码 | 换模型改代码 |
| `LLMProvider` 只有 deepseek_client（固定 base_url）和 openai_client（OPENAI_API_KEY） | MiniMax/OpenRouter key 存在但用不上 |
| Agent 内部 `LLMProvider()` 无配置入口 | 无法按用户偏好路由 |
| 重试机制（retry_call）已接入，重试耗尽直接抛错 | 无 fallback 链 |
| .env 已有 DEEPSEEK/MINIMAX/TAVILY/OPENROUTER key | 大部分闲置 |

---

## 三、需求详述

### FR1 模型注册表（YAML 配置）

新增 `config/models.yaml`（可加载，支持缺失时用默认内置模型）：

```yaml
models:
  deepseek-v4-pro:
    label: "DeepSeek V4 Pro"
    provider: openai-compatible
    model: deepseek-v4-pro
    base_url: "https://api.deepseek.com"
    api_key_env: DEEPSEEK_API_KEY
    input_price_per_m: 0.27
    output_price_per_m: 1.10
    capabilities: [chat, tools]

  minimax-2.7:
    label: "MiniMax 2.7"
    provider: openai-compatible
    model: MiniMax-Text-01
    base_url: "https://api.minimax.io/v1"
    api_key_env: MINIMAX_API_KEY
    input_price_per_m: 0.20
    output_price_per_m: 1.00
    capabilities: [chat, tools]

  openrouter-auto:
    label: "OpenRouter 自动"
    provider: openai-compatible
    model: auto
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: OPENROUTER_API_KEY
    input_price_per_m: 0.00
    output_price_per_m: 0.00
    capabilities: [chat, tools]

agent_defaults:
  celve: deepseek-v4-pro
  gongzhonghao: deepseek-v4-pro
  zhihu: deepseek-v4-pro
  xiaohongshu: deepseek-v4-pro
  shenjiao: deepseek-v4-pro
  export: deepseek-v4-pro

fallback_chains:
  deepseek-v4-pro: [minimax-2.7, openrouter-auto]
  minimax-2.7: [deepseek-v4-pro, openrouter-auto]
  openrouter-auto: [deepseek-v4-pro]
```

要求：
- 模型名、base_url、价格全部可配
- api_key 从环境变量读取（不存明文 key 在 YAML）
- `src/llm/models.py` 提供加载器：`load_models() -> ModelRegistry`，带缓存

### FR2 统一调用接口（Provider 改造）

`LLMProvider` 保留对外方法签名（chat / chat_with_tools），内部改造：

1. `_client_for(model_id)`：按注册表配置动态创建 OpenAI 兼容客户端（懒加载 + 缓存）
2. `chat(messages, agent_type, model_id=None)`：model_id 为 None 时用 agent_defaults
3. `chat_with_tools(messages, tools, agent_type, model_id=None)`：同上
4. 现有 `MODEL_MAP` 删除，由注册表 `agent_defaults` 替代
5. 价格从注册表读取，覆盖 cost_tracker 的 DEFAULT_PRICING

### FR3 用户级路由

1. `ContentProjectState` 增加字段：`model_preference: str | None`（None = 用 Agent 默认）
2. `CreateProjectRequest` 增加 `model_preference: str | None`
3. 路由解析优先级：**用户 model_preference > agent_defaults**
4. Agent 调用 provider 时，从 state 读取 model_preference 传入
   - 实现方式：Agent.run(state) 内 `model_id = state.get("model_preference")`，
     传给 `self.llm.chat(..., model_id=model_id)`
5. 未知 model_id 时：记录告警事件，回退 agent_defaults（不抛错）

### FR4 Failover 自动切换

1. 候选链：`fallback_chains[model_id]`，取不到时 `[model_id]`（只有自己）
2. 调用流程：对候选链逐个尝试 → 每个模型内部走 retry_call（重试 3 次）→
   重试耗尽切下一个候选 → 全部失败才抛错
3. 切换事件记录：`cost_tracker.record(success=False, error_type="failover_to:<model_id>")`，
   保证轨迹/成本统计可见
4. 评测 runner 的 `cost_summary.failures` 会自动包含 failover 事件（可追溯）

### FR5 前端模型选择

1. 新 API：`GET /api/v1/models`
   返回 `{"models": [{"id", "label", "capabilities"}], "default": "deepseek-v4-pro"}`
2. 创建项目页（Create/GuidedForm）加"模型选择"下拉框：
   - 选项：默认（DeepSeek V4 Pro）/ MiniMax 2.7 / OpenRouter 自动
   - 选中值随创建请求提交（model_preference）
3. 前端选择持久化在 project state 中（创建后不再改，MVP 够用）

---

## 四、技术方案

### 4.1 新增/修改文件

```
config/models.yaml                    # 新增：模型注册表
src/llm/models.py                     # 新增：注册表加载器 + ModelRegistry
src/llm/provider.py                   # 修改：统一 client 工厂 + 路由 + failover
src/orchestrator/state.py             # 修改：ContentProjectState 加 model_preference
src/web/server.py                     # 修改：CreateProjectRequest + GET /models + 传参
src/agents/*.py                       # 修改：run() 读取 state.model_preference 传给 provider
frontend/src/views/ 或 components/    # 修改：创建页加模型选择下拉
tests/test_model_routing.py           # 新增：单元测试
docs/spec-model-routing.md            # 本文件
```

### 4.2 核心逻辑（provider 改造要点）

```
LLMProvider.chat(messages, agent_type, model_id=None):
    chain = resolve_chain(model_id, agent_type)      # [primary, backup...]
    for mid in chain:
        try:
            return call_with_retry(mid)               # 现有 retry_call 封装
        except Exception:
            cost_tracker.record(error_type=f"failover_to:{next}")
            continue
    raise  # 全部失败
```

### 4.3 MiniMax 模型名说明

MiniMax 兼容 OpenAI 格式，base_url 和 model 名以官方文档为准，可在 models.yaml
直接改（配置化优势）。实现时先用文档默认值，真实调用验证失败再调配置。

---

## 五、验收标准

- AC1: `config/models.yaml` 配置 3 个模型，新增第 4 个模型只改 YAML 不改代码
- AC2: `LLMProvider.chat(agent_type="celve", model_id="minimax-2.7")` 真实调用 MiniMax 成功
- AC3: 用户传 model_preference="minimax-2.7" 创建项目，所有 Agent 使用 MiniMax（可从 cost_tracker.by_agent 的 model 字段验证）
- AC4: 模拟主模型失败（配置错误 base_url 或注入异常），自动切到备用模型，运行成功且
      cost_summary.failures 可见 failover 事件
- AC5: 未知 model_id 不崩溃，回退默认模型
- AC6: `GET /api/v1/models` 返回注册表模型列表
- AC7: 前端创建页出现模型选择下拉，选择后提交生效
- AC8: 现有评测系统不回归：`python -m src.eval.runner --scenarios devgate_form --repeat 1` 成功

---

## 六、实现任务拆分（按序）

| Task | 内容 | 验收 |
|------|------|------|
| T1 | config/models.yaml + src/llm/models.py 注册表加载器 | 加载 3 模型，缺文件回退内置 |
| T2 | provider 改造：统一 client 工厂 + 路由 + failover | AC2/AC4/AC5 单测通过 |
| T3 | state + server API：model_preference 字段 + GET /models | AC3/AC6 |
| T4 | Agent 传参：6 个 Agent run() 读取 model_preference | AC3 端到端 |
| T5 | 前端模型选择下拉 | AC7 |
| T6 | 全量回归：现有 pytest + 评测单场景 | AC8 |
