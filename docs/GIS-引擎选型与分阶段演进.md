# GIS 引擎选型与分阶段演进（配套文档）

> 配套文档：`docs/SPEC-GIS智能操作平台.md`（Phase 1 MVP 执行文档）。本文档回答三个问题：用什么 GIS 引擎/宿主、什么时候引入、工具描述对着哪份 API 写。
> 版本：v1.0 ｜ 日期：2026-08-17 ｜ 作者：胡贞虎

---

## 0. 一句话结论

- **Phase 1-2（MVP）**：引擎是 GeoPandas + matplotlib（Python 库），不需要任何 GIS 桌面软件；
- **Phase 3**：引入 QGIS（PyQGIS）作为宿主，「GIS 助手」从数据管道助手升级为「嵌在 GIS 里的操作助手」；
- **工具描述来源是 API 文档 + 实测验证，不是源码**；
- **架构骨架全程不变，只换引擎**：Agent 生成脚本 → 沙箱执行 → 校验 → 导出，各阶段同一套。

---

## 1. 核心认知：工具描述 = 引擎 API 的封装说明

工具描述的本质，是把「引擎能做什么」翻译成 LLM 可理解、可调用的声明。写准一份工具描述只需要三步：

1. 查官方 API 文档（例如 GeoPandas 的 `GeoDataFrame.plot` / `overlay` / `buffer`）；
2. 本地跑通最小用例，确认参数、坐标系行为、输出格式；
3. 把可复现的调用方式 + 约束写进 prompt / ToolDescription。

不需要读引擎源码；只有遇到文档没覆盖的边界行为时才按需查源码。例子：

- 「分级设色图」→ `gdf.plot(column=..., scheme="Quantiles", k=5)` + matplotlib legend；
- 「500 米缓冲区」→ `gdf.geometry.buffer(500)`（先确认坐标系单位是米还是度）；
- 「相交分析」→ `gpd.overlay(gdf1, gdf2, how="intersection")`。

**顺序是「先定引擎，再写工具描述」**：引擎选型决定 tool 描述、prompt 约束和 checker 断言，因此选型要前置。

---

## 2. 开源 GIS 三层模型（避免选错层级）

「开源 GIS 系统」至少是三种完全不同的东西，混用会白花集成成本：

| 层级 | 代表 | 语言栈 | 何时用 | 与 Agent 的关系 |
|---|---|---|---|---|
| 数据引擎层 | GeoPandas / PostGIS / GDAL | Python / SQL | Phase 1-2 | Agent 生成脚本直接调用，无界面 |
| 服务发布层 | GeoServer / MapServer | Java / C | 可选（成果发布） | 与 Python 栈跨语言，不做执行引擎 |
| 软件宿主层 | QGIS（PyQGIS 插件） | C++ / Python | Phase 3 | 「嵌入 GIS」的终局：面板 + 操作工程 |

> 一句话：MVP 的「GIS 助手」是**数据管道助手**（GeoPandas）；Phase 3 才升级为**嵌在 GIS 里的操作助手**（QGIS 插件）。

---

## 3. 候选系统评估

| 系统 | 类型 | 许可证 | 与 Agent 的集成方式 | 引入阶段 | 成本 / 风险 |
|---|---|---|---|---|---|
| GeoPandas | Python 库 | BSD | 脚本直接调用，无服务 | Phase 1 | 依赖简单（pip）；MVP 首选 |
| matplotlib | Python 库 | PSF | 出图脚本 | Phase 1 | 随 geopandas 一并安装 |
| seaborn | Python 库 | BSD | 柱状图 / 热力图 | Phase 2 | 轻量，可选 |
| PostGIS | PostgreSQL 扩展 | GPL | 只读连接做空间查询 | Phase 2 | 需 PG 实例；**只读权限**，不给沙箱写库 |
| QGIS / PyQGIS | 桌面 GIS | GPL | Phase 3 宿主：插件面板 + 工程状态注入 | Phase 3 | Windows 环境配置 + CI headless 成本高，提前验证 |
| GeoServer | Java 服务 | GPL | WMS/WFS 发布成果 | 可选 | 跨语言，仅发布场景，不做执行引擎 |
| MapLibre GL | 前端库 | MIT | 成果 Web 展示 | 可选 | 轻量，配前端 |
| GDAL/OGR | C/C++ 库 | MIT | 格式转换兜底 | 按需 | 通常随 geopandas 自带 |

---

## 4. 分阶段引入表（与 SPEC 第 9 节对齐）

| 阶段 | 引擎 | 新增工具 / 描述来源 | 后端开发增量 |
|---|---|---|---|
| Phase 1 MVP | GeoPandas + matplotlib | `data_inspect`（对 CSV/GeoJSON 读取 API）；沙箱 AST 扫描 | 主要是接线：State / 4 个 Agent / graph / server / 上传 |
| Phase 2 | + PostGIS 只读、seaborn | buffer / overlay / 空间连接算子；GeoPandas API | 算子工具 + 校验断言扩展 |
| Phase 3 | QGIS / PyQGIS | 工程状态注入、图层操作工具；PyQGIS API 文档 | 插件面板 + 状态注入 + 危险操作审批 + 回滚 |
| Phase 4 | + RAG 空间检索 | 空间范围过滤 / 矢量属性检索 | 跨项目链路（问答 → 出图） |

---

## 5. QGIS 宿主定位（Phase 3 前瞻）

- **为什么是 QGIS**：开源 GPL（无授权风险）；PyQGIS 是官方 Python 绑定，Agent 生成 PyQGIS 脚本与生成 GeoPandas 脚本是同一套打法；插件体系本身就是 Python；可 headless。
- **嵌入方式**：QGIS 插件面板 —— 输入自然语言 → 后台跑流水线 → 结果以图层 / 图加载进当前工程。
- **状态注入**：读取当前工程（.qgs）的图层列表、坐标系、选中要素 → 注入 PromptContext。
- **Headless 与 CI**：`qgis_process` / offscreen 模式可跑脚本验证，不依赖 GUI。
- **关键风险**：Windows 上 PyQGIS 环境配置较重、CI 无 GUI 场景需要专门适配；进入 Phase 3 前先花一周做环境验证（装 QGIS、跑通一个 PyQGIS 最小脚本）。

---

## 6. 架构演进原则

1. **骨架不变，只换引擎**：编排、沙箱、审批门、校验回环在四个阶段完全复用；
2. **引擎差异隔离**：通过 `data_inspect`、exec 节点等适配层隔离引擎差异，Agent 代码不直接耦合具体 GIS 引擎；
3. **先跑通最小用例，再写工具描述**：每个阶段先本地验证引擎能力，再落 prompt / ToolDescription（测试驱动）；
4. **能不加就不加**：PostGIS、GeoServer、MapLibre 都是按需引入，不作为默认依赖。

---

## 7. 决策记录

| # | 日期 | 决策 | 原因 |
|---|---|---|---|
| 1 | 2026-08-17 | MVP 不引入桌面 GIS，用 GeoPandas | 环境成本最低，MVP 目标是跑通「说人话→出图」 |
| 2 | 2026-08-17 | Phase 3 宿主选 QGIS | 开源 + PyQGIS 官方绑定 + 插件体系，贴合「GIS 软件智能操作」岗位 |
| 3 | 2026-08-17 | GeoServer 不做执行引擎 | Java 栈跨语言，只适合成果发布 |
| 4 | 2026-08-17 | PostGIS 只读连接 | 沙箱脚本绝不持有数据库写权限 |
| 5 | 2026-08-17 | 工具描述来源 = API 文档 + 实测 | 不需要读引擎源码，降低入门成本 |
