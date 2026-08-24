# GIS 智能操作助手 — 待开发任务交接文档

> 用途：交给 Marvis（腾讯桌面 AI 助手）按此文档继续开发；完成后由 Codex 按第 8 节逐项审计验收。
> 版本：v0.1 ｜ 日期：2026-08-24 ｜ 工作目录：`H:\ai-dev-platform`（分支 `feat/gis-mcp-server`）

---

## 1. 项目概况

**定位**：自然语言驱动的 GIS 智能操作助手。用户用一句话让助手完成「读数据 → 空间分析 →
出图/出数据 → 编辑要素/管理图层/定制样式/工程管理」的完整 GIS 工作，**保留分析型能力，
操作型能力是主线**。

- 形态：Web 前端对话（流式输出 + 人工审批卡片）+ FastAPI 后端 + 工具调用型单 Agent
- 双入口：自研 Agent（Web）与 dsh/MCP（`src/gis_mcp`）共用同一套引擎与工具 schema
- 仓库：`https://github.com/Realhu-555/realcode`（分支 `feat/gis-mcp-server`）
- 运行：`start.bat` 启动后端（`http://localhost:8080`），前端为构建产物（`src/web/static/`）

## 2. 技术栈与关键路径

| 模块 | 路径 | 说明 |
|---|---|---|
| 后端 | `src/web/server.py` | FastAPI，SSE 流式 `/api/v1/gis-assistant/run/stream`，会话/审批/产物 API |
| 引擎（默认） | `src/gis_toolkit/engine.py` | geopandas 实现全部工具 |
| 引擎（QGIS） | `src/gis_toolkit/qgis_engine.py`、`qgis_worker.py` | 同接口实现，`GIS_ENGINE=qgis` 切换 |
| Agent | `src/gis_toolkit/agent.py` | `GisToolAgent`：工具循环 + `approval_gate` + checker 校验 + 上下文滚动摘要 |
| 工具注册 | `src/gis_toolkit/schemas.py` | `TOOL_SCHEMAS` 表驱动，新增工具自动暴露给 MCP 与自研 Agent |
| MCP | `src/gis_mcp/tools.py` | 表驱动映射为 `gis_*` MCP 工具 |
| 审批 | `src/gis_toolkit/approval.py` | `ApprovalGate`，模式 `readonly/auto/ask`，危险操作白名单 |
| 会话 | `src/gis_toolkit/session.py` | `GisSessionStore`（图层状态 + 对话历史 + 权限模式） |
| 记忆 | `src/orchestrator/long_term_memory.py` | `LongTermMemory`（lesson 保存 / LTM hint） |
| 前端 | `frontend/`（构建产物 `src/web/static/`） | Vue3 + Naive UI，`GisAssistant.vue` |
| 质量门 | `scripts/check.bat`、`scripts/smoke.py` | ruff check/format + pytest + 冒烟 |

## 3. 当前状态（已完成，勿重做）

- **Gate 1/2/3** ✅：QGIS 环境验证、`QgsEngine` 9 工具、引擎可切换（`GIS_ENGINE`）
- **Gate 6** ✅：要素编辑（事务式会话 start/add/update/update_geometry/delete/commit/rollback）+ 复制图层 + **危险操作审批（HITL）**端到端
- **Gate 7** ✅：样式定制（`categorized` 分类设色、`set_labeling` 标注）+ 工程管理（`get_project_info` / `save_project`）
- **工具共 32 个**：加载/查看（load_data, inspect_data, list_layers, field_statistics, unique_values, load_raster）、空间分析（buffer, overlay, join_by_location, voronoi, run_algorithm, transform_coords, get_crs, set_crs）、统计出图（choropleth, scatter_plot, summarize, categorized, render_map, set_labeling, export_geojson）、编辑（start_editing, add_features, update_features, update_geometry, delete_features, commit_edits, rollback_edits）、工程（duplicate_layer, get_project_info, save_project, finish）
- **测试**：pytest 263 通过 / 2 失败；`scripts/smoke.py` 通过
- **测试数据**：已扩充（见 `data/README.md`：`data/gis_base/` 行政区划/统计面/点线栅格、`data/gis_demo/` CSV）
- **相关文档**：`SPEC-GIS智能操作平台.md`、`GIS-智能助手-工具调用设计.md`、`GIS-真实引擎接入方案.md`、`GIS-智能操作助手-操作能力规划.md`、`改进计划.md`、`GIS-助手工程化与上线方案.md`、`dsh-接入方案.md`、`GIS-3D城市可视化-最小演示方案.md`

## 4. 已知问题（P0，必须先修）

| # | 问题 | 修复要求 | 验收 |
|---|---|---|---|
| T1 | `tests/test_gis_api.py` 两个用例失败：`test_run_gis_assistant_sync_wraps_agent`、`test_gis_assistant_stream_ok`，报 `FakeAgent/BoomAgent.__init__() got an unexpected keyword argument 'approval_gate'` | 测试内 fake agent 构造函数补 `approval_gate=None` 参数 | 两用例通过 |
| T2 | `scripts\check.bat` 第 2 步 `ruff format --check` 不过：ruff 0.16.3 下 `src/` 约 20 个文件未格式化，且 `src/gis_toolkit/bench.py`、`demo.py` 触发 ruff 崩溃（annotation range panic） | 二选一：统一按当前 ruff 格式化全量 `src/ tests/`（单独一个 `style` 提交）；或把 ruff 版本固定到与项目既有格式一致的版本。两种方式都要保证 `check.bat` 全绿 | `check.bat` 三步全过 |
| T3 | 全量 pytest 存在以上 2 失败 + 偶发 `test_gis_toolkit.py` 等地理 CRS 告警 | 不做功能性修改，仅确保回归全绿 | `pytest tests -q` 全绿（`test_ocr_docker/test_sandbox/test_gis_sandbox` 除外） |

## 5. 待开发任务（按优先级）

### P1 — 记忆系统收尾（对应 Gate 4，文档需标记 ✅）
- 现状：`agent.py` 已有滚动摘要压缩（`COMPACT_THRESHOLD_TOKENS=24000`、`HISTORY_WINDOW_MESSAGES=40`）和 `LongTermMemory`（lesson 保存 / `_build_ltm_hint`）
- 待办：
  1. 长期记忆向量化检索：把会话摘要/lesson 结构化提取后写入向量库，按相关性 top-k 注入提示（可用轻量方案，如本地 embedding + sqlite/faiss）
  2. 主动压缩阈值：对话长度接近上限时**提前**触发摘要压缩，而不是爆了才压缩
  3. 补齐测试：10+ 轮长对话不爆上下文；跨会话能召回历史结论与产物引用
- 验收：长链对话稳定；跨会话召回可用；`Gate 4` 在文档标记 ✅

### P1 — 操作能力补强（操作型主线，用户高频需求）
1. **字段计算 `calculate_field`**：对当前图层按表达式生成新列（四则运算、归一化、人均 = gdp/pop 等）；危险写操作进审批
2. **属性连接 `join_by_attribute`**：CSV/表按关键字段关联到当前图层（当前只有空间连接 `join_by_location`）
3. **图层管理增强**：图层重命名/移除、图层清单导出
- 规则：新工具必须走「`schemas.py` 加 schema → `engine.py` 实现 → `qgis_engine/qgis_worker` 同步实现 → MCP 自动暴露 → 单测」五步；危险操作进 `DANGEROUS_TOOLS`
- 验收：Web 与 dsh/MCP 双入口都能用；单测覆盖；工具总数更新（32 → 35+）

### P2 — Gate 8：地图排版与底图
- 布局出图：图例/比例尺/指北针 → 导出 PDF/PNG（geopandas/matplotlib 先做，QGIS `QgsLayout` 校准）
- 数据源：WMS/XYZ 底图加载（QGIS 引擎路线）
- 验收：对话能产出带图例+比例尺的布局图；底图可加载叠加分析

### P2 — 工程化与上线（对齐 `docs/GIS-助手工程化与上线方案.md`）
- 配置/密钥管理、结构化日志、健康检查完善
- 前端体验回归：流式输出、会话管理、审批卡片、权限模式切换
- 按 `docs/部署指南.md` 做一次干净环境部署验证

### P3 — 3D 城市可视化（所有 Gate 结束后再做，方案已定稿）
- 按 `docs/GIS-3D城市可视化-最小演示方案.md` 的阶段 0/1/2 实施：OSM 建筑下载 + MapLibre 拉伸预览 + 接为 agent 工具

### P3 — MCP/dsh 双入口同步
- 确保 `src/gis_mcp` 与自研 Agent 使用同一套 32+ 工具 schema；把 HITL 审批（`approval_gate`）同步到 dsh/MCP 入口（见 `docs/dsh-接入方案.md`）

## 6. 开发规范（必须遵守）

1. **测试不过不准提交**：每个任务完成先跑测试；`scripts\check.bat` 全绿才算完成
2. **提交信息**：`<type>(<scope>): <描述>`，type ∈ feat/fix/docs/style/refactor/test/chore
3. **提交前检查**：`venv\Scripts\python.exe -m ruff check src tests` + `pytest`
4. **禁止提交**：`data/projects.db`、`long_term_memory.db`、`CLAUDE.md`、`data/gis_sessions.json`、运行日志（`backend*.log`、`backend_run.*.log`）、`data/gis_exports/`、`data/gis_toolkit_out/`、`data/gis_traces/`、`data/gis_uploads/`
5. **风格**：中文注释/文档；公共函数类型注解；行宽 ≤100
6. **分支**：在 `feat/gis-mcp-server` 上继续；大改动可建 `feat/<task>` 分支并保持可合并

## 7. 验证命令

```bash
python scripts/smoke.py                                   # 工具链路冒烟
scripts\check.bat                                        # ruff check + format + pytest（质量门）
venv\Scripts\python.exe -m pytest tests -q               # 全量测试
venv\Scripts\python.exe -m pytest tests/test_gis_toolkit.py -q   # 引擎单测
python -m uvicorn src.web.server:app --port 8080         # 启动后端（或 start.bat）
```

## 8. 审计检查点（Codex 验收标准）

Marvis 每完成一个任务需提交：
1. **变更说明**：改了哪些文件、新增工具/接口、对应验收项
2. **测试证据**：相关用例通过 + `check.bat` 结果
3. **文档标记**：涉及 Gate 的在 `docs/` 对应文档打 ✅

Codex 审计重点：
- **回归全绿**：`scripts\check.bat` 通过；pytest 无新增失败
- **schema 一致性**：新工具在 `schemas.py` / 引擎 / MCP handler 三处一致
- **安全边界**：危险操作（编辑/删除/覆盖）必须进审批；路径白名单不被破坏；无任意脚本执行
- **双入口**：自研 Agent 与 dsh/MCP 都能调用新工具
- **质量**：提交信息规范、无违规文件入库、代码风格符合规范
