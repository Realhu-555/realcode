# GIS 智能助手 · 会话上下文管理改造方案

> 参考：Claude Code / Grok Build 的 **auto-compact（自动压缩）** 机制；Grok Build 开源实现见
> `H:\grok\crates\common\xai-grok-compaction`（intra / inter / code_compaction 三层）。
> 配套文档：`docs/GIS-真实引擎接入方案.md`（7.2–7.4 记忆与压缩设计）｜`src/gis_toolkit/agent.py`（现有压缩实现）
> 版本：v1.0 ｜ 日期：2026-09-02 ｜ 作者：胡贞虎

## 0. 一句话结论

Claude Code 能"一个对话连续很长"，靠的不是**放大步数上限**，而是**自动压缩上下文**
（auto-compact）：上下文占用达到模型窗口百分比阈值时，把已发生的内容压缩成摘要、
用 `[system] + [summary] + 最近原文` 重建后续上下文，让对话可以无限延续。

本项目已有滚动摘要的**雏形**，但口径粗糙（估算 token、条数裁剪、无质量校验），
需要按 Grok 的分层压缩思路补齐工程化，才能支撑"生产员半天连续干活"这种长会话。

---

## 1. 从 Grok Build 源码提炼的机制（对照依据）

参考 `H:\grok\crates\common\xai-grok-compaction`，其核心设计：

### 1.1 压缩分三层，目标不同

| 层 | 压缩什么 | 策略 | 对应我们产品 |
|---|---|---|---|
| `code_compaction`（FullReplace，grok-build 用） | **整个会话**（历史 + 本轮步骤） | 全量重写为一条摘要，重建为 `[system]+[summary]`，不留尾巴 | GIS 助手**主要采用**：跨轮长会话 |
| `intra_compaction` | **单次 agent loop 内**累积的步骤轮 | tail-keep：保留近期尾部，压缩更早步骤 | 配合步数上限，防止"单轮几百步"爆上下文 |
| `inter_compaction` | **turn 与 turn 之间**的旧历史 | 分块（chunked）压缩 | 可选的后续增量 |

### 1.2 触发：按上下文百分比，不是按条数

- `trigger_threshold_percent`：**85%**（`last_prompt_tokens / context_window` 超过即触发）；
- `target_threshold_percent`：压到 **50%**（压完回到半仓，留足余量）；
- token 估算由宿主提供可信计数（`ItemTokenCounter`），不用字符数估。

### 1.3 护栏：压缩本身要"值得"且"有效"

- `min_compactable_tokens`（5000）：可压缩量太少不跑，避免压缩的开销 > 收益；
- `min_steps_before_compact`（3）：太早不压；
- `max_reduction_ratio`（0.8）：摘要没把 token 降到原 80% 以下 → **丢弃本次摘要**；
- 退化摘要拒绝（`is_degenerate_summary`）：空/复读/丢关键信息 → 重试或放弃；
- 压缩 LLM 调用独立模型（`compaction_model_name`）、超时、重试，且**失败不阻断主流程**。

### 1.4 安全拆分与状态恢复

- `select.rs` 的 **tool-pair-safe 选择**：切历史窗口起点绝不会落在 `tool` 消息上
  （我们已在 `_history_window` 做对齐，机制一致）；
- 压缩后注入 `<system-reminder>`，把"活跃 agent 状态/当前图层/进行中任务"带回来；
- 摘要强制保留**产物文件名、文件句柄、关键数值**，细节永远从盘上状态恢复。

---

## 2. 现状与差距（对照表）

当前实现集中在 `src/gis_toolkit/agent.py`：

| 项 | 现状 | Grok/Claude 目标 | 差距 |
|---|---|---|---|
| 触发口径 | 估算 token = 字符数 ÷ 3；固定阈值 `COMPACT_THRESHOLD_TOKENS=24000`，80% 预警 | 真实 token 计数；按模型 context 的百分比（85% 触发 / 50% 目标） | 估得不准；不同模型窗口不通用 |
| 压缩对象 | 旧摘要 + 最近 6 条 → ≤300 字新摘要，历史窗口只发最近 `HISTORY_WINDOW_MESSAGES=40` 条 | FullReplace：整段历史重写，`[system]+[summary]+最近原文` 重建 | 我们是"条数截断 + 侧挂摘要"，不是"整体压缩重建" |
| 压缩质量 | 无校验：摘要不缩小/退化也接受 | 缩水率达标校验 + 退化拒绝 + 重试 | 可能"压了等于没压"甚至丢信息 |
| 摘要成本 | 用主对话模型顺带做 | 独立压缩模型、超时、幂等 | 成本/隔离没控制 |
| 触发时机 | 每轮结束后检查一次 | 发送前按当前 prompt 真实占用判断 + loop 内可触发 | 单轮内几百步场景仍然裸奔 |
| 工具对安全 | `_history_window` 起点对齐非 tool（有） | tool-pair-safe 选择器（有） | 已有，保留即可 |
| 状态恢复 | 摘要提示保留产物/图层（提示词层面） | `<system-reminder>` 结构化注入 | 无结构，靠模型自觉 |
| 会话原文保留 | `SESSION_MESSAGE_CAP=200` 全量留存、超限丢弃最旧 | 原文可留档，发送时再压缩 | 持久化可接受，但要与"发送窗口"解耦 |

> 一句话：我们现在是 **"按条数截断 + 手写滚动摘要"**；要做的是 **"按 token 百分比触发的整体压缩（FullReplace）+ 质量护栏 + 可信计数"**。

---

## 3. 目标架构（改造后）

```
每轮结束 / 每次发送前
   └─ token 估算（usage 累计 + 当前 messages 真实计数）
         └─ 上下文占用 ≥ context × 85% ？
               ├─ 是 → 触发 FullReplace 压缩：
               │     ① 选压缩材料：历史全部 + 最近本轮（tool-pair-safe 切分）
               │     ② 独立压缩模型：旧摘要? → 新摘要（保留产物/图层/数值/用户偏好）
               │     ③ 质量校验：退化拒绝 / 缩水率 < 20% 丢弃 / 超时重试
               │     ④ 应用：[system] + 新摘要 + 最近 N 轮原文（窗口起点对齐非 tool）
               │     ⑤ 注入恢复块（当前图层 / 进行中任务 / 上次审批结论）
               └─ 否 → 正常发送
```

### 3.1 落地分层（对齐 Grok 三层）

1. **发送前压缩（本轮改造重点）**：发送给 LLM 的窗口 = `[system 摘要注入] + [最近原文窗口]`，
   压缩发生在后台，用户无感，和 Claude Code 一致；
2. **Loop 内压缩（后续）**：单个 run 若超过 N 步且上下文逼近阈值，在 loop 内压缩已累积步骤，
   从而让"长任务"不再依赖调大 `max_steps` 上限；
3. **Turn 间压缩（可选）**：跨多轮历史的分块压缩服务，量大后再做。

### 3.2 数据模型改造点（代码位置）

| 位置 | 改动 |
|---|---|
| `src/gis_toolkit/session.py` | `messages` 语义改为「原文留档」，新增 `send_window(messages)`（发送时裁剪+摘要注入）；`SESSION_MESSAGE_CAP` 仅约束磁盘留档 |
| `src/gis_toolkit/agent.py` | 替换 `_maybe_roll_summary`/`_roll_summary`：真实 token 计数 + 百分比触发 + FullReplace + 质量校验 |
| `src/gis_toolkit/agent.py` | `_prepare_messages` 组装 `[summary] + [最近窗口]`，窗口起点继续 tool-pair-safe |
| `src/utils/config.py` | `context_window`（随模型）、`compact_trigger_pct=85`、`compact_target_pct=50`、`compact_model`（可空 = 主模型） |
| LLM Provider | 记录每次 `usage`（prompt/completion），支撑真实占用统计 |

---

## 4. 分阶段实施与验收

| Gate | 内容 | 验收标准 |
|---|---|---|
| **C1** | 可信 token 估算：主模型 usage 累计 + 消息级计数；把固定 24000 阈值改为「按当前模型 context × 百分比」 | 同一会话在 128k 与 32k 模型下触发点随窗口缩放；单测覆盖计数 |
| **C2** | FullReplace 压缩：整段历史重写摘要 + `[system]+[summary]+最近 40 条` 发送；保留产物/图层/数值 | 30+ 轮连续任务不爆上下文；历史关键产物引用仍可恢复；`role=tool` 无 400 |
| **C3** | 质量护栏：退化拒绝 / 缩水率校验 / 超时重试；压缩独立模型可配 | 人为构造"压缩前后几乎等长"用例 → 摘要被丢弃重试 |
| **C4** | Loop 内压缩 + 恢复块：单 run 逼近阈值时压缩已累积步骤；注入当前图层/任务状态 | 高步数任务不再靠放大 max_steps；压缩后 Agent 仍知道"当前图层/做了一半的事" |
| **C5** | 长期记忆配合：压缩摘要的关键引用同步进向量记忆（对齐现有 lesson 向量化） | 跨会话能召回"上次任务做到哪、产物在哪" |

> C1→C3 是跨轮长会话的地基（对标 Claude Code 的日常体验）；C4 解决你提的"长任务几百步"；
> C5 让摘要不只服务单会话。

---

## 5. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-09-02 | 长对话 = auto-compact（FullReplace），不是无限放大步数 | Grok/Claude 同款；步数上限仍是防死循环护栏，与压缩正交 |
| 2 | 2026-09-02 | 触发从"固定 token/条数"改为"模型 context 百分比" | 多模型可配（128k/32k/Ollama 本地），口径统一 |
| 3 | 2026-09-02 | 压缩要有质量护栏，压不动/退化就丢弃重试 | 避免"为了压缩而压缩"把有效信息丢掉 |
| 4 | 2026-09-02 | 发送窗口与留档解耦：原文留档，发送时压缩 | 保留可回溯能力，同时控制每次请求成本 |
