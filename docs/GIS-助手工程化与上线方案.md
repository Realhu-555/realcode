# GIS 助手工程化与上线方案

> 配套文档：`docs/dsh-接入方案.md`（dsh/MCP 接入）｜`docs/GIS-真实引擎接入方案.md`（QGIS 引擎）｜`docs/SPEC-GIS智能操作平台.md`（MVP）
> 本文档回答一个问题：**demo 已验证（自研 agent + dsh/MCP 双入口都跑通）之后，怎么把项目做成工程化、可上线试用的产品。**
> 结论：按「工具扩展（Gate 5）→ agent 补强 → 工程化收尾」三阶段推进，每阶段有明确验收。
> 版本：v0.3 ｜ 日期：2026-08-22 ｜ 作者：胡贞虎（阶段一/二完成；阶段三 T10–T15 全部完成）

---

## 0. 一句话结论

- 目标从「demo 能跑」升级为「**工程化、可上线试用**」；
- 顺序：**先把工具做好（Gate 5 P0）→ 再补强自研 agent（checker/记忆/思考/subagent 预留）→ 最后工程化收尾（配置/日志/部署/上线清单）**；
- 双入口保持并行：自研 agent 直接调引擎（主），dsh + MCP 作为可选入口（副）。

---

## 1. 现状盘点（工程化基础）

**已有资产**
| 资产 | 位置 | 状态 |
|---|---|---|
| 自研 agent（工具调用循环） | `src/gis_toolkit/agent.py`（GisToolAgent） | 可用，冒烟通过 |
| MCP Server（20 工具） | `src/gis_mcp/`（server/tools） | 可用，dsh 接入通过 |
| 双引擎 | `GisEngine`（geopandas）/ `QgsEngine`（PyQGIS worker） | 可用 |
| 安全边界 | 路径白名单 / 文件名净化 / 工具白名单 | 已有 |
| 配置管理 | `src/utils/config.py`（pydantic-settings） | 已覆盖 GIS/MCP |
| 日志 / 健康检查 / 追踪 | `src/utils/logger.py / health.py / trace.py` | 已有 |
| 容器与脚本 | `Dockerfile` / `docker-compose.yml` / `start.bat` / `scripts/check.bat` | 已有 |
| 测试 | pytest（全量 228+ 全绿） | 已有 |

**差距（本轮补齐）**
1. 工具从 9 扩到 20，高级能力覆盖（Gate 5 实施）；
2. agent 补 checker 校验回环、滚动摘要、思考展示、subagent 预留；
3. GIS/MCP 配置进 settings（.env 可切换引擎/目录）；
4. 部署文档、上线验收清单、MCP 引擎健康检查。

---

## 2. 阶段一：工具扩展（Gate 5，P0 先行）

> 选型底稿见 `docs/dsh-接入方案.md` 10.4 节（qgis-mcp 118 工具精选映射表）。

### 2.1 任务（T1–T5，P0 五个工具）+ 后续 P1

| 任务 | MCP 工具 | 状态 |
|---|---|---|
| T1 | `gis_join_by_location`（空间连接） | ✅ |
| T2 | `gis_voronoi`（泰森多边形） | ✅ |
| T3 | `gis_get_crs` | ✅ |
| T4 | `gis_set_crs` | ✅ |
| T5 | `gis_list_layers` | ✅ |
| P1 | `field_statistics` / `unique_values` / `transform_coords` / `render_map` / `run_algorithm` / `load_raster` | ✅ |

**开发套路**：schema（引擎无关）→ 引擎方法（geopandas + QGIS 双实现）→ MCP handler（表驱动）→ 测试 + 双引擎 diff。

**验收（Gate 5）**
- MCP 工具 9 → 20，测试全绿（引擎 39 / MCP 14 / QGIS 21）；
- 同一用例在 geopandas / qgis 引擎下结果一致；
- dsh 对话可调通 `gis_join_by_location` 冒烟。

---

## 3. 阶段二：agent 补强（可靠性）

| 任务 | 内容 | 状态 |
|---|---|---|
| T6 ✅ | **checker 校验回环**：产物自动校验（`checker.py`）+ 失败回给 LLM 修正 + 连续失败超限强制终止 | 测试覆盖：空 PNG/CSV/坏 GeoJSON、回环恢复、连续失败升级 |
| T7 🔶 | **记忆升级**：短期 token 阈值滚动摘要 + 最近窗口已实现；**长期向量记忆（T7b）后置**（DeepSeek 无 embedding，待 MiniMax embedding 验证 + 向量库接入） | 短：长对话自动压缩不爆上下文（测试覆盖）｜长：待 T7b |
| T8 ✅ | **思考过程展示**：`run_stream` 工具调用前发 `tool_reason` 事件 | 测试覆盖事件顺序与内容 |
| T9 ✅ | **subagent 接口预留**：`execute_subtask()` + `sub_agent` 注入点，默认 unsupported | 测试覆盖默认与注入两种行为 |

> 顺序：T6 → T7 → T8 → T9（按价值排序，T9 只做接口不做实现）。

---

## 4. 阶段三：工程化收尾（上线标准）

| 任务 | 内容 | 状态 |
|---|---|---|
| T10 ✅ | 配置集中化：`Settings` 增加 gis_engine/gis_out_root/gis_allowed_roots/mcp_tool_timeout_ms；MCP server 与 session 从 settings 读取 | 改 .env 即切换引擎/目录（测试覆盖） |
| T11 ✅ | 结构化日志 + 轨迹落盘：agent 工具调用 json 日志；会话轨迹写入 `data/gis_traces/` | 轨迹文件可解析、含请求/产物/工具链（测试覆盖） |
| T12 ✅ | 质量门禁：`scripts/check.bat`（ruff check + ruff format + pytest）；per-file-ignores 收敛预存问题 | ruff 全量通过；测试全绿 |
| T13 ✅ | 部署：`start.bat`（后端）+ `docs/部署指南.md`（Windows 本机 + Docker + dsh 入口） | README 更新为当前架构 |
| T14 ✅ | 健康检查扩展：产物目录可写 + QGIS 前缀可用性纳入 `/api/health` | health 返回 gis_out_dir/qgis 状态 |
| T15 ✅ | 上线验收：`scripts/smoke.py` 冒烟（加载→分析→出图→导出→完成） | 一键冒烟通过（SMOKE PASSED） |

---

## 5. 上线路径（试用）

**形态 A：单机试用（推荐先做）**
```
本机 QGIS（D:\QGIS）+ venv
  ├─ 自研 agent：启动脚本 start.bat → 对话/接口
  └─ dsh 入口（可选）：MCP Server 被 DSH Desktop 调用
```

**形态 B：服务器部署（后续）**
```
Docker：FastAPI（agent 服务）+ QGIS 无头镜像（qgis_process/worker）
  ├─ /api/v1/gis-assistant/run/stream（SSE）
  └─ /api/v1/gis-assistant/files/...（产物下载）
```

**上线验收清单（T15 落地）**
- [x] 冒烟：同一句自然语言在自研 agent 与 dsh/MCP 双入口走通
- [x] 安全：白名单外路径/非法文件名被拒（测试覆盖）
- [x] 产物：PNG/CSV/GeoJSON 可下载、路径可定位（output_paths 已加）
- [x] 日志：一次会话可完整回放（轨迹）
- [x] 稳定性：连续 20 次冒烟无崩溃、无超时

---

## 6. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-08-22 | 先工具（Gate 5 P0）后 agent 补强再工程化收尾 | 用户指定顺序；工具是能力面，agent 是可靠性，工程化是上线保障 |
| 2 | 2026-08-22 | 自研 agent 为主入口，dsh/MCP 为可选入口 | 自研 agent 直接调引擎，无跨语言依赖，可独立部署上线 |
| 3 | 2026-08-22 | agent 补强顺序：checker → 记忆 → 思考 → subagent 预留 | 按对"可靠可用"的价值排序；subagent 只预留接口不实现 |
| 4 | 2026-08-22 | 目标从 demo 升级为可上线试用 | 用户明确要求工程化 |
