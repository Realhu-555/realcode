# GIS 智能助手 — 结果审核模块设计文档（Marvis 交接）

> 用途：实现方（Marvis）按本文档开发「结果审核」能力；完成后由 Codex 按第 10 节逐项审计验收。
> 版本：v0.1（设计稿）｜ 日期：2026-08-25 ｜ 工作目录：`H:\ai-dev-platform`（分支 `feat/gis-mcp-server`）
> 背景：2026-08-25 实测发现 LLM 在 `finish` 汇报中给出「全国 GDP 合计约 12.6 万亿元」（实际约 126 万亿，差 10 倍）——结论数字未经核实。

---

## 1. 目标与范围

**一句话**：给 GIS 助手加一道「结果审核」：任务结束后自动核对 **AI 汇报的数字与工具返回/产物是否一致**，不一致给出 WARN/FAIL 与证据，FAIL 可回主 Agent 修正。

**两层设计（先 A 后 B）**
- **A. 规则校验（L1，确定性、零 LLM 成本，必做）**：统计类工具返回里带「关键统计」（`stats`），`finish` 后用规则断言核对 `final` 中的数字；
- **B. 审核 Agent（L2，LLM 复核，增强）**：独立审核器读轨迹 + 产物摘要，输出 `PASS / WARN / FAIL` + 原因，FAIL 回主 Agent 重写汇报（限 1–2 轮）。

**本期不做**
- 不做视觉读图审核（图内容是否符合预期，留给后续评测）；
- 不做自动回滚工具操作（审核只作用于「汇报文本」，不改已生成产物）；
- 不做多 Agent 编排改造（审核器是独立模块，不进入主工具循环）。

---

## 2. 现状盘点（已可复用）

| 资产 | 位置 | 现状 |
|---|---|---|
| 产物文件校验（存在/非空/可读/有数据） | `src/gis_toolkit/checker.py::check_outputs` | ✅ 已有，仅文件级 |
| 工具执行 + 校验接入点 | `agent.py::_execute_with_check`（`max_check_retries=3`） | ✅ 已有，接产物校验 |
| 主 Agent 工具循环 | `agent.py::GisToolAgent.run / run_stream` | ✅ 已有 |
| `finish` 工具（`outputs` + `summary`） | `engine.py::finish`、`schemas.py` | ✅ 已有 |
| 轨迹落盘 | `agent.py::_save_trace`（`data/gis_traces/`） | ✅ 已有 |
| 评测集（可复用断言） | `docs/GIS-Agent基准评测集扩展方案.md`（L1 引擎级断言） | 设计稿 |

**缺什么（本期开发）**
- 工具返回里的可核对统计（`stats`）；
- `final` 数字与 `stats` 的规则断言；
- L2 审核 Agent（独立 LLM 调用）；
- 审核结果落轨迹 + 前端展示 + done 事件字段。

---

## 3. 触发场景（验收锚点）

实测案例（必须能被本模块抓出）：
> 用户加载 `data/gis_demo/gdp_demo.csv`（31 省真实 GDP），要求分级设色 + 汇总。
> `summarize` 正确产出 CSV（31 省合计约 126 万亿）。
> LLM 的 `finish.summary` 却写「全国 31 省 GDP 合计约 12.6 万亿元」——**量级错 10 倍**。

期望：L1 规则能抓出（`final` 中的「12.6」与 `stats.total`（约 126.xx）不一致 → FAIL）；L2 审核给出证据并触发一次修正。

---

## 4. 总体架构

```
任务结束（finish 后，final 已生成）
        │
        ▼
┌──────────────────────────────────────────────┐
│ L1 规则校验（无 LLM，确定性）                   │
│  validate_final_numbers(final, trajectory)    │
│   ├─ 从 trajectory 提取各工具 stats            │
│   ├─ 从 final 提取数字（正则/数字短语）          │
│   ├─ 数字可在 stats 中找到 → 通过               │
│   ├─ 找不到 → WARN（疑似未引用）                 │
│   └─ 找到但值不一致（如 12.6 vs 126.xx）→ FAIL  │
└──────────────────┬───────────────────────────┘
                   ▼
┌──────────────────────────────────────────────┐
│ L2 审核 Agent（仅 L1=WARN/FAIL 或产物非空时）   │
│  ResultAuditor.audit(...)                    │
│   输入：user_request / final / trajectory摘要 │
│         / stats / 产物清单                    │
│   输出：{verdict, reasons[], suggestions[]}   │
│   verdict ∈ PASS / WARN / FAIL               │
└──────────────────┬───────────────────────────┘
                   ▼
        FAIL（且修正轮次 < 2）→ 主 Agent 带审核意见重写 final
                   ▼
        done 事件附带 audit_report → 前端展示 → 落轨迹
```

**关键设计原则**
- **L1 先拦截、L2 复核**：能规则化的问题不让 LLM 判（省钱、可复现）；L2 只处理规则判不动的语义问题；
- **审核不改产物**：只针对 `final` 汇报文本；产物文件已生成，不重跑工具；
- **独立上下文**：L2 用自己的 prompt + 独立 `messages`，不进主对话历史；
- **成本可控**：仅当有产物且 L1 非全 PASS 时才跑 L2；L2 修正轮次硬上限 2。

---

## 5. L1 规则校验设计

### 5.1 工具返回扩展：`stats` 字段

统计/数值类工具在返回 dict 中增加 `stats`（可核对的关键数字），其余工具不强制：

| 工具 | stats 内容 |
|---|---|
| `summarize` | `{"total": <agg 合计>, "rows": N, "group_count": M, "top3": [{"k": "...", "v": x}×3]}`（`total` 仅当 agg 为 sum/mean 时给） |
| `field_statistics` | `{"count": N, "min": x, "max": x, "mean": x, "sum": x}` |
| `unique_values` | `{"count": N}` |
| `load_data` | `{"rows": N}` |
| `summarize`（count） | `{"total": N, "rows": N}`（count 的 total = 行数） |

实现：`engine.py` 的 `summarize`/`field_statistics`/`unique_values` 在返回 `_result(...)` 时带上 `stats`（从真实计算结果取，不额外读文件）。`stats` 里的数字**必须来自工具执行结果**，禁止 LLM 生成。

### 5.2 `final` 数字提取

`validate_final_numbers(final, trajectory)`：
1. 从 `trajectory` 汇总所有工具返回的 `stats`，得到 `known = {数字值: 来源说明}`；
2. 从 `final` 提取候选数字：
   - 简单正则 `\d+(\.\d+)?`（过滤年份/坐标/编号等噪声：年份 19xx/20xx、经纬度范围外的数）；
   - 中文字数词（如「12.6 万亿」「十三点五万亿」→ 归一化为万亿单位数字）；
3. 每个候选数字与 `known` 匹配：
   - **精确匹配**（容差 0.5% 内）→ 通过；
   - **量级匹配**（如 12.6 与 126，差 10^x 倍）→ **FAIL**（量级错误，如本次案例）；
   - **单位换算匹配**（final 写「13.56 万亿」= stats 的 135673.2 亿）→ 通过（单位换算表：亿/万/万亿）；
   - **找不到且是「结论性大数」**（>100 且出现在"合计/总共/总量"附近）→ **WARN**；
4. 返回 `{"verdict": "PASS|WARN|FAIL", "issues": [{"number", "expected", "reason"}]}`。

### 5.3 接入点

`agent.py` 在生成 `final` 后、`_emit(done)` / `_save_trace` 之前：
```python
audit = validate_final_numbers(final, trajectory)   # L1，纯函数
```
L1 `FAIL` 且未调用过 finish 才修正；已调 finish 则只记录。

---

## 6. L2 审核 Agent 设计

### 6.1 新模块 `src/gis_toolkit/auditor.py`

```python
@dataclass
class AuditReport:
    verdict: Literal["PASS", "WARN", "FAIL"]
    reasons: list[str]      # 每条给证据（引用了哪个 stats / 哪个产物）
    suggestions: list[str]  # 修改建议（给主 Agent 或用户）
    rounds_used: int

class ResultAuditor:
    def __init__(self, llm: LLMProvider | None = None, max_rounds: int = 2): ...
    def audit(self, user_request: str, final: str, trajectory: list[dict],
              stats: dict[str, Any], outputs: list[str]) -> AuditReport: ...
```

### 6.2 审核 Prompt（要点）

审核器 system prompt 要求：
- 角色：独立的 GIS 结果审核员，**只依据提供的工具返回与产物清单**，不依赖外部常识；
- 检查项：请求是否完成；`final` 中的每个数字能否在工具返回中找到（给出引用）；有无编造的结论；产物清单与 `finish.outputs` 是否一致；
- 输出格式：`---AUDIT_START---` 结构化 JSON（`verdict / reasons / suggestions`），`verdict` 取值 PASS/WARN/FAIL；
- 禁止：改写结论；只判不改。

### 6.3 FAIL 修正回环

- `verdict=FAIL` 且 `rounds_used < max_rounds`：把 `audit_report`（reasons + suggestions）追加进主 Agent 的 messages（作为 tool 风格的审核意见），让主 Agent **只重写 final 文本**（重新调 `finish`），不重跑工具；
- 修正后重新 L1 + L2，最多 2 轮；
- 达到上限仍 FAIL：保留最后一次结果，`audit_report.rounds_used` 标记耗尽。

### 6.4 与 L1 的关系

| 场景 | L1 | L2 |
|---|---|---|
| `final` 无结论数字、产物齐全 | WARN | 跑（确认语义是否完整） |
| 数字量级错（12.6 vs 126） | FAIL | 跑（给证据 + 修正） |
| 数字全部可溯源 | PASS | 不跑（省成本） |
| 无产物（空任务） | 跳过 | 不跑 |

---

## 7. 事件与前端

### 7.1 `done` 事件扩展

```json
{
  "type": "done",
  "final": "...",
  "outputs": [...],
  "steps": 12,
  "timed_out": false,
  "audit_report": {
    "verdict": "WARN",
    "reasons": ["..."],
    "rounds_used": 1
  }
}
```

- `audit_report` 缺失 = 未启用审核（向后兼容）；
- 前端在 final 文本下方渲染徽标：🟢 PASS / 🟡 WARN（展开 reasons）/ 🔴 FAIL（reasons + 「已尝试修正 N 轮」）。

### 7.2 轨迹落盘

`_save_trace` 写入 `audit_report` 字段，供回放与评测集使用。

---

## 8. 安全与成本

1. **成本**：L1 零 LLM；L2 仅「有产物且 L1≠全 PASS」时跑 1 次；修正回环 ≤2 轮，每轮只重写 final 不重跑工具；
2. **不扩大权限**：审核器是只读的（读轨迹/产物路径），不触发任何工具；
3. **不误导用户**：`final` 修正后仍保留原始版本于轨迹（`final_v0` / `final_v1`），可追溯；
4. **防注入**：`final`/轨迹文本进审核 prompt 前截断（各 ≤6000 字符）。

---

## 9. 测试与验收

### 9.1 单元测试 `tests/test_auditor.py`

1. `validate_final_numbers`：精确匹配通过；12.6 vs 126 判 FAIL；万亿/亿单位换算通过；无数字结论判 WARN；
2. `stats` 生成：`summarize`（sum/count）返回正确 `total/top3`；`field_statistics` 各统计值；
3. `ResultAuditor.audit`：mock LLM 返回 PASS/WARN/FAIL 三分支；JSON 解析容错（markdown 包裹）；
4. 修正回环：FAIL → 重写 → PASS（1 轮）；连续 FAIL 达 `max_rounds` 终止；
5. 向后兼容：无 `stats` 的旧工具返回不报错。

### 9.2 验收锚点（必须复现）

构造 `final = "全国 GDP 合计约 12.6 万亿元"` + `stats.total = 126.xx`（万亿口径）：L1 必须判 FAIL，L2 给出「量级不一致」原因。

### 9.3 前端验证

`npm run build` 通过；playwright 打开页面跑出图任务，确认 done 后徽标渲染、WARN/FAIL 可展开原因。

### 9.4 手工验收清单

- [ ] 正常任务（数字可溯源）→ PASS，无打扰；
- [ ] 构造错误量级 → FAIL，前端显示红色徽标 + 原因 + 修正轮数；
- [ ] 多轮会话第二、三轮也带审核；
- [ ] 审核结果在 `data/gis_traces/*.json` 可见；
- [ ] 全量回归无新增失败。

---

## 10. 开发任务拆分（按提交顺序）

### P0 — L1 规则校验（先合入）
1. `engine.py`：`summarize` / `field_statistics` / `unique_values` 返回增加 `stats`；
2. `src/gis_toolkit/validate.py`：`validate_final_numbers`（数字提取 + 匹配 + 量级/单位换算）；
3. `agent.py`：finish 后调用 L1，`done` 事件与轨迹带 `audit_report`（L1 部分）；
4. 单测 `tests/test_validate.py`。

### P1 — L2 审核 Agent
5. `src/gis_toolkit/auditor.py`：`ResultAuditor` + 审核 prompt；
6. `agent.py`：FAIL 修正回环（≤2 轮，只重写 final）；
7. 单测 `tests/test_auditor.py`。

### P2 — 前端与评测接入
8. `done` 事件 `audit_report` 前端渲染（PASS/WARN/FAIL 徽标 + reasons）；
9. `docs/GIS-Agent基准评测集扩展方案.md` 的 L2 任务验收增加「审核通过」维度；
10. 构建同步 + 手工验收。

---

## 11. 开发规范（沿用）

1. **测试不过不准提交**：`scripts\check.bat` 全绿（ruff + pytest）；
2. **提交信息**：`<type>(<scope>): <描述>`；
3. **禁止提交**：`data/projects.db`、`long_term_memory.db`、`CLAUDE.md`、日志、`data/gis_*` 产物目录；
4. **风格**：中文注释；公共函数类型注解；行宽 ≤100；
5. **分支**：继续在 `feat/gis-mcp-server` 或建 `feat/result-audit` 并保持可合并。

## 12. 验证命令

```bash
venv\Scripts\python.exe -m pytest tests/test_validate.py tests/test_auditor.py -q
venv\Scripts\python.exe -m pytest tests -q --basetemp=.pytest_tmp\basetemp   # 全量回归
venv\Scripts\python.exe -m ruff check src tests
cd frontend && npm run build
venv\Scripts\python.exe .pytest_tmp\sync_frontend.py
```

## 13. 审计检查点（Codex 验收标准）

1. **变更说明**：改了哪些文件、新增 API/字段、对应验收项；
2. **测试证据**：`test_validate.py` / `test_auditor.py` 全过 + 全量回归无新增失败；
3. **验收锚点**：12.6 vs 126 案例在单测中 FAIL 成立；
4. **成本边界**：L2 只在该跑时跑、修正 ≤2 轮、无产物不跑；
5. **兼容性**：无 `stats` 旧工具不报错；`done` 无 `audit_report` 时前端不异常；
6. **前端**：徽标渲染正确，构建产物已同步 `src/web/static/`。
