# GIS 智能操作助手 — 项目深度理解与面试速查

> 用途：在面试/答辩/对外介绍前快速复习，确保「被问到任何设计细节都能答上来」。
> 版本：v2.0 ｜ 日期：2026-09-02 ｜ 分支：`feat/gis-mcp-server` ｜ 配套文档见文末「文档地图」。
> v2.0 变更：新增 Settings 模块（模型管理 / API Key 前端配置 / 添加模型页）、结果审核 L1+L2、记忆向量化完成、测试 407、data 移出版本控制。
> 核心原则：**所有结论都能指向代码文件或设计文档，不靠记忆编造**。

---

## 0. 一句话定位

> **自然语言驱动的 GIS 智能操作助手**：用户用一句话让助手完成「读数据 → 空间分析 → 出图/出数据 → 编辑要素/管理图层/定制样式/工程管理」的完整 GIS 工作。LLM 是大脑（规划 + 决策），GIS 引擎是手脚（真正执行），每一步工具调用都落成**可审计轨迹**。

三个关键词：
- **操作型主线**：不是「代写脚本」，而是像人一样一步步操作 GIS 系统（加载图层、做缓冲、改属性、提交编辑）；
- **双入口**：自研 Agent（Web 对话）+ dsh/MCP（桌面助手）共用同一套引擎与工具 schema；
- **人在回路（HITL）**：危险操作（增删改要素、覆盖产物）必须经人工审批，默认超时拒绝。

---

## 1. 技术全景（30 秒版）

```
Web 前端（Vue3 + Naive UI，SSE 流式 + 设置抽屉 + 添加模型页 /gis/models/add）
        │  /api/v1/gis-assistant/run/stream
        ▼
FastAPI 后端（src/web/server.py）
        │
        ▼
GisToolAgent（src/gis_toolkit/agent.py）—— 单 Agent 工具循环
   ├─ LLMProvider（src/llm/provider.py）  DeepSeek function calling（模型可切换/可配置）
   ├─ ApprovalGate（src/gis_toolkit/approval.py）  HITL 审批门
   ├─ 记忆：短期滚动摘要 + LongTermMemory（长期 lesson 向量检索）
   └─ TOOL_SCHEMAS（src/gis_toolkit/schemas.py）  41 个工具，表驱动
        │
        ▼ 任务结束自动过结果审核
结果审核（src/gis_toolkit/validate.py + auditor.py）
   ├─ L1 规则校验：final 数字与工具返回 stats 核对（零 LLM 成本）
   └─ L2 审核 Agent：独立复核，FAIL 回主 Agent 修正（≤2 轮）
        │
        ▼
GIS 引擎抽象层（接口契约不变，实现可换）
   ├─ GisEngine（geopandas，默认，GIS_ENGINE 未设）
   └─ QgsEngine（QGIS/PyQGIS，GIS_ENGINE=qgis 切换）
        │
        ▼
产物：PNG / GeoJSON / CSV / 工程文件 → 输出目录 → 前端可下载

模型管理（Settings）：config/models.yaml ⊕ user_models 表；内置模型 key 前端写 .env
```

关键路径速查：

| 模块 | 路径 | 作用 |
|---|---|---|
| 后端 | `src/web/server.py` | FastAPI + SSE 流式 + 会话/审批/产物 API |
| 引擎（默认） | `src/gis_toolkit/engine.py` | geopandas 实现全部工具 |
| 引擎（QGIS） | `src/gis_toolkit/qgis_engine.py`、`qgis_worker.py` | 同接口实现，`GIS_ENGINE=qgis` 切换 |
| Agent | `src/gis_toolkit/agent.py` | 工具循环 + 审批门 + 校验 + 上下文压缩 |
| 工具注册 | `src/gis_toolkit/schemas.py` | `TOOL_SCHEMAS` 表驱动，新增即暴露给 MCP 与自研 Agent |
| 审批 | `src/gis_toolkit/approval.py` | `ApprovalGate`，模式 `readonly/auto/ask` |
| 用户设置/模型 | `src/gis_toolkit/user_settings.py` | 用户偏好 + `user_models` + `.env` key 写入 |
| 结果审核 L1 | `src/gis_toolkit/validate.py` | `validate_final_numbers` 规则核对 |
| 结果审核 L2 | `src/gis_toolkit/auditor.py` | `ResultAuditor` 独立复核 + 修正回环 |
| 会话 | `src/gis_toolkit/session.py` | 图层状态 + 对话历史 + 权限模式 |
| 记忆 | `src/orchestrator/long_term_memory.py` | `LongTermMemory`（lesson / LTM hint） |
| 前端 | `frontend/` → `src/web/static/` | `GisAssistant.vue` + `AddModel.vue` + 路由 `/gis/models/add` |
| 质量门 | `scripts/check.bat`、`scripts/smoke.py` | ruff + pytest + 冒烟 |

---

## 2. 演进历程（为什么做这个项目）

### 2.1 从「营销内容多 Agent 平台」转向「GIS 智能操作平台」

原项目是生成公众号/知乎/小红书三篇内容的平台，三个致命问题：
1. **产物不实用**：生成的是文字，不能自动发布，没有数据回流闭环；
2. **不贴岗位**：目标岗位是「空间数据智能问答 + GIS 软件智能操作」；
3. **撞车**：通用 Web 应用生成方向竞争不过 v0 / Bolt / Cursor。

### 2.2 从「脚本生成（MVP）」升级为「工具调用」

第一版 MVP（`SPEC-GIS智能操作平台.md`）是**脚本生成**形态：LLM 产出一整段 GeoPandas 脚本 → 沙箱整段执行 → checker 事后校验。它有三个结构性限制：
1. **没有可审计的操作序列**：中间决策不可见、不可干预；
2. **验证靠「结果对」反推**：checker 只能核对产物，无法确认每一步操作是否有意义；
3. **离「GIS 系统助手」很远**：真正的助手是操作 GIS 系统，不是代写脚本。

于是演进为现在的**工具调用**形态：`GisToolAgent` 通过 function calling 直接操作 GIS 引擎，**每一步的参数与返回都是轨迹 = 证据**。这直接回答「怎么知道他会不会操作 GIS 工具」。

### 2.3 内容生成模块为什么删了

项目定位已彻底切换为「GIS 智能操作助手」，原来营销内容生成链路（三渠道 Agent、审校 Agent）与岗位、产物闭环无关，已移除，不复用。

---

## 3. 核心设计决策（面试重灾区，每个都要能讲出「为什么」）

### 3.1 为什么是「工具调用」而不是「脚本生成」

- 轨迹即证据：`(工具名, 参数, 返回摘要)` 全量落轨迹，可回放、可评测、可审计；
- 可干预：中间每步都能挂起（如危险操作审批），脚本是一次性黑盒；
- 贴近真实形态：未来嵌入 QGIS 时，agent 的操作方式不变；
- 工具级自愈：单工具返回 `status=error` 时，LLM 依据错误信息修正重试，不需要 checker 回环。

### 3.2 为什么是「单 Agent 工具循环」而不是多 Agent 编排

这是面试最可能被挑战的点，标准答法：
- GIS 任务本质是**单线程决策链**：加载数据 → 看字段 → 算 → 出图，每一步依赖上一步结果，**串行且决策密集**，没有可并行的子任务；
- 多 Agent 的收益来自「独立子任务并行 + 专职化」，对 GIS 链路收益低、成本高（每个子 Agent 都要吃一遍上下文和 token）；
- 单 Agent + 工具循环足够：`思考 → 调工具 → 观察结果`，加 `max_steps=12` 上限和校验重试兜底；
- 预留了扩展点：`execute_subtask()` / `sub_agent` 接口（T9），复杂任务（大数据量分析、权限边界隔离）时可注入子任务执行器，**不需要推翻主架构**。

> 补充：项目早期其实做过 LangGraph 多 Agent 流水线（plan → design → codegen → sandbox → checker → export），那套是「脚本生成 MVP」的形态，工具调用版是单 Agent。两条路线各有适用场景——**脚本生成适合重产出、可整段执行的批处理；工具调用适合重决策、可干预的交互式操作**。

### 3.3 为什么用「双引擎」设计（geopandas + QGIS）

- **接口契约不变，实现可换**：`GisEngine` 和 `QgsEngine` 同名方法、同返回协议；工具 schema 完全不依赖具体引擎；
- 这样做的收益：先用 geopandas 快速验证 agent 与工具链路（零安装成本、可单测），再逐步替换为真实 QGIS 引擎；
- 切换方式：环境变量 `GIS_ENGINE=qgis`，agent 与前端无感；
- QGIS 接入分两路径：路径 A = QGIS Server / `qgis_process` 无头服务（先做）；路径 B = PyQGIS 插件嵌入桌面（宿主形态，后续）；
- 为什么不用「找开源 GIS 系统」：开源 GIS 主流是「三层四家」（GeoPandas/PostGIS → GeoServer/MapServer → QGIS → MapLibre），选型结论是宿主选 QGIS；写工具描述需要的是**官方 API 文档 + 本地实测**，不是源码。

### 3.4 为什么工具注册是「表驱动」

`TOOL_SCHEMAS` 是一份声明式清单，三个消费方自动同步：
- 自研 Agent 的工具列表；
- MCP server 的 `gis_*` 工具（`src/gis_mcp/tools.py` 遍历映射）；
- 前端展示/校验。

新增工具五步走：`schemas.py` 加 schema → `engine.py` 实现 → `qgis_engine/qgis_worker` 同步实现 → MCP 自动暴露 → 单测。**一处定义、三端生效**，不会出现「Agent 有、MCP 没有」的漂移。

### 3.5 为什么工具只返回 JSON 摘要，不给对象

- LLM 永远拿不到 `GeoDataFrame` 内部对象，只拿到 `{rows, columns, crs, geometry_type, bounds, 样例}`；
- 强制 LLM「先 inspect 再决策」，轨迹因此更可读；
- 摘要控制在几百字节内，避免撑爆上下文、控制 token 成本；
- 引擎内部状态隔离，安全边界清晰。

### 3.6 为什么双入口（自研 Agent + dsh/MCP）

- 用户实际使用的入口是桌面助手（dsh/Marvis）和 Web 两种形态，MCP 是行业标准协议，能让第三方 AI 直接调用我们的 GIS 能力；
- 同一套 schema 保证两入口能力完全一致；
- HITL 审批在 MCP 入口的同步是后续 P3 项（`dsh-接入方案.md` 有设计）。

---

## 4. 记忆系统设计（Gate 4 相关）

### 4.1 短期记忆：滚动摘要压缩（已实现）

| 参数 | 值 | 含义 |
|---|---|---|
| `COMPACT_THRESHOLD_TOKENS` | 24000 | 会话历史估算 token 的硬阈值 |
| `COMPACT_WARN_RATIO` | 0.8 | 达到阈值的 80% 就**提前**触发摘要（主动压缩，不等到爆） |
| `HISTORY_WINDOW_MESSAGES` | 40 | 发给 LLM 的最近消息条数（约 5~10 轮） |

机制：`_maybe_roll_summary()` 用 LLM 把「旧摘要 + 最近对话」合并为 ≤300 字新摘要（必须保留产物文件名、图层状态、关键数值、用户偏好），然后裁剪历史窗口。

细节亮点（可讲）：
- **提前压缩而非爆了才压缩**：估算 token 达到 80% 阈值即触发，避免上下文一次性逼近硬上限导致长对话质量劣化；
- **窗口对齐防 400**：`_history_window()` 裁剪时向前扩展对齐到非 tool 消息，否则 `role=tool` 消息没有前导 `tool_calls` 会触发「Messages with role 'tool' must be a response to a preceding message with 'tool_calls'」报错——这是实际踩过并修掉的坑；
- **摘要失败不阻断**：`_maybe_roll_summary` 内 `try/except`，摘要失败下次再试，不中断会话。

### 4.2 长期记忆（向量化已实现）

- 机制：lesson 用字符 n-gram 哈希特征向量（256 维）+ 余弦相似度做 top-k 语义召回；Agent 构建时注入 `ltm_hint`；
- 为什么这样设计：长期记忆的目的是**跨会话召回**（比如上次的成果引用、用户偏好、踩过的坑），用向量检索是为了「相关才注入」，而不是把全部历史塞进 prompt 烧 token。

### 4.3 记忆设计的取舍（可主动讲）

- 短期靠压缩保留「最近细节」，长期靠向量检索保留「历史结论」，两者互补；
- 摘要必须结构化字段（产物、图层、数值、偏好），否则压缩后信息丢失不可逆；
- 阈值是估算 token（`字符数 // 3`），成本低、足够准，不必引入真实 tokenizer。

---

## 5. 安全与合规（HITL 是项目亮点）

### 5.1 审批门 `ApprovalGate`

- 三种权限模式：`readonly`（全拒）/ `auto`（自动放行）/ `ask`（询问，默认）；
- 危险工具注册表 `DANGEROUS_TOOLS`（8 项）：`add_features`、`update_features`、`update_geometry`、`delete_features`、`commit_edits`、`overwrite_output`、`calculate_field`、`remove_layer`；
- `ask` 模式下：危险操作前置检查返回 `pending_approval` + `approval_id`，前端弹审批卡片，`wait_for_approval()` 阻塞等待；`approve` / `reject` / `timed_out`；
- **超时默认拒绝**（`APPROVAL_TTL_SECONDS=60`）——这是从旧 MVP 就修正过的坑：原实现超时默认放行，对危险操作是反的；
- 只读模式全拒，保证「只问不答」场景零风险。

### 5.2 安全边界（可逐条报）

- **路径白名单**：输入文件只允许 `data/` 根目录内的路径，禁止 LLM 臆造路径；
- **产物文件名净化**：只允许 `[\w.\-]+`，一律写引擎输出目录；
- **上传限制**：≤10MB，只读输入（不写回源数据）；
- **沙箱 AST 扫描**（MVP 阶段）：生成的脚本必须通过 AST 静态扫描（禁 `os.remove` 等危险调用），未通过不执行直接重写；
- **引擎异常兜底**：单工具抛异常不中断整个会话，返回 `status=error` 让 LLM 自愈；
- **审核轨迹**：全部工具调用 `(工具名, 参数, 返回)` 落轨迹，可回放审计。

---

## 6. 成本控制与防死循环（重点讲法）

| 机制 | 数值/方式 | 目的 |
|---|---|---|
| 步数上限 | `max_steps=12` | 防 agent 无限循环烧 token |
| 校验重试上限 | `max_check_retries=3` | checker 不过最多重试 3 次 |
| 历史窗口 | 最近 40 条消息 | 控制每次请求的输入规模 |
| 滚动摘要 | 80% 阈值提前压缩 | 长对话不爆上下文 |
| 工具返回摘要 | 几百字节 JSON | 观察结果不撑爆上下文 |
| 错误自愈 | `status=error` 由 LLM 修正 | 避免无效重试 |
| 终止条件三选一 | finish 工具 / 无工具调用 / 步数上限 | 正常结束路径 |

**死循环兜底**（可主动讲）：三层——工具级错误自愈（不重复同样错误）、步数硬上限（`timed_out=True` 返回）、checker 重试上限。不存在无限重试的路径。

---

## 7. 错误处理与排查

### 7.1 运行期错误处理链

1. 引擎层：`GisEngineError` → 返回 `{status: error}`；
2. Agent 层：`except Exception` 兜底 → `工具执行异常: ...`，不让单工具异常中断会话；
3. LLM 层：工具返回 error 后由 LLM 依据 error 信息修正参数重试；
4. 超时/上限：`timed_out=True`，返回已完成的轨迹和部分产物。

### 7.2 排查手段

- 每次会话的 `trajectory`（步骤、工具、参数、结果）落 `data/gis_traces/`，可回放定位是「哪一步、什么参数、返回什么」出的问题；
- 后端日志：`agent_logger` 结构化记录每次 tool_call 的 step/tool/status/rows；
- 测试门：`scripts/smoke.py` 冒烟 + pytest 全量回归。

### 7.3 已踩过的坑（面试加分素材）

- `role=tool` 消息没有前导 `tool_calls` 导致 400：通过 `_history_window` 对齐修复；
- 审批超时默认放行是反向的：改为默认拒绝；
- fake agent 没接 `approval_gate` 参数导致 API 测试失败：已修（fake 构造补默认参数）；
- ruff 0.16.3 全量格式化 + UP038 现代化：已完成（单独 style 提交）；
- 结论数字幻觉（12.6 vs 126 万亿）：prompt 约束是软约束，最终靠 L1 规则校验 + L2 审核兜底；
- 设置改默认权限后前端新会话不跟随：修复为新会话读取用户设置（免刷新）。

---

## 8. 评测体系（benchmark）

方案文档：`docs/GIS-Agent基准评测集扩展方案.md`（v1.1）

两层评测：

### L1 工具正确性（引擎级，无 LLM 成本）
- 直接对引擎断言「合格数据」：行数、字段、几何、CRS、产物文件；
- 不经过 LLM，纯确定性，可进 CI；
- 含**故意损坏的反例**，验证断言能捕获真实失败。

### L2 E2E 真实 LLM 任务
- 15 个任务：10 个单工具（A–D 类）+ 5 个组合任务（E1–E5）；
- 组合任务覆盖「不同工具在同一个任务里串行配合」的真实场景（对应你提的建议：评测口径要具体、任务要复合）；
- 报告维度：pass-rate、coverage、avg-steps、fail-reasons；
- 审核通过维度（已落地）：bench 记录 `audit_pass`/`audit_verdict`，报告审核通过率。

### 为什么评测口径要「合格数据」而不是「工具可调用」

工具可用 ≠ 返回合格数据（可能空几何、错 CRS、字段被吞）。L1 用引擎级断言量化「合格」，L2 用真实任务验证「agent 会不会用」。

---

## 9. 工程化与上线

- 运行：`start.bat` 启动后端（`http://localhost:8080`），前端为构建产物（`src/web/static/`）；
- 质量门：`scripts/check.bat` = ruff check + ruff format + pytest；`scripts/smoke.py` 工具链路冒烟；
- 测试现状：pytest 407 通过全绿；冒烟通过（`smoke.py` PASSED）；
- 提交规范：`<type>(<scope>): <描述>`，type ∈ feat/fix/docs/style/refactor/test/chore；
- 禁止入库：`data/` 已整体移出版本控制（测试数据不入 git、本地保留）；`long_term_memory.db`/`CLAUDE.md`/日志/轨迹等继续忽略；
- 上线方案：`docs/GIS-助手工程化与上线方案.md`（配置/密钥管理、结构化日志、健康检查、干净环境部署验证）；
- 已完成（经 Codex 审计）：Gate 1-8、记忆向量化、操作能力补强、结果审核（L1+L2+前端徽标+评测维度）、Settings 模块（模型管理 / API Key 前端配置 / 添加模型独立页 / 默认权限同步）、3D 城市可视化；
- 剩余：干净环境完整部署验证（Docker 真跑一次）、评测落地跑分（L1/L2 真实基线）、QGIS 宿主插件嵌入（Phase 4）、MCP 审批同步确认。

---

## 10. 面试问答速查（按最可能被问到的顺序）

### Q1：这个项目解决了什么问题？
把 GIS 操作从「会软件的人」下沉为「说句话就能用」。专业计算交给 GeoPandas/PyQGIS，LLM 只做规划与翻译，产物是 PNG/GeoJSON/CSV/工程文件，全程轨迹可审计。

### Q2：架构是怎么样的？
前端（Vue3 + SSE 流式）→ FastAPI → 单 Agent 工具循环（LLM 大脑）→ GIS 引擎抽象层（geopandas/QGIS 可换）→ 产物文件。工具 schema 表驱动，同时供自研 Agent 与 MCP 使用。

### Q3：为什么是工具调用而不是让 LLM 直接写代码？
脚本生成不可审计、不可干预、离真实 GIS 助手远。工具调用让每一步 `(工具名, 参数, 返回)` 都是证据，可以挂起审批、可以回放、可以评测，未来嵌入 QGIS 也不变。

### Q4：为什么用单 Agent 而不是多 Agent？
GIS 任务是串行决策链，无并行收益；单 Agent + 工具循环 + 步数/重试上限足够；预留了 sub_agent 扩展点。多 Agent（LangGraph 流水线）是早期脚本生成形态，两条路线适用场景不同。

### Q5：你的工具是怎么定义和扩展的？
表驱动 `TOOL_SCHEMAS`，一处定义三端生效（Agent / MCP / 前端）。新增走五步：schema → geopandas 引擎 → QGIS 引擎 → 自动暴露 → 单测。工具描述对照官方 API + 本地实测写，不靠臆想。

### Q6：记忆系统怎么设计的？
短期：滚动摘要压缩（80% 阈值提前触发，保留产物/图层/数值/偏好，窗口 40 条）；长期：lesson 向量化检索（n-gram 哈希 256 维 + 余弦 top-k）注入提示，语义优先、旧库文本回退。取舍：相关才注入，避免全量历史烧 token。

### Q7：上下文爆炸怎么办？
不会爆：估算 token 达阈值 80% 提前压缩；窗口限 40 条；工具返回控制在几百字节。即使异常也有 `try/except` 保证摘要失败不阻断会话。

### Q8：怎么防止 agent 死循环烧钱？
三层：工具错误自愈（不重复同样错误）+ `max_steps=12` 硬上限 + checker 重试上限 3 次。没有无限重试路径。

### Q9：安全合规怎么做的？
HITL 审批门（危险操作 `pending_approval` 挂起，前端审批卡片，超时默认拒绝，60s）；三权限模式（readonly/auto/ask）；路径白名单 + 文件名净化 + 上传 ≤10MB；全量轨迹审计。

### Q10：怎么评测 agent 好不好用？
两层：L1 引擎级断言「合格数据」（行数/字段/几何/CRS/产物，无 LLM 成本，可进 CI）；L2 15 个真实任务（含 5 个组合任务），报告 pass-rate / coverage / avg-steps / fail-reasons。

### Q11：为什么用 DeepSeek + function calling？
兼容 OpenAI 格式，`chat_with_tools` 统一封装；换模型只改 `model_id`，工具 schema 不变；成本低，适合工具循环这种「多轮多调用」场景。

### Q12：和真实 GIS 系统怎么接？
引擎抽象层换实现：`GIS_ENGINE=qgis` 切换到 `QgsEngine`，工具名、参数、schema 全部不变。先走 QGIS Server / `qgis_process` 无头路径，再考虑 PyQGIS 插件宿主。

### Q13：dsh/MCP 入口是什么？
同一套 `TOOL_SCHEMAS` 映射为 `gis_*` MCP 工具，桌面 AI 助手（dsh/Marvis）通过 MCP 协议直接调用我们的 GIS 能力。双入口共用引擎，能力一致。

### Q14：你踩过什么坑？
（挑 2~3 个说）`role=tool` 400 对齐修复；审批超时默认改为拒绝；工具异常兜底不让会话中断；评测口径从「可调用」修正为「合格数据」。

### Q15：项目接下来做什么？
Gate 1-8、Settings、结果审核、3D 均已落地。剩余：干净环境完整部署验证、评测落地跑分（拿真实 pass-rate）、QGIS 宿主插件嵌入（Phase 4）、MCP 审批同步。

### Q16：结果审核是怎么做的？
两层：L1 规则校验（统计工具返回带 `stats`，`validate_final_numbers` 对 final 数字做精确/量级/单位换算匹配，能抓 12.6 vs 126 这类量级错，零 LLM 成本）；L2 审核 Agent（独立上下文复核，输出 PASS/WARN/FAIL + 证据，FAIL 回主 Agent 只重写 final ≤2 轮）。前端 `done` 事件带 `audit_report` 渲染徽标。

### Q17：模型管理怎么做的（为什么能在 UI 配 Key）？
两层模型源：内置 `models.yaml` 只读基线 + 用户自定义 `user_models` 表，运行时叠加（同名用户优先）；内置模型 key 经 `PUT /api/v1/models/{id}/key` 自动写入 `.env` 并即时生效，`has_key` 检查环境变量真有值；添加模型有独立页预置 8 家厂商（DeepSeek/通义/GLM/Kimi/MiniMax/OpenRouter/Ollama 等），填 Key 即可，支持「保存并测试」连通。

---

## 11. 数字速查表（背下来）

| 项 | 数值 |
|---|---|
| 工具总数 | 41（读 7 / 空间分析 9 / 统计出图 8 / 编辑 11 / 工程 4 / 3D 2） |
| 危险工具 | 8（增改删要素 ×4 + commit + overwrite_output + calculate_field + remove_layer） |
| 步数上限 | 12 |
| checker 重试上限 | 3 |
| 摘要硬阈值 / 警告比 | 24000 tokens / 0.8 |
| 历史窗口 | 40 条消息 |
| 审批超时 | 60s，默认拒绝 |
| 权限模式 | readonly / auto / ask（会话默认可从设置配置） |
| 结果审核 | L1 规则校验（零成本）+ L2 审核 Agent（FAIL 修正 ≤2 轮） |
| 模型管理 | models.yaml（内置）⊕ user_models（自定义），UI 配 key 写 .env |
| 测试 | pytest 407 通过全绿；冒烟通过 |
| 引擎切换 | `GIS_ENGINE=qgis` |
| 上传限制 | ≤10MB |
| 提交规范 | `<type>(<scope>): <描述>` |

工具分类明细：
- **加载/查看（7）**：`load_data`、`inspect_data`、`list_layers`、`field_statistics`、`unique_values`、`load_raster`、`load_basemap`
- **空间分析（9）**：`buffer`、`overlay`、`join_by_location`、`join_by_attribute`、`voronoi`、`run_algorithm`、`transform_coords`、`get_crs`、`set_crs`
- **统计出图（8）**：`choropleth`、`scatter_plot`、`summarize`、`categorized`、`render_map`、`layout_map`、`set_labeling`、`export_geojson`
- **编辑（11）**：`start_editing`、`add_features`、`update_features`、`update_geometry`、`delete_features`、`calculate_field`、`commit_edits`、`rollback_edits`、`rename_layer`、`remove_layer`、`export_layer_inventory`
- **工程（4）**：`duplicate_layer`、`get_project_info`、`save_project`、`finish`
- **3D（2）**：`download_osm_buildings`、`render_3d`

---

## 12. 文档地图

| 文档 | 内容 |
|---|---|
| `SPEC-GIS智能操作平台.md` | Phase 1 MVP 执行文档（脚本生成形态） |
| `GIS-智能助手-工具调用设计.md` | 工具调用版设计（本文档的源头） |
| `GIS-真实引擎接入方案.md` | QGIS 接入路径 A/B、引擎换实现 |
| `GIS-引擎选型与分阶段演进.md` | 开源 GIS 选型矩阵 |
| `GIS-智能操作助手-操作能力规划.md` | 分析型 → 操作型演进规划 |
| `GIS-Agent基准评测集扩展方案.md` | L1/L2 两层评测 |
| `GIS-助手工程化与上线方案.md` | 部署与上线 |
| `GIS-智能助手-待开发交接文档.md` | P0–P3 待办 + 审计检查点 |
| `GIS-智能助手-Settings模块设计文档.md` | Settings 模块（模型/主题/偏好 + Ollama） |
| `GIS-智能助手-结果审核模块设计文档.md` | 结果审核 L1/L2 设计 |
| `工程化检查清单.md` | 8 维度 × 5 问交付模板 |
| `SQL-查询与联查速查.md` | 通用 SQL 速查 |
| `改进计划.md` | 改进路线 |
| `dsh-接入方案.md` | dsh/MCP 入口设计 |
| `GIS-3D城市可视化-最小演示方案.md` | 3D 方案（已实现 OSM 下载 + MapLibre 预览） |
| `部署指南.md` | 部署步骤 |
| `GIS-智能助手-项目深度理解与面试速查.md` | 本文档（设计细节速查 + 面试 Q&A） |
