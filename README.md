# GIS 智能操作助手

用自然语言操作 GIS：加载数据 → 分析（缓冲区/叠加/空间连接/泰森多边形/重投影…）→ 出图/导出。
支持 **geopandas 与 QGIS（PyQGIS worker）双引擎**，可切换；可通过 **自研 Agent** 或 **dsh（DeepSeek Harness）入口** 使用。

## 功能特性

- **自然语言驱动**：说人话完成 GIS 分析，支持多轮连续对话与思考过程展示（流式逐字输出）
- **20+ 工具**：加载/查看、空间操作（buffer/overlay/join/voronoi）、分析出图、统计导出、栅格入口、白名单算法
- **双引擎**：`GisEngine`（geopandas）/ `QgsEngine`（PyQGIS worker 子进程），`.env` 一键切换
- **可靠性**：产物自动校验（checker 回环）、会话滚动摘要（长对话不爆上下文）、危险操作可配审批
- **双入口**：自研 Agent（FastAPI + Web UI）与 dsh/MCP（DSH Desktop）共享同一套引擎

## 架构

```
自研 Agent（GisToolAgent：工具调用循环 + checker 校验 + 滚动摘要 + 流式输出）
   └─ 引擎：GisEngine（geopandas）/ QgsEngine（PyQGIS worker 子进程）
         └─ 20 个工具（load/join/voronoi/choropleth/统计/渲染/算法/栅格…）

dsh 入口（可选）：DSH Desktop ← MCP Client ← gis_mcp Server（同一套引擎）
```

## 快速开始

```bat
python -m venv venv
call venv\Scripts\activate.bat
pip install -e ".[dev]"
copy .env.example .env        # 填 DEEPSEEK_API_KEY
start.bat                     # 启动后端 http://localhost:8080
```

- 引擎切换：`.env` 里 `GIS_ENGINE=geopandas|qgis`
- 质量门禁：`scripts\check.bat`
- 冒烟：`python scripts\smoke.py`
- 部署：见 `docs/部署指南.md`

## 使用示例

> 台风灾情影响评估：加载 `data/gis_demo/storm_demo.csv`，按省份汇总经济损失、做影响地图、按阶段分析损失趋势、空间连接识别受灾最严重省份。

助手会规划并执行：`load_data → inspect → summarize → choropleth → summarize(按阶段) → join_by_location → finish`，流式输出每一步与最终结论（含关键数值）。

## 文档

- 操作能力规划（GIS 智能操作助手路线）：`docs/GIS-智能操作助手-操作能力规划.md`
- 工程化与上线方案：`docs/GIS-助手工程化与上线方案.md`
- dsh/MCP 接入与工具映射：`docs/dsh-接入方案.md`
- QGIS 引擎接入：`docs/GIS-真实引擎接入方案.md`
- 部署指南：`docs/部署指南.md`

## 工具清单（20 个）

加载/查看：`load_data` `load_raster` `inspect_data` `list_layers` `get_crs` `set_crs`
空间操作：`buffer` `overlay` `join_by_location` `voronoi` `transform_coords` `run_algorithm`
分析出图：`choropleth` `scatter_plot` `render_map` `field_statistics` `unique_values` `summarize`
交付：`export_geojson` `finish`

## 测试

```bat
call scripts\check.bat   # ruff + pytest 全绿
```
