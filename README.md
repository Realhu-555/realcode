# GIS 智能操作助手

用自然语言操作 GIS：加载数据 → 分析（缓冲区/叠加/空间连接/泰森多边形/重投影…）→ 出图/导出。
支持 **geopandas 与 QGIS（PyQGIS worker）双引擎**，可切换；可通过 **自研 Agent** 或 **dsh（DeepSeek Harness）入口** 使用。

## 架构

```
自研 Agent（GisToolAgent，工具调用循环 + checker 校验 + 滚动摘要）
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

## 文档

- 工程化与上线方案：`docs/GIS-助手工程化与上线方案.md`
- dsh/MCP 接入与工具映射：`docs/dsh-接入方案.md`
- QGIS 引擎接入：`docs/GIS-真实引擎接入方案.md`
- MVP 执行文档：`docs/SPEC-GIS智能操作平台.md`

## 工具清单（20 个）

加载/查看：`load_data` `load_raster` `inspect_data` `list_layers` `get_crs` `set_crs`
空间操作：`buffer` `overlay` `join_by_location` `voronoi` `transform_coords` `run_algorithm`
分析出图：`choropleth` `scatter_plot` `render_map` `field_statistics` `unique_values` `summarize`
交付：`export_geojson` `finish`

## 测试

```bat
call scripts\check.bat   # ruff + pytest 全绿
```
