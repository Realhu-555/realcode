# GIS 智能助手 · QGIS 插件嵌入方案（Live Engine）

> 配套文档：`docs/GIS-真实引擎接入方案.md`（路径 A/B 与 QgsEngine 现状）｜`docs/GIS-智能助手-数据生产员任务清单.md`（目标用户与验收任务）
> 版本：v1.0 ｜ 日期：2026-09-02 ｜ 作者：胡贞虎

## 0. 一句话结论

- 目标用户是**数据生产人员**，天天在 QGIS 里干活 → 助手必须能操作**他打开的工程**，而不是 headless 独立进程；
- 形态决策：**Web 对话 = 大脑与入口，QGIS 插件 = 实时手脚（Live Engine）**，两者通过本地回环通道连接；
- 插件不是「聊天框搬家」，而是把现有 `QgsEngine` 的 worker 从 offscreen 换成**当前 QGIS 会话（QgsProject + 画布）**；
- 一句话：**插件管「操作当前工程」，Web 管「对话/审批/留痕」，共享同一套 41 工具 schema 与安全边界。**

---

## 1. 为什么插件 = Live Engine，而不是「第二套聊天界面」

| 对比项 | 插件聊天框（不采用） | 插件 Live Engine（采用） |
|---|---|---|
用户 | 强迫生产员在 QGIS 里再学一个新聊天 UI | 保持他习惯的 web 对话 + QGIS 原生界面 |
大脑 | 插件内嵌 agent，QGIS python 环境要装全套 LLM 依赖 | agent 留在后端 venv（依赖全、可加记忆/审核） |
结果 | 截图或文件，回到工程还得手动导入 | 直接在当前工程加图层/改图层，所见即所得 |
安全 | 审批 UI 重做 | web 审批卡 + 插件内确认弹窗复用同一白名单 |
复用 | 工具/schema/checker 全部重写 | 复用现有 `TOOL_SCHEMAS` 与引擎方法契约 |

---

## 2. 目标架构

```
┌──────────── Web（FastAPI + Vue，现有）────────────┐
│  GisToolAgent（LLM 函数调用循环）                  │
│   ├─ 记忆 / checker / auditor / ApprovalGate       │
│   └─ create_gis_engine() ─ 引擎工厂（现有）        │
└──────────────┬────────────────────────────────────┘
               │ 统一工具接口（41 个 schema，JSON 摘要 + 产物文件）
       ┌───────┴────────┐
       │ 引擎选择（GIS_ENGINE）       │
       │ geopandas（现状/回退）        │
       │ qgis headless worker（现状）  │
       │ live-qgis（新增，走插件）     │◀── 本次目标
       └───────┬────────┘
               │ 本地回环 HTTP（127.0.0.1，带令牌）
┌──────────────▼──────────── QGIS 桌面 ──────────────┐
│  gis_assistant 插件（PyQt5，QGIS 3.40）             │
│  ├─ 停靠面板：工程图层/选中/连接状态               │
│  ├─ LiveEngine：操作 QgsProject.instance() + 画布   │
│  ├─ 审批桥：危险操作 → QGIS 内确认弹窗             │
│  └─ 控制服务：接收主进程工具调用 → 主线程执行        │
└────────────────────────────────────────────────────┘
```

> 插件与主进程之间的工具调用**完全复用 `QgsEngine` 的语义**：返回 JSON 摘要、
> 产物写引擎输出目录、输入路径白名单由主进程校验。插件侧只多一件事——**把结果图层加进用户当前工程**。

---

## 3. 与现有代码的关系（增量最小化）

| 现有资产 | 在方案中的角色 | 改动 |
|---|---|---|
| `src/gis_toolkit/qgis_worker.py`（offscreen worker） | 工具实现的**对照参考**，部分函数可直接搬 | 不删除，继续给 headless/CI 用 |
| `src/gis_toolkit/qgis_engine.py`（QgsEngine 主进程侧） | 协议与安全校验模板 | 抽公共校验，供 live 复用 |
| `src/gis_toolkit/schemas.py`（41 工具表驱动） | schema 源 | 不改 |
| `src/gis_toolkit/agent.py` + ApprovalGate | 对话/审批 | 不改（新增 live 引擎实现同一接口） |
| `src/gis_mcp/` | 外接宿主（dsh/OpenClaw） | 不动，MCP 也可指向 live 引擎 |

**新增物**：

1. `qgis_plugin/gis_assistant/` —— 可被 QGIS 加载的插件包；
2. `src/gis_toolkit/live_engine.py` —— 主进程侧「Live 引擎」，与 `QgsEngine` 同接口，
   只是把 JSON-lines 换成对本地插件 HTTP 服务的调用；
3. `engine.py::create_gis_engine` 增加 `GIS_ENGINE=live`（可含 `LIVE_QGIS_URL`/令牌配置）。

---

## 4. 控制通道协议（本地回环，第一版）

- **地址**：`http://127.0.0.1:8756`（默认，可配）；仅绑定回环地址；
- **鉴权**：`X-GIS-Token`，插件启动时生成/持久化到 QSettings，主进程从同一配置读取；
- **格式**：HTTP + JSON，与现有 JSON 摘要语义一致：

```jsonc
// 请求
POST /v1/tools/invoke
{ "tool": "update_features", "args": { ... }, "req_id": "..." }

// 响应
{ "ok": true,  "result": { "updated": 12, "layer": "村界" } }
{ "ok": false, "error": "...", "needs_approval": true }  // 危险操作回显审批
```

- **状态上报（供主进程/前端轮询）**：

```jsonc
GET /v1/state
{ "project": "D:/work/xxx.qgz",
  "crs": "EPSG:4547",
  "layers": [{ "id": "...", "name": "村界", "type": "Vector",
               "geometry": "Polygon", "features": 1234, "selected": 5, "editing": false }],
  "engine": "qgis-live", "version": "0.1.0" }
```

### 线程模型（关键）

QGIS 的对象**只能由主线程（GUI 线程）碰**。控制服务分两层：

1. `QTimer` 每 1s 在主线程刷新**只读快照**（图层名/要素数/选中数/编辑状态），HTTP 线程只读快照 → 状态查询永远安全；
2. 工具调用（写操作）由 HTTP 线程把请求放入队列，主线程通过 `signal/slot + QEventLoop` 执行并回传结果；
   危险操作由插件弹 QGIS 原生确认框（`QMessageBox`），主线程等待用户点确认/取消（超时默认拒绝）。

---

## 5. 安全边界（与 Web/MCP 对齐，只增不减）

| 边界 | 说明 |
|---|---|
| 工具白名单 | 复用 `TOOL_SCHEMAS`，插件不暴露 QGIS 表达式/处理脚本自由执行（沿用现有决策） |
| 路径白名单 | 加载外部文件仍由主进程 `_check_input_path` 校验；「工程外授权目录」后续按任务清单 P0 扩展 |
| 本地通道 | 仅 127.0.0.1 + Token；防同机其他进程越权调用 |
| 审批 | 危险工具（编辑/删除/提交/网络下载）走 ApprovalGate + 插件 QGIS 确认弹窗；超时默认拒绝 |
| 许可 | 插件进程内持有 QGIS（GPL）→ 内部部署 OK；商业化分发仍走 QGIS Server 隔离 |

---

## 6. 分阶段实施（Gate 划分，与任务清单验收对应）

| Gate | 内容 | 验收标准 | 对应验收任务 |
|---|---|---|---|
| **M1** ✅ 2026-09-02 | 插件骨架可加载：停靠面板显示工程图层/选中/连接状态；本地状态端点可查 | 面板出现；`GET /v1/state` 返回真实工程；headless 冒烟通过；Token 鉴权（401）验证通过 | 打底 |
| **M2a** ✅ 2026-09-02 | 主进程 `LiveEngine`（只读）：config + `.env`（`LIVE_QGIS_URL/TOKEN`）+ `create_gis_engine("live")` + `get_project_info`/`list_layers` 对接插件 | 后端能读到用户 QGIS 当前工程/图层状态；5 个单测通过；冒烟通过 | 状态注入前置 |
| **M2b** ✅ 2026-09-02 | 插件侧 `POST /v1/tools/invoke` + 主线程任务队列；首批 17 个工具（加载/检查/编辑增删改/提交回滚/缓冲/复制/导出等），结果图层真实加入当前工程 | headless 冒烟通过：加载→检查→增改→提交(文件校验 AA/B/C)→缓冲→导出；LiveEngine 6 单测通过；**web 端到端演示待 QGIS 重启插件后真机验收** | **T1** |
| **M3** | 审批桥：危险操作在 QGIS 弹原生确认框，web 审批卡与插件状态同步 | 编辑/提交前必须确认，取消即回滚 | T1 安全版 |
| **M4** | 新增质检工具（规则集 + 结果图层 + 报告），并接入工具 schema | 任务清单 **T2** 通过 | T2 |
| **M5** | 状态注入：把当前工程/图层/选中要素注入 prompt 上下文，Agent 能「看到」用户在干什么 | 对话里说「当前图层」，agent 回答与工程一致 | 生产员日常 |

> M2/M4 是能力大头；M1/M3 是形态与安全地基。完成 M1→M3 后即可拿 T1 做首次真环境演示。

---

## 7. 环境与开发方式（本机现状）

| 项 | 现状 |
|---|---|
| QGIS | `D:\QGIS`，3.40.10-Bratislava，Python 3.12.11，PyQt5 5.15.11 |
| 插件目录 | `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins`（尚无插件） |
| 开发部署 | 开发期把 `qgis_plugin/gis_assistant` 目录同步/软链到插件目录；QGIS 里启用后自动加载 |
| 校验 | 无 GUI 环境用 `python-qgis-ltr.bat -m py_compile` 校验语法；行为冒烟在 QGIS GUI 手工做 |

---

## 8. 风险与对策

| 风险 | 对策 |
|---|---|
| 主线程阻塞：工具执行期间 QGIS 界面冻结 | 写操作本就快（native 算法），先接受短阻塞；长任务（下载/3D）后续迁 `QgsTask` |
| 插件崩溃影响用户工程 | 编辑全部走事务（start/commit/rollback），崩溃可回滚；危险操作默认 ask |
| QGIS 版本差异（3.40 vs 未来 LTR） | 插件 `qgisMinimumVersion=3.34`，API 只用稳定子集 |
| 与现有 headless worker 双份维护 | M2 起抽「工具实现层」，worker 与插件共用函数；headless 保留给 CI |
| Web 在插件未启动时调用 | live 引擎启动时探测失败 → 明确报错并提示「请在 QGIS 打开插件」，可回退 qgis worker |

---

## 9. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-09-02 | 插件定位为 Live Engine，不做聊天框 | 用户偏好 web 对话；生产员要求操作落在当前工程；LLM 栈留后端 |
| 2 | 2026-09-02 | 控制通道用本地 HTTP + Token，第一版不做 WebSocket | 实现简单、状态轮询足够；长推送后续再升级 SSE/WS |
| 3 | 2026-09-02 | 新增 `GIS_ENGINE=live`，复用引擎工厂与 41 工具 schema | 主进程/前端/MCP 零侵入，可随时回退 geopandas/qgis |
| 4 | 2026-09-02 | 危险操作审批 = ApprovalGate（web）+ QGIS 原生弹窗（插件）双通道 | 用户在 GIS 里操作时，审批就在眼前，符合 HITL 直觉 |
