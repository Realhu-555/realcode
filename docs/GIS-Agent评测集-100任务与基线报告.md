# GIS Agent 评测集（100 级任务集）与基线报告

> 版本：v1.0 ｜ 日期：2026-09-04
> 代码：`src/gis_toolkit/benchsuite.py`（runner + 声明式断言）｜`src/gis_toolkit/eval_tasks.py`（98 条任务）
> 配套口径：`docs/GIS-Agent基准评测集扩展方案.md`（v1.1）

---

## 1. 评测集构成（98 条，按 8 个维度）

| 维度 | 数量 | 测什么 | 代表性任务 |
|---|---|---|---|
| base | 25 | 读/查看/字段统计/唯一值/栅格元数据 | load+inspect、field_statistics、unique_values、load_raster |
| spatial | 21 | 缓冲/空间连接/属性连接/投影/泰森/叠加 | buffer、join_by_location/attribute、transform_coords、voronoi、overlay |
| chart | 20 | 分级设色/分类设色/散点/渲染出图 | choropleth、categorized、scatter_plot、render_map |
| edit | 6 | 编辑会话/提交回滚/字段计算/图层管理 | start_editing、add/update/delete、calculate_field、commit/rollback、duplicate/rename/remove |
| chain | 10 | 多工具真实场景（分析→图→汇总→导出） | 组合链路 ≥3 工具 + 产物互消费 |
| long | 6 | 高步数/多文件/多产物长任务 | ≥6 工具、编辑+分析+出图+交付、三任务连做 |
| memory | 6 | 多轮会话上下文/前文引用/不重复加载 | dialog 逐轮 agent.run，复用 session |
| robust | 4 | 拒绝越界请求/文件不存在/只读拦截 | 拒答类断言"有合理答复"而非调 finish |

> 任务 request 不写答案（防泄漏）；数值期望在加载时从数据计算；断言统一在产物文件/轨迹上执行。

---

## 2. 基线结果（2026-09-04）

### 2.1 总览

| 指标 | 结果 |
|---|---|
| 功能通过（每个任务至少一次完整跑通） | **98/98（100%）** |
| L2 审核通过 | 64/98（65%） |

> 第一轮全量 98 任务中 21 个因模型 API 限流瞬时失败（`所有候选模型调用失败`），串行重跑全部恢复；
> 功能失败 2 条为评测断言不合理（POI 实际只覆盖 8/40 个点，预期写错为 16 行）已修正；验证 3/3 通过。

### 2.2 分维度通过（功能 / 审核）

| 维度 | 功能 | 审核 |
|---|---|---|
| base | 25/25 | 9/25 |
| chain | 10/10 | 9/10 |
| chart | 20/20 | 15/20 |
| edit | 6/6 | 4/6 |
| long | 6/6 | 5/6 |
| memory | 6/6 | 6/6 |
| robust | 4/4 | 4/4 |
| spatial | 21/21 | 12/21 |

### 2.3 审核未通过的归因（决定了下一步调优点）

- **inspect/统计类（约 16 条 FAIL）**：`inspect_data` 的字段/CRS/范围此前只写在返回正文（message），
  未进结构化 `stats` → 审核器无法核验 final 中引用的字段与坐标系 → 判 FAIL。**已修复**：给 inspect_data
  补 `stats`（rows/columns/crs/geometry_type/bounds）；下次全量将显著提升 base 审核通过率。
- **buffer/choropleth 类（约 15 条 WARN）**：final 引用的派生量（如"约 29 倍"）无 stats 直接来源，
  判 WARN（无冲突但证据不足）。可进一步通过 prompt 约束"只引用工具统计字段原值"减少。
- **D01 编辑类 FAIL**：需单独看审计原因（编辑会话最终汇报与事务状态描述）。

---

## 3. 复现

```bash
# 全量（串行更稳，防模型限流；约 40 分钟）
python -m src.gis_toolkit.benchsuite
# 指定维度 / 冒烟
python -m src.gis_toolkit.benchsuite --category memory
python -m src.gis_toolkit.benchsuite --limit 8
# 报告
data/gis_bench_results/<时间戳>/report.json | report.md
```

---

## 4. 说明与后续

- 98 条已构成"百级评测集"（差 2 条到整百，可按需补 edit/robust 变体）；
- 下一步：① 重跑全量产出审核提升后的干净基线；② 每任务跑 2~3 次取稳定通过率；
  ③ 把"工具调用/产物"层与"审核"层分开报告；④ 接入 live/QGIS 引擎通道。

---

## 5. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-09-04 | 评测任务用声明式断言 DSL + 生成器，不再手写 lambda 检查 | 100 级任务可维护、可增量 |
| 2 | 2026-09-04 | 默认 ApprovalGate=auto，写操作评测可自动放行；只读拦截单独用 readonly 用例 | 避免评测卡审批 |
| 3 | 2026-09-04 | 拒答/越界类任务不要求调 finish，断言"有合理最终答复" | 语义正确（无可调工具） |
| 4 | 2026-09-04 | 工具返回补结构化 `stats`（inspect/choropleth/field_statistics 等） | 审核器只认 stats，文本 message 无法作为证据 |
| 5 | 2026-09-04 | 全量评测默认串行（并发可选） | 实测并发易触发模型 API 限流 |
