# GIS 真实引擎接入方案（Phase 3 实施）

> 配套文档：`docs/SPEC-GIS智能操作平台.md`（Phase 1 MVP）｜`docs/GIS-引擎选型与分阶段演进.md`（选型结论）｜`docs/GIS-智能助手-工具调用设计.md`（9 个工具定义）
> 本文档回答一个问题：demo 已验证、内容生成模块已删除之后，**如何把「伪引擎（geopandas 本地模拟）」替换成「真实开源 GIS 系统」**，以及**是否需要去 GitHub 找开源系统**。
> 版本：v0.4（Gate 1/2/3 已完成；Gate 4 规划中）｜日期：2026-08-18 ｜作者：胡贞虎

---

## 0. 一句话结论

- **不需要去 GitHub 漫无目的地找开源 GIS 系统**：开源 GIS 主流就「三层四家」（见第 2 节），选型已在配套文档定案——Phase 3 宿主 = **QGIS**；
- **写工具描述需要的是官方 API 文档 + 本地实测，不是源码**；只有遇到 API 文档没覆盖的边界行为（如空几何、多部件、CRS 单位）才按需查源码；
- **接入方式 = 新增一个 `QgsEngine` 实现现有引擎接口**：Agent、9 个工具 schema、前端对话界面全部不动，只换「手脚」。

---

## 1. 现状盘点（demo 已验证的能力）

当前 `src/gis_toolkit/` 是一条完整的「工具调用版」链路：

```
GisToolAgent（LLM 大脑，function calling 循环）
   ↓ OpenAI 格式工具调用
GisEngine（geopandas 手脚，单会话：当前图层 + 产物清单 + 输出目录）
   ↓
产物文件（PNG / CSV / GeoJSON）→ /api/v1/gis-assistant/files/{sid}/{file}
```

- **9 个工具**：`load_data`、`inspect_data`、`buffer`、`overlay`、`choropleth`、`scatter_plot`、`summarize`、`export_geojson`、`finish`；
- **引擎接口契约**：每个工具只返回 JSON 摘要（行数/字段/CRS/范围/样例行），LLM 永远拿不到 `GeoDataFrame` 内部对象；产物一律写引擎输出目录，文件名净化；
- **安全边界**：输入路径白名单（默认 `data/` 根）、产物文件名 `[\w.\-]+`、上传 ≤10MB、只读输入；
- **前端**：`GisAssistant.vue` 会话式界面，SSE 流式输出（text_delta / tool_call / tool_result 按序排版）+ 会话管理 + 产物卡片。

这套骨架是「引擎无关」的：`TOOL_SCHEMAS` 的注释已写明「引擎换 PyQGIS 时 schema 不变」。

---

## 2. 要不要去 GitHub 找开源 GIS 系统？——不需要

### 2.1 开源 GIS 主流是可数的「三层四家」

| 层级 | 系统 | 许可 | 在我们架构里的角色 | 结论 |
|---|---|---|---|---|
| 数据引擎层 | GeoPandas / PostGIS / GDAL | BSD / GPL / MIT | 当前引擎（geopandas），或只读数据源 | 已在使用，无需「找」 |
| 服务发布层 | GeoServer / MapServer | GPL / MIT | 成果发布（WMS/WFS），**不做执行引擎** | 可选，非必须 |
| 软件宿主层 | **QGIS（PyQGIS + QGIS Server）** | GPL v2+ | Phase 3 目标宿主：引擎实现 + 插件面板 | **唯一需要引入的** |
| 前端展示层 | MapLibre GL / OpenLayers / Leaflet | MIT / BSD | 成果 Web 预览 | 可选，按需 |

不存在「淘到一个更好的开源 GIS」的问题——选型就是在这几家之间做减法，结论已定：**宿主选 QGIS**（理由见配套选型文档第 5 节）。

### 2.2 写工具描述不需要源码

一个工具描述（`load_data` / `buffer` / `choropleth`…）的产出步骤：

1. 查官方 API 文档——QGIS 有完整的 Python API 文档（`docs.qgis.org` / PyQGIS Cookbook）；
2. 本地跑通最小用例，确认参数、CRS 行为、输出格式；
3. 把可复现的调用方式 + 约束写进 `TOOL_SCHEMAS`。

只有在第 2 步遇到「文档没写清边界行为」（如某算子对空几何/多部件/None 值的处理）时，才去查 `qgis/QGIS` 源码。

> 如果你仍想收藏官方仓库（仅作参考，不是前置条件）：
> - QGIS：`github.com/qgis/QGIS`（核心源码，C++ + Python 绑定）
> - QGIS Server / Docker 镜像：`qgis/qgis-server`（Docker Hub）
> - GeoServer：`github.com/geoserver/geoserver`

---

## 3. 目标形态：两条接入路径（先 A 后 B）

### 路径 A：QGIS Server / `qgis_process`（无头服务，**推荐先做**）

- 用 **QGIS Server（Docker 镜像 `qgis/qgis-server`）** 或 **`qgis_process` 命令行**跑算法，FastAPI 后端通过子进程/REST 调用；
- 优点：headless、可 Docker 化、与当前「HTTP 请求 + 文件产物」形态最像，**Windows 环境成本最低**（容器内跑 QGIS，宿主只需 Python 客户端）；
- 缺点：QGIS 官方对 Windows 上的 QGIS Server 支持较弱（推荐 Linux/Docker）。

### 路径 B：PyQGIS 插件（嵌入 QGIS 桌面，宿主形态）

- 插件面板承载对话 UI，操作直接作用于**当前工程**（图层树、选中要素、CRS 状态注入 prompt）；
- 优点：真正的「GIS 系统里的智能助手」体验；
- 缺点：Windows GUI 环境 + CI 无头配置成本高，需专门适配。

**建议**：先做路径 A 打通「真实引擎能力」（Gate 2 验收对象），路径 B 留作 Phase 4 宿主嵌入。两条路径共用同一个 `QgsEngine` 实现，差异只在「谁来创建/持有 QgsApplication」。

---

## 4. 引擎实现：`QgsEngine`（同接口，换实现）

### 4.1 接口不变

```python
class QgsEngine:                      # 与 GisEngine 同名方法、同返回协议
    def __init__(self, data_file=None, out_dir="data/gis_toolkit_out", allowed_roots=None): ...
    def load_data(self, path: str) -> dict: ...
    def inspect_data(self) -> dict: ...
    def buffer(self, distance: float) -> dict: ...
    def overlay(self, other_path: str, how: str = "intersection") -> dict: ...
    def choropleth(self, column, scheme, k, output) -> dict: ...
    def scatter_plot(self, x, y, output) -> dict: ...
    def summarize(self, column, groupby, agg, output) -> dict: ...
    def export_geojson(self, output) -> dict: ...
    def finish(self, outputs, summary) -> dict: ...
```

内部状态：`QgsApplication`（offscreen 模式）→ `QgsVectorLayer`（当前图层）→ `QgsProject`（可选，仅宿主形态用）；产物仍写引擎输出目录，返回协议不变。

### 4.2 工具映射表（9 个工具 → PyQGIS API）

| 工具 | 现状（geopandas） | PyQGIS API | 差异 / 注意事项 |
|---|---|---|---|
| `load_data` | `gpd.read_file` / CSV+`points_from_xy` | `QgsVectorLayer(path, name, "ogr")`；CSV 用 `"delimitedtext"` provider | CSV 经纬度列 → `points_from_xy` 等价物：`QgsGeometry.fromPointXY`；CRS 用 `layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))` |
| `inspect_data` | `gdf.head()` + `total_bounds` | `layer.fields()` + `layer.featureCount()` + `layer.extent()` | 字段类型、范围、样例行需自行遍历 feature |
| `buffer` | `gdf.geometry.buffer(d)` | `QgsGeometry.buffer(distance, segments)` | 距离单位随 CRS（度/米），与现状一致；写回需 `QgsVectorLayerEditBuffer` |
| `overlay` | `gpd.overlay(how=...)` | `QgsGeometry.intersection/union/difference` 或 `QgsOverlayUtils` | `how ∈ {intersection, union, difference, symmetric_difference}` 保持 schema 不变 |
| `choropleth` | `gdf.plot(column=, scheme=, k=)` | `QgsCategorizedSymbologyRenderer` / `QgsGraduatedSymbolRenderer` + 导出 PNG | 分级方法（NaturalBreaks/Quantiles/EqualInterval）需对照 QGIS 内置分类器实现，**这是差异最大的工具，需实测校准** |
| `scatter_plot` | matplotlib scatter | matplotlib（PyQGIS 环境下仍可用）或 `QgsPlot` | 保持 matplotlib 即可，不引入新差异 |
| `summarize` | `groupby + agg → to_csv` | `QgsVectorLayer` 字段统计 / `QgsAggregateCalculator` | agg 枚举不变，输出 CSV 用 pandas 写 |
| `export_geojson` | `gdf.to_file(driver="GeoJSON")` | `QgsVectorFileWriter.writeAsVectorFormatV3(..., "GeoJSON")` | 需注意 writer 版本 API 差异 |
| `finish` | 声明完成 | — | — |

### 3.3 实际落地：OSGeo4W 常驻 worker（Gate 1/2 采用）

本机部署走「OSGeo4W + 常驻 worker 子进程」，介于路径 A/B 之间：

- **主进程**（项目 venv，零 QGIS 依赖）：`src/gis_toolkit/qgis_engine.py` 的 `QgsEngine`——安全校验（路径白名单/文件名净化/产物目录）、worker 进程生命周期、9 工具同接口；
- **worker 子进程**（QGIS 自带 Python 运行 `qgis_worker.py`）：持有当前 `QgsVectorLayer`，执行 9 工具（CSV→delimitedtext、buffer/overlay 用 native 算法、choropleth 用 `QgsGraduatedSymbolRenderer` + PIL 图例拼接、导出 `QgsVectorFileWriter`）；
- **协议**：stdin/stdout JSON-lines，`{"op":"call","tool":...,"args":...}` ↔ `{"ok":true,"result":...}`；QGIS 渲染线程崩溃问题已通过保留 `QgsApplication` 引用解决；
- **切换**：`GIS_ENGINE=qgis` 环境变量（`create_gis_engine` 工厂），Agent/schema/前端零改动；
- **已知差异**：choropleth 分级边界以 QGIS 分类器为准（Jenks/Quantile/EqualInterval 与 mapclassify 略有出入）；buffer 输出统一为 MultiPolygon。

### 3.4 Gate 3 冒烟验收（2026-08-18 通过）

同一句自然语言（加载 `gdp_demo.csv` → 按省份分级设色图 → 按省份汇总 → 导出 GeoJSON）在两种引擎下真实 LLM 走通：

| 项 | geopandas 引擎 | qgis 引擎 |
|---|---|---|
| 轨迹 | load_data → inspect_data → 三工具并行 → finish（3 步） | 同（4 步） |
| 产物 | choropleth.png / summary.csv / points.geojson | 同 |
| summary 数值 | GDP 总和 1250931.7 | 与 geopandas 完全一致 |
| choropleth | 省面聚合（3 省无数据） | 省界聚合，NaturalBreaks 5 级，含图例 |

### 4.3 会话状态与底图

- 当前图层 = 引擎持有的单个 `QgsVectorLayer` 引用；`load_data` 后替换；
- 底图：`data/gis_base/china_province.geojson` → `QgsVectorLayer`，分级样式复用 `choropleth` 同一套渲染器；
- `allowed_roots` / 文件名净化 / 产物目录逻辑原样复用（与引擎无关）。

---

## 5. 环境与依赖（Windows 现状）

| 方案 | 安装方式 | 适用 |
|---|---|---|
| A. Docker（**推荐**） | `docker pull qgis/qgis-server`，容器内提供 `qgis_process`；宿主 Python 通过 subprocess/REST 调用 | 路径 A，成本最低 |
| B. OSGeo4W 本机安装 | 安装 QGIS LTR（含 PyQGIS），需配置 `PYTHONPATH` 指向 QGIS Python 目录 | 路径 B / 本机调试 |
| C. conda-forge | `conda install -c conda-forge qgis` | 备选，版本较新 |

> **本机现状（2026-08-18）**：Docker 拉取 `qgis/qgis-server` 超时（国外大流量源网络问题），已改走 **OSGeo4W 本机安装**——阿里云镜像下载 `QGIS-OSGeo4W-3.40.10-1.msi`（1.3GB），提权静默安装到 `D:\QGIS`（C 盘空间不足）；源码浅克隆 `final-3_40_10` 到 `D:\qgis-src` 作 API 参考。

> **Gate 1 验收**：跑通一个最小 PyQGIS 脚本——读 `china_province.geojson` → 出 PNG + GeoJSON，输出与 geopandas 引擎结果一致。

---

## 6. 安全边界（保持与 MVP 一致，只增不减）

1. **工具白名单**：只暴露 9 个工具，**不暴露任意 Python 表达式 / QGIS 处理脚本执行**（QGIS 表达式引擎有脚本能力，绝不能透传给 LLM）；
2. **输入路径白名单**：只允许 `data/` 根下文件，禁止任意路径读取；
3. **产物文件名净化 + 固定输出目录**：沿用 `_sanitize_filename`；
4. **危险操作审批**：覆盖写、删除、网络请求等操作需用户确认（Phase 4 加）；
5. **Checker 校验**：产物 PNG 尺寸 / CSV 行数 / CRS 与任务要求一致，FAIL 自动回环；
6. **许可合规**：QGIS 是 GPL v2+——内部部署无问题；**商业闭源分发**要避免把 QGIS 作为进程内库，优先走 QGIS Server（HTTP 服务方式交互）或 GeoServer。

---

## 7. 上下文治理与记忆系统设计（单 Agent 长链）

> 本节回答：ESRI ArcGIS AI 助手案例（收集→报告→热力图→汇总→预测→扩展分析）这类**链式任务**如何避免上下文爆炸，是否需要拆多 Agent。
> 结论：**单 Agent + 上下文治理**，不拆多 Agent。

### 7.1 为什么单 Agent 而不是多 Agent

- 多 Agent 解决的是**上下文隔离**（子任务上下文彼此独立、需并行、权限不同），不是**上下文爆炸**；
- 链式任务状态强耦合（每步消费上一步产物），拆开反而增加「任务描述 + 结果回传」的 token 开销，编排与错误排查更复杂；
- 拆多 Agent 的时机（当前不满足）：子任务上下文独立且大、需要并行、有独立工具集/权限边界。届时用 LangGraph supervisor 模式，Agent 之间也只传**产物句柄**，不传数据。

### 7.2 上下文爆炸的三个来源与对策

| 来源 | 对策 | 现状 |
|---|---|---|
| 工具结果直接进对话 | 结果落盘（PNG/CSV/GeoJSON），对话只传文件名 + JSON 摘要 | 已实现 |
| 中间状态在文本里传 | 状态外置到引擎图层/数据集句柄（`layer:xxx`） | 已实现 |
| 历史消息无限累积 | 分层记忆 + token 阈值主动压缩（见 7.3 / 7.4） | **本次新增** |

### 7.3 记忆分层设计

| 层 | 内容 | 存储 |
|---|---|---|
| 工作记忆 | 当前任务工具结果、图层句柄、产物引用 | 引擎状态对象（不进对话） |
| 会话记忆（episodic） | 每轮问答摘要 + 关键产物引用 | 向量库 |
| 语义记忆（semantic） | 用户偏好、项目画像 | SQLite 结构化（已有 `user_preferences` 表） |
| 程序性记忆 | GIS 经验教训（踩坑、成功模式） | SQLite `lessons` 表 + 向量召回 |

**现状对照**：`session.py` 是 40 条硬截断到 30 条（粗暴丢弃，无摘要）；`long_term_memory.py` 是 SQLite 存项目/教训/偏好，**无向量检索**。本次设计补齐这两块。

### 7.4 主动压缩策略（阈值触发，不等到爆）

1. **触发条件**：按 token 数计数（每轮从 LLM 响应的 `usage` 累加），阈值 = 模型 context 上限的 **60~70%**（如 128k 模型在 ~80k 触发），留足余量；
2. **滚动摘要**：`新摘要 = LLM(旧摘要 + 本轮事件)`，不重写全部历史，成本低、不丢「已发生过什么」；
3. **保留最近 N 轮原文**（如 5 轮），更早的压成摘要——用户可能刚问完「刚才那张图数据源」，需要原文可查；
4. **摘要必须保留产物引用**（文件名、图层句柄、统计数字），细节永远从文件/状态对象恢复，摘要丢细节也不怕；
5. 压缩后注入结构：`[滚动摘要] + [最近 N 轮原文] + [当前引擎状态]`。

### 7.5 长期记忆：向量化存取

- **存**：每轮结束 → 轮次摘要 + 产物引用 + 时间戳 + session_id 作为一条 chunk，embedding 后入库；
- **取**：新请求 → top-k 语义检索（k=3~5），命中结果 + 滚动摘要 + 最近原文一起注入 system prompt；
- **相关性阈值**：低于阈值不注入，避免无关记忆污染（记忆污染比没记忆更糟）；
- **选型**：`sqlite-vec`（零部署、单文件）或 ChromaDB 持久化模式，**不引重型服务**；量级上来再迁 LanceDB/Milvus，存取接口先抽象。

### 7.6 落地顺序（Gate 4）

1. 短期记忆升级：token 计数 + 滚动摘要 + 保留最近 N 轮原文（收益最大，先做）；
2. 轮次摘要写入向量库 + 请求时检索注入；
3. 结构化记忆（偏好/教训）接向量补充召回。

### 7.7 参考案例：ESRI ArcGIS AI 助手（2024）

- 来源：[CSDN《宣布推出适用于 ArcGIS 的 AI 助手》](https://blog.csdn.net/qq_39397927/article/details/143357732)（ESRI 分享会摘要）；
- 典型链式工作流：获取数据 → 发布服务 → 添加元数据 → 地图/图层中使用 → 加入应用程序；风暴数据分析链：收集数据 → 查看报告 → 热力图 → 汇总 → 预测 → 趋势图 → 供应链影响扩展分析；
- 可借鉴点：**回答链接回源数据、生成地图与地理编码位置**（数据溯源）；**链式任务逐步派生产物**（与我们工具链一致）。

---

## 8. 开发排期（4 个 Gate，每 Gate 有明确验收）


| Gate | 内容 | 工期 | 验收标准 |
|---|---|---|---|
| **Gate 1** ✅ 2026-08-18 | 环境验证：Docker `qgis/qgis-server` 或 OSGeo4W 装 QGIS；跑通最小 PyQGIS 脚本 | 0.5 周 | `china_province.geojson` → PNG + GeoJSON 与 geopandas 输出一致 |
| **Gate 2** ✅ 2026-08-18 | 实现 `QgsEngine`（9 个工具）+ 单元测试 | 1–1.5 周 | 同一批用例在 `GisEngine` / `QgsEngine` 下产物与摘要 diff 通过（choropleth 分级校准在内） |
| **Gate 3** ✅ 2026-08-18 | 后端引擎可切换：`GIS_ENGINE=geopandas|qgis` 环境变量，会话级选择；前端不动 | 0.5–1 周 | 冒烟：同一句自然语言在两种引擎下走通，产物可下载 |
| **Gate 4** 规划中 | 上下文治理与记忆系统：token 阈值滚动摘要压缩 + 轮次摘要入向量库 + 检索注入 | 1 周 | 长链 10+ 轮对话不爆上下文；跨会话能召回用户偏好与历史任务产物引用 |
| **Gate 4** 规划中 | 上下文治理与记忆系统：token 阈值滚动摘要压缩 + 轮次摘要入向量库 + 检索注入 | 1 周 | 长链 10+ 轮对话不爆上下文；跨会话能召回用户偏好与历史任务产物引用 |

**总工期约 3–4 周**。Phase 4（可选）：QGIS 插件面板嵌入、危险操作审批、RAG 空间检索。

---

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| Windows 上 PyQGIS 环境配置复杂 | 优先 Docker（qgis/qgis-server），本机只留客户端 |
| `choropleth` 分级方法与 QGIS 内置分类器行为不同 | Gate 2 专门做分级校准用例，按 QGIS 输出为准 |
| QGIS 引擎行为差异（CRS 单位、字段名、空几何） | 每个工具写「实测用例」记录边界，schema 描述同步校准 |
| LLM 幻觉工具参数 | schema 枚举硬校验（how/agg/scheme）+ checker 回环 |
| GPL 许可传染 | 内部部署 OK；商业化走 QGIS Server 服务化隔离 |
| 摘要压缩丢细节（坐标/字段/文件） | 摘要强制保留产物引用，细节从文件/状态对象恢复，不依赖摘要 |
| 向量检索召回无关记忆 | top-k + 相关性阈值过滤，低于阈值不注入 system prompt |

---

## 10. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-08-18 | 不引入新开源系统，宿主定 QGIS | 主流可数，选型文档已定案；工具描述来自 API 文档+实测，无需源码 |
| 2 | 2026-08-18 | 先做 QGIS Server / `qgis_process`（路径 A），后做插件面板（路径 B） | headless、可 Docker、与现有「HTTP+文件产物」形态一致，Windows 成本最低 |
| 3 | 2026-08-18 | 接入方式 = 新增 `QgsEngine` 实现同一接口 | Agent / schema / 前端零改动，可平滑回退 geopandas 引擎 |
| 4 | 2026-08-18 | 不向 LLM 暴露 QGIS 表达式/处理脚本执行 | 表达式引擎有脚本能力，保持工具白名单安全边界 |
| 5 | 2026-08-18 | 单 Agent + 上下文治理，不拆多 Agent | 链式任务状态强耦合；多 Agent 解决隔离不解决爆炸，且编排与 token 成本更高；长链用「结果外置 + 状态句柄 + 分层记忆 + 阈值压缩」 |
