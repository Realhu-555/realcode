# GIS Agent 基准评测集扩展方案（v1）

> 版本：v1.1 ｜ 日期：2026-08-24 ｜ 前置：`src/gis_toolkit/bench.py`（已有 4 个任务）
> 目标：把评测从「4 个任务」扩成「覆盖 32 工具的工程回归基准」，产出可量化的成功率与工具覆盖率，用于简历展示与每次改动的回归。

## 1. 评测口径（两层，都校验「返回合格数据」）

> ⚠️ 关键澄清：「工具能调用不报错」≠「工具返回合格数据」。两层评测**都必须校验结果的数据语义**，
> 区别只在「谁在调用」——层 1 由引擎直接调用（无 LLM），层 2 由 LLM 规划后调用。

| 口径 | 含义 | 成本 | 频率 |
|---|---|---|---|
| 层 1 工具正确性 | 引擎级：每个工具按最小用例调用，**断言返回结构与数据语义合格**（不调 LLM） | 低 | 每次提交（可接 check.bat） |
| 层 2 Agent 端到端 | 真实 LLM 跑任务，**校验最终产物合格**（调 LLM） | 高 | 每周全量 / 关键改动后 |

- **防泄漏**：任务答案不写入 prompt，只用 checker 从产物/状态反推校验（沿用现有设计）
- **层 1 校验示例（“合格”标准）**：
  - `load_data`：返回行数 = 期望值、字段名集合正确、CRS 正确
  - `buffer`：要素数不变、几何类型变为 Polygon、缓冲后面积 > 原面积
  - `summarize`：CSV 行数/列名正确、合计值与源数据一致
  - `choropleth`：PNG 存在且 > 阈值、不抛异常
  - `add_features`：图层行数 +1、新要素属性/几何与入参一致
- **指标**：
  - 层 1：**工具正确率** = 返回合格数据的工具数 / 32（每个工具带 ≥1 条数据语义断言）
  - 层 2：**任务通过率** = 通过任务 / 总任务；**组合任务链路覆盖** = 任务用到的工具链种类
  - 公共：平均步数、平均耗时、失败原因归类（tool_error / check_fail / timeout / other）

## 2. 现状

- `bench.py`：`TASKS`（request + data + checks 规则函数）→ `run_one`（每任务独立 engine + `GisToolAgent`）→ 报告落 `data/gis_bench_results/<ts>/report.json`
- 已有 4 任务：choropleth / summarize / buffer / scatter（曾 4/4 通过）

## 3. 任务集设计（v1.1：单工具任务 + 组合任务）

### 3.1 单工具任务（覆盖 32 工具的正确性，层 1 + 层 2 共用同一套「合格数据」断言）

| 类 | 任务 | 数据 | 核心校验 |
|---|---|---|---|
| A 读/查看 | A1 加载并查看字段/CRS | `china_population.csv` | 调用了 load+inspect；返回行数=34 |
| | A2 字段统计 | `beijing_districts_stats.geojson` | 调用了 field_statistics |
| | A3 栅格元数据 | `dem_demo.tif` | 调用了 load_raster；宽高=100×100 |
| B 空间分析 | B1 河流缓冲 | `major_rivers.geojson` | 调用了 buffer；有 geojson 产物 |
| | B2 相交叠加 | `rivers + china_province_stats` | 调用了 overlay；有产物 |
| | B3 省会泰森 | `china_capitals_points.geojson` | 调用了 voronoi；有产物 |
| | B4 POI×北京空间连接 | `poi_demo.csv + beijing_districts` | 调用了 join_by_location；结果行数>0 |
| | B5 广东市质心 | `guangdong_cities.geojson` | 调用了 run_algorithm；几何变为点 |
| C 统计出图 | C1 面分级设色 | `guangdong_cities_stats.geojson` | 调用了 choropleth；png>10KB |
| | C2 CSV 点聚合设色 | `china_population.csv` | choropleth；png>10KB |
| | C3 散点图 | `china_population.csv` | scatter_plot；png>5KB |
| | C4 分类设色+标注 | `sichuan_cities_stats.geojson` | categorized + set_labeling；png |
| D 操作类 | D1 编辑+审批拦截 | `beijing_districts.geojson` | readonly 模式下 add_features 被拒；commit 未执行 |
| | D2 复制图层 | `china_province_stats.geojson` | duplicate_layer 成功；图层仍在 |
| | D3 工程信息 | 任意已加载图层 | get_project_info 返回 engine/layer 状态 |

> 单工具任务按「四类 × 每类选代表工具」展开，目标覆盖全部 32 个工具；
> 剩余未展开的工具（如 set_crs/transform_coords/update_geometry 等）在组合任务中覆盖。

### 3.2 组合任务（真实场景 = 一个任务里多个工具协作）

| # | 场景 | 工具链（按顺序） | 验收要点 |
|---|---|---|---|
| E1 | GDP 分析出图 | load → inspect → choropleth → summarize → export | PNG + CSV 产物齐全；汇总值=源数据合计 |
| E2 | 河流影响分析 | load rivers → buffer → overlay(省份面) → summarize → export | 相交结果要素数 >0；几何为面 |
| E3 | POI 区县分布 | load poi → join_by_location(北京区县) → summarize(每区数量) → categorized → export | 连接后行数 >0；每区 POI 计数合理 |
| E4 | 编辑+渲染交付 | load 区县 → start_editing → add point/line → commit → render_map → export | 编辑生效；渲染图存在；审批按模式生效 |
| E5 | 省会空间格局 | load capitals → voronoi → buffer(0.3) → export | 泰森多边形可导出；组合链路步数 < 上限 |

> 组合任务同时验证：**Agent 能按真实场景串起多个工具**、步数不超限、中间产物可被后续工具消费
> （例如 E3 的空间连接结果必须能被 summarize 分组）。这是单工具任务覆盖不到的。

## 4. 跑批脚本改动点（`bench.py`）

1. 支持 `--category A/B/C/D`、`--task <id>` 增量跑
2. 层 1 `engine_selfcheck()`：不调 LLM，32 个工具按最小用例调用，**每个工具带「合格数据」断言**（行数/字段/几何/CRS/产物可解析）
3. 组合任务：`request` 描述真实场景（多步），`checks` 校验**工具链顺序 + 最终产物合格**
4. D 类/组合任务用 `ApprovalGate(mode="readonly")` 或 mock 审批，避免真实卡审批
5. 报告升级：`report.json` 增加 `tool_correct_rate`（32 工具合格率）、`task_pass_rate`、`chain_covered`、`avg_steps`、`avg_duration_s`、`fail_reasons`
6. 输出人类可读 `report.md` 摘要（表格：任务/工具链/通过/失败原因）
7. 接入可选质量门：`GIS_BENCH=1 scripts\check.bat` 时追加跑层 1（工具正确性）

## 5. 成本与节奏

- 全量 15 任务 × 每任务约 3~8 步 LLM 调用 ≈ 60~120 次调用；建议**每周全量 + P0/P1 改动后增量**
- 工具可用性层每次提交跑（约几十秒，无 LLM 成本）

## 6. 验收标准

- [ ] 32 个工具均有「合格数据」断言（层 1）；5 个组合任务定义完成，校验工具链顺序与最终产物
- [ ] `python -m src.gis_toolkit.bench --category C` 可增量跑
- [ ] report.json/report.md 字段齐全（工具正确率/任务通过率/链路覆盖/avg_steps/失败原因）
- [ ] 防泄漏自查：任务 request 中不含答案数值
- [ ] 层 1 可无 LLM 跑通，且对「返回不合格数据」的实现能判定为失败（自检用例含 1 个故意错误对照）

## 7. 后续 v2（暂不做）

- 更长链路（5+ 工具）、错误恢复（首次失败后自动重试）、审批流端到端、3D 出图
