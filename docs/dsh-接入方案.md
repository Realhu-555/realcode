# dsh 接入方案（GIS 智能操作助手 · 入口改造）

> 配套文档：`docs/SPEC-GIS智能操作平台.md`（MVP）｜`docs/GIS-真实引擎接入方案.md`（QGIS 引擎接入）｜`docs/GIS-智能助手-工具调用设计.md`（9 个工具定义）
> 本文档回答一个问题：**能不能用 DeepSeek Harness（dsh）做助手的入口，把我们的 GIS 引擎接进去。**
> 结论：**可以，且推荐。dsh 负责「UI + 会话 + agent 循环 + 模型」，我们的 GIS 引擎封装成 Python MCP Server 被 dsh 调用，QgsEngine 零重写。**
> 版本：v0.2 ｜ 日期：2026-08-22 ｜ 作者：胡贞虎（Gate 1/2/3 已完成）

---

## 0. 一句话结论

- **dsh（DeepSeek Harness）** 是 DeepSeek 官方开源的 Agent 运行时（MIT，`Agent = Model + Harness`），核心理念「一切皆插件」，原生是 **MCP 客户端**；
- 本机已安装 **DSH Desktop**（`C:\Users\25062\AppData\Roaming\DSH Desktop`，配置在 `C:\Users\25062\.dsh`），默认模型 `deepseek-v4-flash`（经 `@liustack/modlens`），已装记忆插件与插件市场；
- **接入方式 = 我们的 GIS 引擎封装成 Python MCP Server（stdio）**，dsh 通过内置 MCP 客户端调用 9 个工具；不重写 Node、不重写引擎；
- 现有 FastAPI + Vue 前端保留为可回退入口，但不再作为主入口演进。

---

## 1. 背景：为什么换入口

### 1.1 现状（自研入口已跑通）

```
浏览器 → Vue 前端（GisAssistant.vue）
       → FastAPI（/api/v1/gis-assistant/run/stream）
       → GisToolAgent（单 agent，OpenAI 格式 function calling）
       → GisEngine / QgsEngine（9 个工具，PyQGIS worker）
       → 产物 PNG/CSV/GeoJSON
```

自研部分承担的职责：对话 UI、会话管理（`GisSessionStore`）、SSE 流式、短期记忆截断、模型适配、agent 工具循环。这些与 dsh 重复。

### 1.2 dsh 是什么

- GitHub：`deepseek-ai/deepseek-harness`；运行：`npx @deepseek-ai/dsh web`（Web UI 默认 `127.0.0.1:3080`）；桌面版：DSH Desktop（Electron）；
- 基于 Cordis 插件框架：模型适配器、工具、会话、主循环、CLI、Web UI、slash 命令、skills、**MCP 客户端**全部是插件；
- 支持多模型提供商（DeepSeek / OpenAI / Anthropic / Gemini…）、读取 `AGENTS.md` / `CLAUDE.md`、社区插件市场（`dsh-community-market`）；
- 目前 **developer preview**，迭代快，存在破坏性变更风险。

### 1.3 入口改造的目标形态

```
DSH Desktop（入口：对话 UI + 会话管理 + agent 循环 + 模型 + 记忆插件）
   └─ MCP Client（dsh 内置）
        └─ Python MCP Server（本项目，stdio，FastMCP）
              └─ create_gis_engine()（GIS_ENGINE=geopandas|qgis 切换）
                    └─ GisEngine（geopandas）/ QgsEngine（PyQGIS worker）
```

用户只需打开 DSH Desktop，选择 GIS 助手预设，用自然语言操作 GIS——「入口」就是 dsh。

---

## 2. 为什么用 dsh（取舍）

| 维度 | 现状（自研） | dsh 接入后 | 结论 |
|---|---|---|---|
| 对话 UI / 流式输出 | Vue 自研 | dsh 内置 | 省维护 |
| 会话管理 | `GisSessionStore` JSON | dsh 会话机制 | 迁移 |
| agent 主循环 | `GisToolAgent` | dsh 主循环 | 简化 |
| 模型适配 | 自研 provider（DeepSeek 兼容 OpenAI） | dsh 多提供商 | 更强 |
| 记忆 | 短期截断 + SQLite（无 RAG） | dsh 记忆插件 + 自研长期记忆可保留 | 保留自研长期记忆 |
| GIS 工具 | 9 个 schema + 引擎 | MCP 工具（复用引擎） | **零重写** |
| 权限/安全 | 路径白名单 + 文件名净化 | dsh 沙箱 + 自研白名单叠加 | 叠加 |
| 技术栈 | Python 后端 | 入口变 Node（dsh），GIS 仍是 Python | 混合可接受 |
| 风险 | 可控 | dsh 是 preview 版 | 薄封装 + MCP 标准协议兜底 |

**不做的**：不把 GIS 逻辑用 Node 重写（PyQGIS 无法在 Node 内运行）；不用 dsh 替代我们的安全边界（路径白名单、文件名净化、工具白名单继续生效）。

---

## 3. 目标架构

```
┌─────────────────────────────────────────────┐
│ DSH Desktop（入口）                          │
│  - 对话 UI / 流式输出 / 会话列表             │
│  - agent 主循环（工具调用）                  │
│  - 模型：deepseek-v4-flash（modlens）       │
│  - 记忆插件 / slash 命令 / skills            │
│  - MCP Client（stdio → 本项目 MCP Server）   │
└───────────────┬─────────────────────────────┘
                │ MCP 协议（stdio）
┌───────────────▼─────────────────────────────┐
│ Python MCP Server（本项目，FastMCP）         │
│  - gis_* 9 个工具（MCP tools）              │
│  - 按 dsh 会话维护 engine 实例（图层/产物）  │
│  - 安全边界：allowed_roots / 文件名净化      │
│  - 双引擎切换：GIS_ENGINE=geopandas|qgis    │
└───────────────┬─────────────────────────────┘
                │
┌───────────────▼─────────────────────────────┐
│ GisEngine / QgsEngine（现有，零改动）        │
│  - 9 个工具同接口                            │
│  - 产物写输出目录（PNG/CSV/GeoJSON）         │
└─────────────────────────────────────────────┘
```

**会话状态设计**：
- 每个 dsh 会话对应一个 `engine` 实例（持有当前图层、产物清单、输出目录）；
- MCP Server 以「客户端会话」为维度维护 `session_id -> engine`，会话结束/空闲超时回收；
- 产物目录沿用 `data/gis_toolkit_out/<session_id>/`，路径规则与现状一致。

---

## 4. MCP 工具映射表（9 个工具 → MCP tools）

工具名统一加 `gis_` 前缀，避免与 dsh 内建工具（bash/fs/网络等）冲突；参数与现有 schema 一致（引擎无关，QGIS 接入时不变）。

| MCP 工具名 | 参数（沿用现有 schema） | 引擎方法 | 返回（JSON 摘要） | 备注 |
|---|---|---|---|---|
| `gis_load_data` | `path` | `load_data` | 行数/字段/CRS/范围 | 输入路径白名单校验 |
| `gis_inspect_data` | — | `inspect_data` | 字段/行数/CRS/范围/前 5 行 | 决定后续操作前先调 |
| `gis_buffer` | `distance` | `buffer` | 要素数/几何类型 | 单位随 CRS |
| `gis_overlay` | `other_path, how` | `overlay` | 结果行数/字段 | `how` 枚举硬校验 |
| `gis_choropleth` | `column, scheme, k, output` | `choropleth` | 产物文件名 + 分级统计 | PNG 产物路径回传 |
| `gis_scatter_plot` | `x, y, output` | `scatter_plot` | 产物文件名 | PNG 产物路径回传 |
| `gis_summarize` | `column, groupby, agg, output` | `summarize` | 产物文件名 + 摘要统计 | CSV 产物路径回传 |
| `gis_export_geojson` | `output` | `export_geojson` | 产物文件名 | 文件名净化 |
| `gis_finish` | `outputs, summary` | `finish` | 最终交付摘要 | 结束当前任务声明 |

**产物展示（需 Gate 3 验证）**：
- PNG/CSV 返回路径后，如何让 dsh UI 显示图片/文件 —— 两种候选：
  1. 工具返回 `image` 类型 content（MCP 支持 image content，需确认 dsh 客户端渲染）；
  2. 工具返回本地文件路径 + dsh 附件/文件查看机制。
- 备选：MCP Server 额外提供一个 `gis_open_outputs` 目录浏览能力，或产物通过 dsh 附件上传机制注入。

---

## 5. dsh 插件 bundle 设计（可选，先简化后完善）

**阶段 1（先跑通，不做插件）**：在 DSH 的 MCP 设置里配置一个 stdio MCP server（用 `dsh-mcp-settings` 或官方 MCP 管理界面），命令为启动我们 Python MCP Server 的脚本：

```
python H:\ai-dev-platform\mcp\gis_server.py --out-root H:\ai-dev-platform\data\gis_toolkit_out
```

**阶段 2（体验完善）**：做一个薄 npm bundle（参考 wps-dsh-plugin / upstash 模式）：
- 安装时自动注册上面的 MCP server（`dsh.mcpServers` 配置或 cordis 插件启动）；
- 附带 GIS 助手的预设/提示词（slash 命令：`/gis 加载 xxx 并出分级图`）；
- bundle 只做注册与提示词，**不含 GIS 逻辑**（避免被 dsh preview 变更牵连）。

---

## 6. 安全边界（沿用现状，只增不减）

1. 工具白名单：只暴露 `gis_*` 9 个工具，不暴露任意表达式/脚本执行；
2. 输入路径白名单：`allowed_roots` 默认 `data/`，MCP Server 复用 `_check_input_path`；
3. 产物文件名净化：复用 `_sanitize_filename`；
4. dsh 沙箱权限：按 dsh 权限模型对 bash/fs 等内建工具收紧（GIS 会话只需 MCP 工具）；
5. 危险操作审批：覆盖写、删除等保持「用户确认」（dsh 权限体系叠加）；
6. GPL 合规不变：QGIS 引擎走本机/服务化，商业分发按 `GIS-真实引擎接入方案.md` 第 6 节处理。

---

## 7. 落地步骤（Gate）

| Gate | 内容 | 验收标准 |
|---|---|---|
| **Gate 1** ✅ 2026-08-22 | Python MCP Server：`mcp` SDK（FastMCP），stdio 模式，9 个 `gis_*` 工具，复用 `create_gis_engine` | 12/12 测试全绿；stdio 握手正常（9 个 gis_* 工具可列出） |
| **Gate 2** ✅ 2026-08-22 | dsh 接入：`cordis.patch.yml` insert `@deepseek-ai/dsh-mcp-client`；desktop/web profile 显式装依赖 | 进程级验证：DSH Desktop 已 spawn `gis_mcp/server.py`，工具注册为 `mcp__gis-mcp__gis_*` |
| **Gate 3** ✅ 2026-08-22 | 冒烟：完整链路「加载 gdp_demo.csv → 分级设色 → 汇总 → 导出 GeoJSON」 | 工具注册与连接已确认；**对话内自然语言走通 + 产物展示待用户实测确认** |
| **Gate 4** | 会话状态 + 双引擎 + 安全核对 | 多会话互不串图层；`GIS_ENGINE=qgis` 切换可用；白名单/净化用例全绿 |
| **Gate 5** 规划中 | 高级工具扩展：P0（`gis_join_by_location` + `gis_voronoi`）先行 | 新工具在 MCP / DSH 双端可用，冒烟通过；schema 计入上下文成本 |

---

## 8. 风险与对策

| 风险 | 对策 |
|---|---|
| dsh 是 developer preview，接口/插件 API 可能破坏性变更 | 只依赖 MCP 标准协议；插件 bundle 薄封装；现有 FastAPI+Vue 保留可回退 |
| MCP 产物（PNG/CSV）在 dsh UI 展示不理想 | Gate 3 专项验证；备选 image content / 附件机制 / 目录浏览工具 |
| DSH Desktop 拉起 Python MCP server 的环境差异（PATH/Python 版本） | 用绝对路径 + 独立启动脚本（bat），日志落盘便于排查 |
| 多 dsh 会话共享引擎导致状态串 | MCP Server 按会话维护 engine 实例，空闲超时回收 |
| `deepseek-v4-flash` 工具调用遵循度不足 | Gate 3 冒烟验证；必要时按预设切换 `deepseek-v4` 或提高 reasoningEffort |
| dsh 记忆插件与自研长期记忆重复/冲突 | 自研长期记忆（SQLite+向量）作为 MCP 工具 `gis_memory_*` 暴露，由 dsh 会话调用，统一口径 |

---

## 9. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-08-21 | 用 dsh（DeepSeek Harness）做助手入口 | 对话 UI/会话/agent 循环/模型全内置，原生 MCP 客户端，本机已装好 |
| 2 | 2026-08-21 | GIS 引擎封装为 Python MCP Server，不重写 Node | PyQGIS 无法在 Node 内运行，QgsEngine 零重写，双引擎切换保留 |
| 3 | 2026-08-21 | 工具统一加 `gis_` 前缀 | 避免与 dsh 内建工具冲突 |
| 4 | 2026-08-21 | 现有 FastAPI+Vue 保留为可回退入口，不作为主入口演进 | dsh 为 preview 版，保留独立可运行的 MVP 出口 |
| 5 | 2026-08-22 | Gate 1/2/3 完成：MCP Server + dsh 接入 + 工具注册验证 | 测试全绿、DSH Desktop 已 spawn gis_mcp server（进程级证据） |


---

## 10. 高级玩法：工具扩展规划（Gate 5）

> 参照 ESRI ArcGIS AI 助手（2024）的风暴数据链式分析案例 + 社区 `nkarasiak/qgis-mcp`（118 工具）清单，规划下一批 GIS 工具。
> 目标：让助手能做「空间连接 / 插值 / 地形 / 网络分析 / 空间统计 / 适宜性」等高级操作，而不止步于 9 个基础工具。

### 10.1 参照案例拆解（ESRI 风暴链 → 我们的工具映射）

| ESRI 演示环节 | 需要的能力 | 现状 / 规划 |
|---|---|---|
| 收集风暴数据 | 数据加载 | `gis_load_data` ✅ |
| 查看报告 | 属性查看 / 统计 | `gis_inspect_data` / `gis_summarize` ✅ |
| 制作风暴热力图 | 分级设色 / 核密度 | `gis_choropleth` ✅；KDE 规划中 |
| 数据汇总 | 聚合统计 | `gis_summarize` ✅ |
| 预测趋势 | 统计 / 时序外推 | 规划 `gis_time_series`（暂缓） |
| 趋势图可视化 | 图表 / 地图 | `gis_choropleth` ✅ |
| 扩展分析（受影响供应链） | **空间连接 / 空间查询** | **`gis_join_by_location`（P0）** |
| 回答链接回源数据 | 数据溯源 | 工具返回携带来源图层 / 查询串（规划） |

### 10.2 工具扩展优先级清单

| 优先级 | MCP 工具 | 业务场景 | QGIS 实现 | 成本 |
|---|---|---|---|---|
| P0 | `gis_join_by_location` ✅ | POI 归属行政区、设施影响范围统计 | Processing「按位置连接」 | 低 |
| P0 | `gis_voronoi` ✅ | 服务范围划分（商圈 / 站点） | `QgsGeometry` Voronoi / Processing | 低 |
| P1 | `gis_raster_terrain` | 坡度 / 坡向 / 山体阴影 | GDAL 地形算法 | 低 |
| P1 | `gis_interpolate` | 气象站 → 连续温度面（IDW / 克里金） | Processing「插值」 | 低 |
| P1 | `gis_network_analysis` | 最短路径、服务区 / 等时圈 | QNEAT3 / Processing 网络算法 | 中 |
| P2 | `gis_kde` | 事故 / 犯罪热点密度 | GDAL 核密度 | 中 |
| P2 | `gis_hotspot` | Getis-Ord Gi* 热点 | 需额外统计库（esda 等） | 高 |
| P2 | `gis_least_cost_path` | 输电线 / 管道最低成本路径 | Processing LeastCostPath | 中 |
| P3 | `gis_raster_calc` | 栅格计算器 / 重分类 | GDAL 栅格代数 | 中 |
| P3 | `gis_viewshed` | 瞭望塔 / 基站视域 | GDAL viewshed | 中 |

### 10.3 约束与注意事项

1. **工具总数控制**：工具 schema 全量进模型上下文，建议精选 **20~30 个高频工具**，避免 token 膨胀；
2. **安全边界不变**：仍不暴露任意 Python / 表达式执行，高级能力一律以白名单工具形式提供；
3. **统一套路**：每个工具走「schema + handler + 单元测试 + QGIS 行为校准」，参考 Gate 2 的 9 个工具；
4. **按场景驱动**：优先做目标业务场景（应急 / 规划 / 交通 / 农业 / 水利）最高频的工具，而非一次性全做。


### 10.4 参考 qgis-mcp 118 工具精选映射表（Gate 5 选型底稿）

> 来源：[nkarasiak/qgis-mcp](https://github.com/nkarasiak/qgis-mcp)（118 个工具，17 类）。
> 原则：① 保留我们 9 个已上线工具；② 从 118 精选 **~21 个**高频工具补齐能力面（总量控制在 30 个内防 token 膨胀）；
> ③ 借鉴其 `compound` 分组思路：工具多时可开"分组模式"（action+params）降每轮 schema 开销；
> ④ 安全边界不变：**不引入 `execute_code` / 任意表达式执行**。

#### A. 已覆盖（我们 9 个工具 → 118 对应）

| 我们（已有） | 对应 118 工具 | 说明 |
|---|---|---|
| `gis_load_data` | Layers.add_vector_layer | CSV/GeoJSON/zip → 图层 |
| `gis_inspect_data` | Features.get_field_statistics | 字段/行数/CRS/范围/样例 |
| `gis_buffer` | Processing（native:buffer） | 缓冲区 |
| `gis_overlay` | Processing（native:intersection/union/…） | 空间叠加 |
| `gis_choropleth` | Styling.set_layer_style(graduated) | 分级设色 |
| `gis_scatter_plot` | — | 散点图（无对应，保留自研） |
| `gis_summarize` | — | 聚合统计导出 CSV |
| `gis_export_geojson` | Layers.export_layer | 导出 GeoJSON |
| `gis_finish` | — | 任务完成声明 |

#### B. 精选新增（Gate 5 实施）

| 优先级 | 建议 MCP 工具 | 对应 118 工具 | 业务场景 | QGIS 实现 | 备注 |
|---|---|---|---|---|---|
| P0 | `gis_join_by_location` | Analysis.spatial_join | POI 归属行政区、影响范围统计 | Processing spatial join | 已实现 ✅ |
| P0 | `gis_voronoi` | Processing（native:voronoi） | 服务范围划分 | Voronoi 算法 | 已实现 ✅ |
| P0 | `gis_get_crs` | Layers.get_layer_crs | 查看当前图层 CRS | `layer.crs()` | 已实现 ✅ |
| P0 | `gis_set_crs` | Layers.set_layer_crs | 统一坐标系（先统一再做叠加） | `layer.setCrs()` | 已实现 ✅ |
| P0 | `gis_list_layers` | Layers.get_layers | 查看会话内图层/产物状态 | 引擎状态快照 | 已实现 ✅ |
| P1 | `gis_load_raster` | Layers.add_raster_layer | 加载栅格（地形/影像） | `QgsRasterLayer` | 栅格入口 |
| P1 | `gis_field_statistics` | Features.get_field_statistics | 字段统计（min/max/mean 等） | `QgsAggregateCalculator` | 已实现 ✅ |
| P1 | `gis_unique_values` | Features.get_unique_values | 分类列取值（用于 categorized） | `layer.uniqueValues()` | 已实现 ✅ |
| P1 | `gis_render_map` | Rendering.render_map | 出图/截图（含当前图层） | 引擎渲染导出 | 已实现 ✅ |
| P1 | `gis_transform_coords` | System.transform_coordinates | 坐标转换（度↔米/投影） | `QgsCoordinateTransform` | 已实现 ✅ |
| P1 | `gis_run_algorithm` | Processing.execute_processing | **白名单** Processing 算法 | `processingRegistry` + 算法白名单 | 已实现 ✅（白名单 3 算法） |
| P1 | `gis_zonal_statistics` | Analysis.zonal_statistics | 分区统计（栅格↔矢量） | Processing zonal statistics | |
| P1 | `gis_interpolate` | Processing（插值算法） | IDW / 克里金 | Processing interpolate | 已规划 |
| P2 | `gis_categorized` | Styling.set_layer_style(categorized) | 分类设色（非数值列） | `QgsCategorizedSymbologyRenderer` | |
| P2 | `gis_identify` | Query.identify_features | 位置/点选查询 | 空间索引查询 | |
| P2 | `gis_join_by_attribute` | Layers.add_table_join | 属性表连接 | `QgsVectorLayerJoinInfo` | |
| P2 | `gis_raster_terrain` | Processing（slope/aspect/hillshade） | 坡度/坡向/山体阴影 | GDAL 算法 | 已规划 |
| P2 | `gis_kde` | Processing（heatmap） | 核密度热点 | GDAL heatmap | 已规划 |
| P2 | `gis_list_algorithms` | Processing.list_processing_algorithms | 列出白名单内可用算法 | `processingRegistry` | 配合 run_algorithm |
| P3 | `gis_raster_calc` | Analysis.raster_calculator | 栅格计算/重分类 | GDAL 栅格代数 | 已规划 |
| P3 | `gis_export_layout` | Layouts.export_layout | 打印排版导出（地图+图例+比例尺） | `QgsLayoutExporter` | 有需求再做 |

> 合计：9（已有）+ 22（新增）= 31 个，接近 30 个预算上限；若开启 compound 分组模式可压到 ~15 组。

#### C. 明确排除（含原因）

| 118 工具（类别） | 排除原因 |
|---|---|
| `System.execute_code` | 执行任意 PyQGIS，违反安全边界，**绝不引入** |
| `System.batch_commands` | 批量命令绕过工具白名单 |
| `System.diagnose / list_qgis_instances / get_message_log` | 桌面 GUI / 多实例诊断，无头不适用 |
| `Plugins.*`（list/install/reload） | 插件管理高权限，与 GIS 助手职责无关 |
| `Connections.*`（PostgreSQL 等） | 依赖外部数据库连接与凭据，暂缓 |
| `Bookmarks.* / Map themes.*` | 桌面交互特性，无头不适用 |
| `Layouts.* / Atlas.*`（全套排版） | 打印排版后置，仅保留 `gis_export_layout` 一个出口 |
| `Editing.*`（start/commit/rollback/undo/redo） | 要素编辑=危险写操作，需 Phase 4 审批机制 |
| `get_3d_screenshot` | 无头环境不支持 3D |
| `create_processing_model / run_model / create_layout` 等 | 创作类复杂操作，收益低、维护成本高 |
