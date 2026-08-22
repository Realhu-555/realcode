# GIS 智能操作助手 · 操作能力规划

> 配套文档：`docs/GIS-助手工程化与上线方案.md`（工程化）｜`docs/dsh-接入方案.md`（dsh/MCP 与工具映射）｜`docs/GIS-真实引擎接入方案.md`（QGIS 引擎）
> 本文档回答一个问题：**如何从「数据分析助手」升级为「GIS 智能操作助手」——让助手像人一样操作 GIS 系统（编辑要素、管理图层、定制样式、排版出图、管理工程），而不只是分析数据出报告。**
> 结论：分 4 个 Gate 补齐操作类能力，配套危险操作审批机制；远期演进到 PyQGIS 插件宿主（操作正在运行的 QGIS 工程）。
> 版本：v0.1 ｜ 日期：2026-08-23 ｜ 作者：胡贞虎

---

## 0. 定位调整（一句话）

- 旧定位：**数据分析助手**——用户提问，助手调算法，出图出结论；
- 新定位：**GIS 智能操作助手**——用户下达操作指令，助手像人一样驱动 QGIS：加图层、编辑要素、改样式、排版出图、管理工程；数据分析只是其中一类能力。
- 两者不是二选一：**分析能力保留并继续扩展，操作能力是新主线**。

---

## 1. 为什么必须补操作能力

| 维度 | 数据分析助手（现状） | GIS 操作助手（目标） |
|---|---|---|
| 交互 | 问 → 算 → 答 | 指令 → 操作 GIS → 交付 |
| 数据 | 只读分析 | 可读可改（增删改要素） |
| 界面 | 背后计算，用户看不到 GIS | 操作的就是用户眼前的 GIS 工程 |
| 价值 | 汇报材料、统计报表 | 替人干活：改图、整理数据、出图 |
| 天花板 | 问它要数据 | 让它干活 |

现状的 20 个工具几乎全是**分析/只读**类；要成为"会操作 GIS 的助手"，必须补操作类工具（编辑/图层/工程/样式/排版/数据源）。

---

## 2. 操作能力分类与工具规划

> 对照 `nkarasiak/qgis-mcp` 118 工具（其 C 表我们之前排除了 Editing/Layouts 等，现因定位调整重新纳入，但套我们的安全边界）。

### A. 要素编辑（操作数据）—— P0

| MCP 工具 | 说明 | QGIS 实现 | 安全 |
|---|---|---|---|
| `gis_add_features` | 新增要素（点/线/面，指定几何与属性） | `QgsVectorLayerEditBuffer` | 危险操作：审批 |
| `gis_update_features` | 按条件更新属性 | `changeAttributeValue` | 危险操作：审批 |
| `gis_update_geometry` | 修改要素几何 | `changeGeometry` | 危险操作：审批 |
| `gis_delete_features` | 按条件删除要素 | `deleteFeatures` | 危险操作：审批 |
| `gis_start_editing` / `gis_commit_edits` / `gis_rollback_edits` | 编辑会话（事务式） | `startEditing/commitChanges/rollBack` | 编辑必须走会话 |

> 设计要点：所有编辑操作**必须在编辑会话内**（start → 操作 → commit/rollback），避免半截操作污染数据；删除/覆盖写必须有用户审批。

### B. 图层管理—— P0

| MCP 工具 | 说明 | QGIS 实现 |
|---|---|---|
| `gis_list_layers` ✅ | 会话图层清单（已有） | 引擎状态 |
| `gis_set_layer_visibility` | 图层可见性开关 | `layer.setItemVisibilityChecked` |
| `gis_duplicate_layer` | 复制图层（编辑前先复制，安全兜底） | `QgsVectorLayerUtils.duplicate` |
| `gis_set_active_layer` | 切换当前操作图层 | 引擎状态 |

### C. 样式定制—— P1

| MCP 工具 | 说明 | QGIS 实现 |
|---|---|---|
| `gis_categorized` | 分类设色（非数值列） | `QgsCategorizedSymbologyRenderer` |
| `gis_set_labeling` | 要素标注（字段名标注） | `QgsVectorLayerSimpleLabeling` |
| `gis_apply_style_qml` / `gis_save_style_qml` | 样式文件导入/导出 | `layer.loadNamedStyle/saveNamedStyle` |

### D. 工程管理—— P1

| MCP 工具 | 说明 | QGIS 实现 |
|---|---|---|
| `gis_create_project` / `gis_save_project` / `gis_load_project` | QGIS 工程（.qgz）建/存/读 | `QgsProject` |
| `gis_get_project_info` | 工程信息（图层/CRS/范围） | `QgsProject` |

### E. 地图排版（Layout 出图）—— P2

| MCP 工具 | 说明 | QGIS 实现 |
|---|---|---|
| `gis_create_layout` | 新建布局 | `QgsPrintLayout` |
| `gis_add_layout_map` / `gis_add_layout_legend` / `gis_add_layout_scalebar` | 布局添加地图/图例/比例尺 | `QgsLayoutItem*` |
| `gis_export_layout` | 导出 PDF/PNG | `QgsLayoutExporter` |

### F. 数据源连接—— P2（暂缓部分）

| MCP 工具 | 说明 | 状态 |
|---|---|---|
| `gis_add_web_layer` | 加载 WMS/XYZ 底图 | 规划（底图类，安全） |
| `gis_connect_postgis` | PostGIS 数据库连接 | **暂缓**（依赖外部凭据，需单独安全设计） |

---

## 3. 安全机制：危险操作审批（操作类的前提）

操作类工具（编辑/删除/覆盖）不能像分析工具一样直接执行，需要**用户确认**。

### 3.1 双入口统一审批
- **自研 agent**：工具执行前检查是否为危险操作，是则回调 `on_approve`（前端弹确认），拒绝则返回 `status=rejected`；
- **dsh/MCP**：利用 MCP `ToolAnnotations`（`destructive: true`）+ dsh 的 elicitation 确认机制（参考 qgis-mcp：`QGIS_MCP_AUTO_CONFIRM` 默认关闭 elicitation，由客户端确认）。

### 3.2 审批清单（默认需确认）
| 操作 | 级别 | 备注 |
|---|---|---|
| 删除要素 / 删除图层 | 危险 | 默认拒绝，需确认 |
| 修改/新增要素 | 中度 | 需确认（编辑会话内可批量确认一次） |
| 覆盖写已有产物文件 | 中度 | 需确认 |
| 数据源连接（外部服务） | 中度 | 需确认 |
| 分析/只读操作 | 安全 | 无需确认 |

### 3.3 兜底策略
- 编辑强制走**会话 + 提交前预览**（commit 前返回将影响的要素数，用户确认）；
- 默认拒绝超时（`default_on_timeout=reject`，参考既有 ApprovalGate 设计）；
- 审计日志：所有危险操作记录到轨迹（谁/何时/改了什么）。

---

## 4. 宿主形态演进（远期）

| 阶段 | 形态 | 说明 |
|---|---|---|
| 现在 | 无头 worker | 助手在幕后驱动 PyQGIS 运算，用户看不到 QGIS 界面 |
| Gate 9 | **PyQGIS 插件宿主** | QGIS 插件（QTimer + TCP socket）+ 外部 MCP/agent 驱动——**助手操作的就是用户眼前正在运行的 QGIS 工程**（参考 qgis-mcp 架构：插件进程内执行 + FastMCP 外部桥） |

> 插件宿主是"GIS 系统里的智能助手"的最终形态：用户打开 QGIS 看到助手面板，下指令，图层树/画布/样式实时变化。

---

## 5. 分阶段路线（Gate）

| Gate | 内容 | 验收标准 |
|---|---|---|
| **Gate 6**（P0） | 要素编辑（会话式）+ 图层管理 + 危险操作审批 | 能对话完成"新增/修改/删除要素"（带审批）；编辑会话 commit/rollback 正确 |
| **Gate 7**（P1） | 样式定制（分类设色/标注）+ 工程管理 | 能对话完成"按地类分类设色并标注"；工程可保存/重开 |
| **Gate 8**（P2） | 地图排版（布局出图）+ 数据源（WMS/XYZ 底图） | 能对话产出带图例/比例尺的 PDF/PNG；底图可加载 |
| **Gate 9**（远期） | PyQGIS 插件宿主（操作当前工程） | 插件面板对话，操作实时反映在用户 QGIS 界面 |

> 前置依赖：Gate 6 必须先实现**审批机制**（否则编辑/删除无防护）；Gate 9 依赖 Gate 6-8 的工具在插件内可复用。

---

## 6. 与现有架构的关系

```
自研 Agent / dsh（入口，不变）
   └─ 引擎层（GisEngine/QgsEngine，新增操作类方法）
         ├─ 分析类：现有 20 工具（保留，继续扩展 run_algorithm 白名单）
         └─ 操作类：Gate 6-9 新增（编辑/图层/样式/工程/排版）
   └─ 审批层（危险操作 on_approve / ToolAnnotations destructive）
```

- 操作类工具同样走「schema + 引擎方法 + MCP handler + 测试」套路，Agent 与 MCP 双入口自动共享；
- 无头 worker 先实现全部操作逻辑（Gate 6-8），插件宿主（Gate 9）复用同一套引擎方法，只换"宿主"。

---

## 7. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-08-23 | 定位从「数据分析助手」升级为「GIS 智能操作助手」 | 只做数据分析不够"智能助手"；用户明确要求操作类能力 |
| 2 | 2026-08-23 | 重新纳入此前排除的 Editing/Layouts/图层管理，套危险操作审批 | 操作 GIS 系统需要这些能力；用审批机制控制风险 |
| 3 | 2026-08-23 | 先无头 worker 实现操作逻辑（Gate 6-8），插件宿主后置（Gate 9） | 复用现有引擎架构，插件宿主依赖操作能力成熟 |
