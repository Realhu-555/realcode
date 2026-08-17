# SPEC — GIS 智能操作平台（ai-dev-platform 方向切换）

> 给实现方（AI 编程助手）的执行文档。按 Task 顺序实现，每完成一个 Task 跑测试全绿再进下一个。
> 版本：v1.2 ｜ 日期：2026-08-17 ｜ 作者：胡贞虎
> 文档定位：Phase 1（MVP）执行文档；引擎选型 / 开源 GIS 宿主 / 分阶段演进见配套文档 `docs/GIS-引擎选型与分阶段演进.md`。
> 基础代码：以 `master` 分支（`1e5aed7`）为基线 —— 含 ApprovalGate / 模型路由 / eval / observability / recovery / storage 全部可复用资产；
> `.worktrees/feature-phase2-agents`（worktree-phase2-agents 分支）仅作为旧 Agent 结构参考（requirement/architect/backend/tester/deployer 角色映射），不再作为直接基线（该分支缺少 master 已实现的 gate、模型路由、评测等能力）。
>
> v1.1 变更摘要（2026-08-17 设计评审后补充）：
> 1. 工具分层：只有 `data_inspect` 注册为 LLM 工具；`sandbox_run` / `list_artifacts` 改为 exec/export 节点的内部能力，不进工具注册表；
> 2. `data_inspect` 改为 plan 前代码预注入（schema 进 state），不依赖 LLM 主动调用；
> 3. 沙箱必须实现 AST 静态扫描（禁 `os.remove` 等危险调用），相关验收用例从「加分项」提升为「必过项」；
> 4. ApprovalGate 复用需加 `default_on_timeout` 参数，危险操作超时默认拒绝（原实现超时默认放行，对危险操作是反向的）；
> 5. checker 校验三层化：规则断言（非 LLM）→ 脚本打印 figure 信息 → 视觉模型 OCR，不再接受「文本声明即可」；
> 6. 新增 Phase 1 Task 0：依赖前置（geopandas/matplotlib 安装与手写出图冒烟）；
> 7. 新增配套文档 `docs/GIS-引擎选型与分阶段演进.md`：引擎选型矩阵与分阶段引入（Phase 3 起引入 QGIS，MVP 不需要桌面 GIS）；
> 8. 文档拆分：本文档定位为 Phase 1（MVP）执行文档，原「开源 GIS 选型与宿主定位」一节移至配套文档。

---

## 0. 为什么换方向（背景）

原项目是「营销内容多 Agent 平台」：生成公众号/知乎/小红书三篇内容 → 审校 → 导出 Markdown。
三个致命问题：

1. **产物不实用**：生成的是文字，不能自动发布（公众号有配额、知乎/小红书无公开 API），没有数据回流闭环。
2. **不贴岗位**：目标岗位是「空间数据智能问答 + GIS 软件智能操作」，营销内容与岗位无关。
3. **与现成工具撞车**：通用 Web 应用生成方向（v0 / Bolt / Cursor）竞争不过。

**新方向：GIS 智能操作平台** —— 用户用自然语言描述 GIS 操作需求，系统自动完成
任务解析 → 步骤规划 → GIS 脚本生成 → 沙箱执行 → 结果校验 → 成果导出。

一句话定位：**把「说人话 → 出图/出数据」变成一条多 Agent 流水线。**

---

## 1. 项目定位

- **用户**：规划、测绘、智慧城市、房产、运营等需要做空间分析的从业者；不懂 GIS 代码。
- **输入**：一句自然语言 + 一个数据文件（CSV / GeoJSON / Shapefile）。
  - 例：「把示例数据 GDP.csv 按省份做分级设色图」
  - 例：「找出地铁站 500 米范围内的学校并导出为 GeoJSON」
  - 例：「统计每个区县的 POI 数量，做成柱状图」
- **输出**：成果包（PNG 图 / GeoJSON / CSV + 操作说明文档）。
- **核心价值**：GIS 操作从「会软件的人」下沉为「说句话就能用」，专业计算交给 GeoPandas/PyQGIS，LLM 只做规划和翻译。

---

## 2. 与现有代码的复用关系（基线见文件头：以 master 分支为主）

直接复用的资产：

| 现有资产 | 路径 | 复用方式 |
|---|---|---|
| 多 Agent 编排 | `src/orchestrator/graph.py` | 改节点注册，保留条件边 + 并行结构 |
| 共享状态 | `src/orchestrator/state.py` | 新增 `GisProjectState`，复用 Reducer 模式 |
| Agent 基类 | `src/agents/base.py` | 不动，继续用 `build_prompt_context` + Jinja2 渲染 |
| 代码沙箱 | `src/sandbox/executor.py` | 直接复用（create / run / list_files / pack_zip / cleanup） |
| Prompt 系统 | `src/prompt/renderer.py` + templates | 换一套 GIS 模板 |
| 追问机制 | requirement 的 `[ASK_USER]` 结构化标记 | 原样迁移到 plan Agent |
| LLM Provider / 模型路由 | `src/llm/provider.py` | 不动 |
| WebSocket 服务 | `src/web/server.py` | 改 pipeline 初始化，前端换页面 |
| ApprovalGate | master 分支 `src/orchestrator/gate.py`（docs/approval-gate-spec.md 已接入） | 复用到危险操作确认 |

不保留的：营销内容的 5 个 prompt 模板、三渠道 Agent、审校 Agent（角色被 checker 取代）。

---

## 3. 总体架构

```
用户输入（一句话 + 数据文件）
    ↓
┌──────────────────────────────────────────────┐
│ plan 规划 Agent      ← 拆解任务、信息不足追问  │
│  (原 requirement 角色)                        │
└──────────────┬───────────────────────────────┘
               ↓ 任务方案（步骤清单）
┌──────────────────────────────────────────────┐
│ design 方案 Agent   ← 数据源/坐标系/算子/出图  │
│  (原 architect 角色)                          │
└──────────────┬───────────────────────────────┘
               ↓ 技术方案
┌──────────────────────────────────────────────┐
│ codegen 脚本 Agent  ← 生成 GeoPandas 脚本     │
│  (原 backend 角色，可拆分析脚本+出图脚本并行)   │
└──────────────┬───────────────────────────────┘
               ↓ 脚本
┌──────────────────────────────────────────────┐
│ sandbox 执行       ← SandboxExecutor 运行     │
└──────────────┬───────────────────────────────┘
               ↓ 执行日志 + 产出文件
┌──────────────────────────────────────────────┐
│ checker 校验 Agent  ← 结果校验（文件/范围/坐标）│
│  (原 tester 角色，审核 Agent 的延续)           │
└──────────────┬───────────────────────────────┘
               ↓ 校验报告（不通过 → 回 codegen 重写，最多 N 轮）
┌──────────────────────────────────────────────┐
│ export 导出        ← 打包成果 zip + 说明文档    │
└──────────────────────────────────────────────┘
```

**两个关键机制（面试重点）：**
1. **条件边 + 追问**：plan 信息不足 → `ask_user` → 暂停等用户（复用营销平台确认门）。
2. **校验反馈回路**：checker 不通过 → 带着问题清单回 codegen 重写，最多 2 轮，防死循环烧 token。

---

## 4. Agent 角色定义

### 4.1 plan 规划 Agent（替代 requirement）
- **职责**：把用户一句话翻译成明确的 GIS 任务；判断是否具备四要素——数据（有没有文件/路径）、目标（要什么结果）、范围（哪块区域/哪个字段）、输出（图/表/文件）。
- **输出**：结构化任务方案（Markdown 步骤清单），信息不足输出 `[ASK_USER]` 追问。
- **Prompt 要点**：明确「不知道就问」；禁止编造数据文件名和字段名（必须基于用户提供或示例数据）。

### 4.2 design 方案 Agent（替代 architect）
- **职责**：确定技术方案——数据源读取方式（CSV 用 geopandas + lon/lat 列 / GeoJSON 直接读）、坐标系（EPSG，缺失时默认 WGS84 并注明）、分析算子（分级设色=quantile/equal_interval、缓冲区=buffer、相交=overlay）、出图方案（matplotlib 底图 + 图例 + 标题 + 数据来源标注）。
- **输出**：技术方案文档（`---TECH_PLAN_START---` 结构标记，复用现有协议）。
- **Prompt 要点**：强制写明「输入字段清单 + 坐标系假设 + 输出文件清单」，这是 checker 的校验依据；字段清单必须来自 `data_schema`（data_inspect 预注入的真实数据），禁止编造。

### 4.3 codegen 脚本 Agent（替代 backend/frontend）
- **职责**：按技术方案生成完整可运行的 Python 脚本（GeoPandas + matplotlib），输出 `---SCRIPT_START---` 结构。
- **输出规范**：脚本必须：
  - 顶部注释写明输入文件路径、输出文件路径、坐标系；
  - 所有输出写进沙箱工作目录（`os.environ.get("SANDBOX_WORKDIR", ".")`），不写绝对路径；
  - 打印关键中间结果（行数、字段、坐标系、范围）到 stdout，供 checker 核对；
  - 数据读取失败时 `print("ERROR: ...")` 并以非 0 退出，不静默。
- **Prompt 要点**：只允许使用示例数据中真实存在的字段；不允许删除源文件；不允许写沙箱目录外的路径。
- **执行前置**：生成的脚本必须通过 AST 静态扫描（见 6.3），未通过不进入执行，直接回 codegen 重写。

### 4.4 sandbox 执行（纯代码，无 LLM）
- 复用 `SandboxExecutor`：先复制源数据进沙箱（快照），再执行脚本，收集 stdout/stderr/退出码/产出文件列表。
- 超时默认 60s，超时 kill。

### 4.5 checker 校验 Agent（替代 tester，审核 Agent 的延续）
- **职责**：执行后自检，输出结构化校验报告（`---CHECK_REPORT_START---`）：
  - ✅/❌ 输出文件是否存在且非空；
  - ✅/❌ 数据范围/分级数量是否符合技术方案（行数、分类数、字段名）；
  - ✅/❌ 坐标系是否与方案一致（脚本打印的 EPSG）；
  - ✅/❌ 图是否可读：三层校验——① 规则断言（非 LLM）：PNG 存在且 >20KB、用 PIL 检查尺寸与非常色；② 脚本打印 figure 信息（axes 数 / 是否有图例 / 标题）；③ 可选用视觉模型（MiMo/EasyOCR 栈）真实读图。禁止只信脚本文本声明；
  - ✅/❌ 是否有 ERROR 日志。
- **输出**：整体结论 `PASS / FAIL` + 逐项问题 + 修改建议（回传 codegen 用）。
- **Prompt 要点**：只基于沙箱真实产出判断，不脑补；结论必须可被脚本日志 / 规则断言结果佐证。

### 4.6 export 导出（替代 deployer，纯代码）
- 把沙箱内的成果文件（PNG/GeoJSON/CSV + 校验报告 + 操作说明 md）打包 zip，返回下载路径。

### 4.7 Agent 工具集（最小权限，v1.1 新增）

| Agent | 工具 | 说明 |
|---|---|---|
| plan | `data_inspect` | 优先使用预注入的 `data_schema`，仅在需要补充信息（如查看某列取值分布）时再调 |
| design | `data_inspect` | 同上 |
| codegen | （无） | 不暴露任何工具，缩小注入面 |
| checker | （无） | 只基于 state 里的 `exec_log` / 产出清单 / 规则断言结果判断 |

---

## 5. State 设计（GisProjectState）

新增 `GisProjectState(TypedDict)`，沿用现有 Reducer 模式：

```python
class GisStage(str, Enum):
    PLAN = "plan"
    DESIGN = "design"
    CODEGEN = "codegen"
    EXEC = "exec"
    CHECK = "check"
    EXPORT = "export"
    DONE = "done"
    ERROR = "error"

class GisProjectState(TypedDict):
    # 用户输入
    user_request: str            # 原 user_idea
    data_file: str | None        # 上传/指定的数据文件路径
    data_schema: str | None      # data_inspect 预注入（字段清单+前5行样例+坐标列识别）

    # Agent 产出
    task_plan: str | None        # 原 prd
    tech_plan: str | None        # 保留
    script: str | None           # 原 backend_code
    exec_log: str | None         # 沙箱 stdout/stderr（新增）
    artifacts: list[str]         # 沙箱产出文件列表（exec 节点写入，checker 校验用）
    check_report: str | None     # 原 test_report
    artifact_path: str | None    # 原 zip_path

    # 状态管理
    current_stage: Annotated[GisStage, _latest_stage]
    error_message: str | None
    ask_user: str | None
    messages: Annotated[list[dict], operator.add]
    rewrite_round: int | None    # 校验失败重写轮次（新增，上限 2）

    # 沙箱
    workdir: str | None          # 当前沙箱目录（新增，checker/export 需要）
```

**并行写冲突**：同现有设计——`messages` 用 `operator.add`，`current_stage` 取最新值。

---

## 6. 工具与沙箱

### 6.1 工具分层（v1.1 修订）

区分「LLM 工具」与「流水线内部能力」，二者不混用：

- **LLM 工具**（进工具注册表，Agent 可在对话中调用）：
  - `data_inspect(path)`: 读取数据文件头几行 / GeoJSON 字段。安全约束：只读、限制大小 10MB、**路径白名单**（仅允许 project 的 data 目录或沙箱快照，禁止任意路径，防止 prompt injection 诱导读取 `.env` 等敏感文件）。
- **内部能力**（图节点直接调用，不注册为 Tool、不进 LLM 上下文）：
  - `sandbox_run(script)` → exec 节点直接调 `SandboxExecutor.run_command()`；
  - `list_artifacts()` → export 节点直接调 `SandboxExecutor.list_files()`。

> 原因：`sandbox_run` 一旦注册为 Tool，即使不放入任何 Agent 的 tool_ids，也在注册表里多了一个被误调用的面，且与「exec 是纯代码节点」的架构矛盾。

### 6.2 data_inspect 预注入（v1.1 修订）

进入 plan 前，由 pipeline 代码自动执行一次 `data_inspect`，把结果写入 `state["data_schema"]`（字段清单 + 前 5 行样例 + 坐标列识别）。plan/design 的 PromptContext 直接携带真实 schema，不依赖 LLM 记得去调工具。这同时支撑「禁止编造字段名」约束。

### 6.3 沙箱规则

- 每次任务独立临时目录，执行完打包后清理；
- 源数据以副本进入沙箱，脚本无权改源文件；
- **AST 静态扫描（必过项）**：脚本执行前用 `ast` 解析，命中以下模式直接拒绝执行：
  - import 黑名单：`os`、`shutil`、`subprocess`、`socket`、`requests`、`urllib`、`pathlib`（写操作）；
  - 调用黑名单：`os.remove` / `os.unlink` / `shutil.rmtree` / `eval` / `exec` / `open(..., "w")` 等写、删类调用；
  - 绝对路径写入：脚本只允许写 `SANDBOX_WORKDIR` 下的相对路径；
- 网络隔离：MVP 无法做容器级隔离，靠 AST 禁网络相关 import + 文档声明「降级版，生产用 Docker」；
- 超时默认 60s，超时 kill（沿用现有 `SandboxExecutor.run_command`）；
- 沙箱执行同步阻塞，在 server 中必须走 `run_in_executor` 线程池（与现有 `_build_agents` 调用方式一致）。

---

## 7. 安全与可靠性（面试必讲）

1. **操作前快照**：源数据复制进沙箱，任何执行都在副本上进行，源数据零风险。
2. **危险操作二次确认**：任务含删除图层、覆盖输出、批量修改时触发 ApprovalGate，人工确认后才继续。检测双保险：plan 阶段 LLM 判断 + codegen 后规则扫描（AST 命中危险模式强制触发）。复用 master 的 gate，但**必须加 `default_on_timeout` 参数**：危险操作超时默认拒绝（现实现 `src/orchestrator/gate.py` 超时默认放行，对危险操作是反向的）。
3. **坐标系校验**：脚本必须打印 EPSG，checker 与方案比对，不一致判 FAIL（防止投影错乱导致结果错位）。
4. **超时 + 轮次上限**：沙箱执行 60s 超时；校验失败回写最多 2 轮；plan 追问最多 3 轮。
5. **可观测**：沿用 TraceTracker——每个 Agent 的输入输出、工具调用、耗时、成本全量记录；前端实时显示阶段。

---

## 8. Demo 验收标准（MVP 必须跑通）

**输入**：用户上传 `gdp_demo.csv`（省/市 + 数值字段），输入「按省份做分级设色图」。

验收清单（全部通过才算 MVP 完成）：
1. plan 产出 ≥3 步任务清单，且不追问（信息足够）；
2. design 技术方案含字段清单、坐标系（WGS84 默认）、分级方式（quantile 5 级）、输出文件名；
3. codegen 生成脚本，沙箱执行退出码 0，无 ERROR 日志；
4. 产出 `choropleth.png`（>20KB）+ `summary.csv`；
5. checker 全部 ✅，结论 PASS；
6. export 打包 zip 可下载，内含操作说明 md（说明数据来源、分级方式、如何解读）。

**必过安全验收（v1.1 提升）**：
- 脚本故意注入 `os.remove("...")` → AST 扫描拒绝执行（不进入子进程）；
- 脚本尝试 `import requests` / 读沙箱外绝对路径 → 拒绝执行。

**额外加分验收（Phase 1 尾期）**：
- 用户输入「数据里没有经纬度，帮我看看」→ plan 追问而非硬跑；
- 校验失败 → 自动回 codegen 重写 1 次成功。

---

## 9. 分阶段实施计划

### Phase 1（本周）：MVP 跑通
- ✅ Task 0（2026-08-17 完成）：依赖前置——venv 已装 `geopandas 1.1.4` / `matplotlib 3.11.1` / `pandas 3.0.5` / `Pillow`，冒烟出图通过；沙箱 AST 静态扫描已实现（`src/sandbox/security.py` + `SandboxExecutor.run_script`，12 个测试全绿）；
- ✅ Task 1（2026-08-17 完成）：`GisProjectState` + `GisStage` 已加入 `src/orchestrator/state.py`（向后兼容保留 `ContentProjectState`，4 个测试全绿）；
- ✅ Task 2（2026-08-17 完成）：plan / design / codegen / checker 四个 Agent（`src/agents/gis_*.py`）+ 4 个 prompt 模板 + `data_inspect` 工具（路径白名单/10MB 限制）+ 模型路由注册（8 个 Agent 测试 + 6 个工具测试全绿）；
- ✅ Task 3（2026-08-17 完成）：`create_gis_graph()` 已加入 `src/orchestrator/graph.py`（plan→design→codegen→exec→checker→export，条件边 ask_user + 校验回环上限 2 轮，exec/export 纯代码节点；4 个图测试全绿）；
- ✅ Task 4（2026-08-17 完成）：server 接入 `/api/v1/gis/upload`（限 .csv/.geojson/.json/.zip、10MB）+ `/api/v1/gis/build` + WebSocket `action=build_gis`（阶段进度推送，6 个 API 测试全绿）；
- ✅ Task 5（2026-08-17 完成）：MVP 验收清单 1-6 自动化通过（`tests/test_gis_demo.py`，gdp_demo.csv 分级设色出图）；沙箱安全/状态/Agent/工具/图/API/demo 共 42 个 pytest 用例全绿；真实 LLM 端到端冒烟通过（`data/gis_demo/gdp_demo.csv` → `choropleth.png` + `summary.csv`，checker 逐项 PASS）。

### Phase 2（下周）：算子与数据扩展
- 算子：buffer / overlay / 空间连接 / 简单路径；数据源：Shapefile、PostGIS 只读连接；
- 出图扩展：柱状图、散点图、热力图（seaborn）；
- 新增「校验不通过自动重写」正式闭环 + 重试计数展示。

### Phase 3：GIS 软件操作（贴岗位）
- 把 PyQGIS / ArcPy 常用操作封装成工具（加图层、符号化、导出 PDF）；
- 「操作序列 + 状态注入」：把当前工程状态（图层列表、坐标系、选中要素）作为上下文注入 Agent；
- 危险操作（覆盖、删除）二次确认 + 操作历史/回滚。

### Phase 4：与 RAG 项目合体（空间数据智能问答）
- 项目二（rag-knowledge-qa）加空间检索模块（空间范围过滤 + 矢量属性检索）；
- 组合场景：先问答定位数据 → 再操作生成图表，两个项目串成一条链路。

---

## 10. 评测与迭代

- **规则指标（不依赖 LLM）**：执行退出码、产出文件存在性、分级数量正确性、字段存在性——自动化断言。
- **LLM 指标**：checker 报告与真实日志一致性抽检（人工每 10 次看 1 次）。
- **坏例反哺**：每次 FAIL 记录 badcase，归类（规划错/字段错/API 错/坐标系错），每类攒 5 条就补一条 prompt 约束。
- **目标**：MVP 场景首次通过率 ≥ 70%（10 次真实任务）。

---

## 11. 面试故事线

### 3 分钟陈述
> 「我第一个项目用 LangGraph 搭了营销内容多 Agent 平台，验证了多 Agent 编排、工具权限隔离、并行 fan-out、人机确认这套能力。第二步我把同一套能力迁移到 GIS 域，做成 GIS 智能操作平台：用户说『把 GDP 数据做成分级设色图』，规划 Agent 拆步骤 → 方案 Agent 定数据源和坐标系 → 脚本 Agent 生成 GeoPandas 代码 → 沙箱执行 → 校验 Agent 核对输出文件、数据范围、坐标系 → 导出成果包。关键设计有三个：一是校验反馈闭环，结果不对自动回写重写，最多两轮；二是安全，源数据快照进沙箱，危险操作人工二次确认；三是坐标系强校验，防止投影错乱。这套『写查分离 + 清单驱动 + 人工兜底』和我之前的审核 Agent 是一脉相承的。」

### 面试追问清单（每问配一句话答案）
1. 为什么用多 Agent 不用单 Agent 写脚本？→ 规划/方案/代码/校验是四种不同能力，prompt 和校验逻辑完全不同，拆开可观测可并行。
2. 怎么防止「脚本跑通但结果错」？→ 三步：脚本强制打印中间结果 → checker 对方案逐项核对 → 规则断言（文件/字段/分级数）不依赖 LLM。
3. 危险操作怎么兜底？→ 快照 + ApprovalGate 二次确认 + 沙箱禁危险函数。
4. 坐标系不一致怎么办？→ 脚本必须声明 EPSG，checker 比对，不一致直接 FAIL。
5. 生成代码质量不稳怎么处理？→ 字段白名单 + 校验回环重写（上限 2 轮）+ badcase 反哺 prompt。
6. 沙箱安全？→ 独立临时目录 + 源数据副本 + 禁网 + 受限子进程 + 60s 超时。
7. 和岗位的关系？→ 这就是「GIS 软件智能操作」场景；「空间数据智能问答」由我的 RAG 项目扩展承接，一读一写覆盖岗位两个场景。

---

## 12. 与目标岗位的对应（面试结尾升华句）

> 「岗位的两个场景我正好用两个项目覆盖：空间数据智能问答 = 我的 RAG 项目加空间检索模块（读数据、答问题）；GIS 软件智能操作 = 这个项目（把想法变成图和文件）。共同的设计原则是：**专业计算交给引擎（PostGIS/GeoPandas），LLM 只做规划和翻译；所有生成结果过校验，支持失败重试和人工介入；每一步可追溯。**」

---

## 13. 引擎选型与分阶段演进（见配套文档）

> 原「开源 GIS 选型与宿主定位」内容已移至配套文档 `docs/GIS-引擎选型与分阶段演进.md`（含三层模型、候选系统评估、分阶段引入表、QGIS 宿主定位、决策记录）。
> 一句话结论：**MVP 用 GeoPandas + matplotlib，不需要桌面 GIS；Phase 3 引入 QGIS 作宿主；工具描述来源是 API 文档 + 实测，不是源码。**

---

## 附：实现顺序提醒（给实现方）

- 先做 state 和 prompt 模板，再连 graph，最后接 server；
- 每个 Agent 先写最小可用 prompt，跑通再加约束；
- 沙箱测试必须覆盖「注入 os.remove 被拒」这个安全用例；
- 所有新代码跑 `pytest tests/` 全绿再提交，遵守现有 CLAUDE.md 规范（ruff + mypy）。
