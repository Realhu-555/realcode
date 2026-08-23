# GIS 智能助手（工具调用版）设计文档

> 配套文档：`docs/SPEC-GIS智能操作平台.md`（Phase 1 MVP，脚本生成模式）｜ `docs/GIS-引擎选型与分阶段演进.md`（引擎选型）。
> 本文档定义一条**并列于 MVP 的演进路线**：把「LLM 生成脚本 → 沙箱执行」升级为「LLM 通过 function calling 直接操作 GIS 引擎」。
> 版本：v0.1（设计稿，待评审） ｜ 日期：2026-08-17 ｜ 作者：胡贞虎

---

## 1. 背景与定位

MVP（SPEC v1.2）已证明「说人话 → 出图/出数据」能跑通，但形态是**脚本生成**：LLM 产出一整段 GeoPandas 脚本，沙箱整段执行，checker 事后校验。这有三个结构性限制：

1. **没有可审计的操作序列**：脚本是一次性产物，「先读数据 → 再看字段 → 再决定怎么算」的中间决策不可见、不可干预；
2. **验证靠"结果对"反推**：checker 只能核对产物，无法确认 LLM 每一步的 GIS 操作是否有意义（能不能 buffer、overlay 参数选没选对）；
3. **离"GIS 系统助手"很远**：真正的助手是**操作**一个 GIS 系统（点按钮、跑算法），不是代写脚本。

**本文档的目标形态**：`GisToolAgent`（LLM 大脑）通过工具调用序列操作 `GIS 引擎`（手脚），每一步工具的调用参数与返回结果都成为可审计轨迹。这直接回答「怎么知道他会不会操作 GIS 工具」——**轨迹即证据**。

定位关系：

| 形态 | 引擎 | 交互方式 | 阶段 |
|---|---|---|---|
| 脚本生成（MVP） | GeoPandas | LLM 写脚本 → 沙箱执行 | Phase 1（已完成 ✅） |
| **工具调用（本文档）** | GeoPandas（可换 PyQGIS） | LLM 调工具 → 引擎执行 | Phase 2 候选 / 原型 |
| 嵌入 GIS 宿主 | QGIS（PyQGIS 插件） | 面板 + 工程状态注入 | Phase 3 |

---

## 2. 目标与非目标

### 目标
- 自然语言 → 工具调用序列 → 操作真实空间数据 → 产出 PNG / GeoJSON / CSV / 统计；
- 每个工具调用的 `(工具名, 参数, 返回摘要)` 全量落轨迹，可回放、可评测；
- 引擎抽象层：现在用 GeoPandas 实现，未来换 PyQGIS 实现时**工具接口不变**；
- 首批 9 个工具覆盖 MVP 验收同款任务（分级设色 / 统计 / 空间操作）。

### 非目标（本期不做）
- 不替代 QGIS 桌面 GUI，不做图层树 / undo-redo / 多窗口；
- 不做多 Agent 工作流编排（单 Agent 循环即可，LangGraph 编排留给 Phase 3）；
- 不做通用全部 GIS 算子（只做 9 个高频工具）；
- 不做前端对话界面（先 CLI / API 验证，前端后续）。

---

## 3. 总体架构

```
用户自然语言 + 数据文件
        ↓
┌──────────────────────────────────┐
│ GisToolAgent（LLM 大脑）            │ ← DeepSeek function calling
│  循环：思考 → 工具调用 → 观察结果      │   （复用 src/llm/provider.chat_with_tools）
└──────────────┬───────────────────┘
               │ OpenAI 格式工具调用
               ↓
┌──────────────────────────────────┐
│ GIS 引擎抽象层（接口契约）            │
│  ├─ GisEngine（协议：load_data /   │
│  │    buffer / overlay / choropleth│
│  │    / summarize / export ...）   │
│  ├─ GeoPandasEngine（本期实现）      │
│  └─ PyQGISEngine（Phase 3 实现）    │
└──────────────┬───────────────────┘
               ↓
        数据文件 / 产物目录
        （PNG / GeoJSON / CSV）
```

关键点：
- **引擎只暴露函数式工具，不暴露内部对象**：LLM 永远拿不到 GeoDataFrame 本身，只拿到 JSON 摘要（行数 / 字段 / CRS / 范围 / 样例行）；
- **工具描述 = 引擎 API 的封装说明**（遵循配套文档「先定引擎，再写工具描述」）：每个工具的参数、约束、返回都对着 GeoPandas API 写，实测跑通后才定稿；
- **未来换引擎零成本**：工具名与参数不变，只换实现类（GeoPandas → PyQGIS），LLM 无感。

---

## 4. 工具集设计（首批 9 个）

### 4.1 清单

| 工具 | 参数 | 返回摘要 | GeoPandas 实现（本期） | 未来 QGIS 对应 |
|---|---|---|---|---|
| `load_data` | `path` | 行数/字段/CRS | `read_file` / CSV+`points_from_xy` | `QgsVectorLayer` + `addMapLayer` |
| `inspect_data` | （无） | 字段/行数/CRS/范围/样例行 | `gdf.head()` + `total_bounds` | 图层属性表读取 |
| `buffer` | `distance` | 新图层摘要 | `gdf.geometry.buffer(d)` | `QgsGeometry.buffer` |
| `overlay` | `other_path, how` | 新图层摘要 | `gpd.overlay(how=...)` | `QgsGeometry.intersection/union` |
| `choropleth` | `column, scheme, k, output` | PNG 路径/大小 | `gdf.plot(column=, scheme=, k=)` | `QgsCategorizedSymbology` + 导出图片 |
| `scatter_plot` | `x, y, output` | PNG 路径/大小 | `matplotlib scatter` | `QgsPlot`（若有） |
| `summarize` | `column, groupby, agg, output` | CSV 行数 | `groupby + agg → to_csv` | `QgsVectorLayer` 统计 |
| `export_geojson` | `output` | 文件路径/大小 | `gdf.to_file(driver="GeoJSON")` | `QgsVectorFileWriter` |
| `finish` | `outputs, summary` | 完成声明 | — | — |

### 4.2 工具描述原则（写进 schema 的硬规则）
- **名称动词化**，一眼可懂：`load_data` / `buffer` / `choropleth`；
- **参数必须带 type + description**，枚举类参数写明合法值（如 `how ∈ {intersection, union, difference, symmetric_difference}`、`agg ∈ {sum, mean, count, min, max}`、`scheme ∈ {NaturalBreaks, Quantiles, EqualInterval}`）；
- **每个工具必须声明副作用**：写不写文件、写到哪（引擎输出目录）、返回什么；
- **禁止 LLM 臆造路径**：输入文件路径只能来自 `load_data` 的返回值或用户给定；产物一律相对文件名，由引擎写入输出目录。

### 4.3 返回协议（所有工具统一）
```json
{
  "status": "ok",            // 或 "error" / "finished"
  "message": "人类可读的结果说明",
  "layer": {"rows": 31, "columns": ["province", "gdp", "lon", "lat"], "crs": "EPSG:4326", "geometry_type": "Point"},
  "outputs": ["choropleth.png"],
  "...": "工具特有字段（size_bytes / summary_rows 等）"
}
```
- 摘要控制在几百字节内，避免撑爆上下文；
- 错误返回 `{"status": "error", "error": "..."}`，LLM 依据错误信息自行修正后重试（工具级自愈，不需要 checker 回环）。

---

## 5. 会话与状态模型

- **单会话单图层**：引擎持有「当前图层」（GeoDataFrame）+ 产物清单 + 输出目录；工具默认作用于当前图层，`overlay` 会加载第二图层后把结果设为当前图层；
- **隐式状态，显式摘要**：LLM 看不到图层对象，只能通过 `inspect_data` 的返回了解当前状态——这强制 LLM 先查看再决策，轨迹因此更可读；
- **输出目录**：默认 `data/gis_toolkit_out/`，按会话建子目录，产物不污染仓库（建议进 `.gitignore`）；
- 状态保存在引擎实例内，Agent 单次 `run()` 用完即弃，不做跨会话持久化（本期）。

---

## 6. 执行循环协议

复用 `LLMProvider.chat_with_tools`（原生 function calling，返回 `{content, tool_calls}`）。

```
messages = [system, user]
repeat up to MAX_STEPS(12):
    resp = chat_with_tools(messages, TOOL_SCHEMAS)
    if resp.tool_calls:
        messages += assistant(tool_calls)
        for each tool_call:
            result = engine.execute(name, args)   # 异常 → {"status":"error"}
            trajectory += {step, tool, args, result}
            messages += tool(tool_call_id, json(result))
        if any result.status == "finished":
            return 完成
    else:
        return 结束（把 resp.content 作为最终答复）
return 达到步数上限（轨迹保留，标记超限）
```

硬性约束：
- **步数上限 12**，防死循环烧 token；
- **工具异常不回滚**：`buffer` 失败后当前图层保持不变，LLM 拿到 error 后重新决策；
- **`finish` 是唯一终止工具**：LLM 必须先完成所有产物，再调用 `finish(outputs=[...], summary="...")` 声明产出；引擎会核对声明文件是否真实存在，防 LLM 谎报；
- 无工具调用但内容非空：视为自然语言收尾，直接返回（保留轨迹）。

---

## 7. 安全与沙箱

脚本模式靠 AST 静态扫描，工具模式不产生脚本，安全防线移到**引擎层**：

| 防线 | 做法 |
|---|---|
| 输入白名单 | `load_data`/`overlay` 只允许 `data/` 下文件（沿用 `data_inspect` 的 10MB 限制与路径校验） |
| 输出隔离 | 引擎只写自己的输出目录，工具参数里的 `output` 做文件名净化（拒绝 `../`、绝对路径） |
| 参数校验 | 枚举参数（how/agg/scheme）在引擎层二次校验，不信任 LLM 参数 |
| 只读输入 | 引擎不修改任何输入文件，无 `open(w)` 类能力 |
| 超时 | 单次 `run()` 整体超时（如 180s），防止单工具卡死 |

> 未来接 PyQGIS 时，引擎在独立进程跑（QGIS 库与主进程隔离），进一步降低崩溃影响。

---

## 8. 验证与评测（怎么知道他会不会操作 GIS 工具）

这是本文档的核心关切，分四级，从弱到硬：

| 级别 | 手段 | 回答的问题 |
|---|---|---|
| 1 工具轨迹审计 | 每个 step 的 `(tool, args, result)` 落盘 JSON | 「他调了哪些工具、参数是什么」——可人工回放 |
| 2 产物规则校验 | PNG 存在且 >20KB + PIL 尺寸/非常色；CSV 行数与数值区间断言 | 「产物真的存在且合理」 |
| 3 基准任务集 | 8~10 个典型任务，每个带标准答案（预期行数/统计值/字段名），跑批对比 | 「面对新任务，操作质量稳定吗」 |
| 4 真实 LLM 冒烟 | gdp_demo.csv 等固定数据端到端跑通 | 「当前模型/配置能跑通整条链路」 |

关键设计：**轨迹（级别 1）是评价主证据**——即使产物没全过，轨迹也能区分「模型不会用工具」（乱调参/不会 finish）与「模型会但结果偏差」（参数合理、产物差一点）。

评测输出示例：
```json
{
  "task": "gdp_choropleth",
  "trajectory": [{"step":1,"tool":"load_data","args":{"path":"gdp_demo.csv"},"result":"..."}],
  "pass": true,
  "checks": {"png_exists": true, "png_size": 89421, "outputs_declared_match": true}
}
```

---

## 9. 与现有 MVP 的关系（复用清单）

| 现有资产 | 复用方式 |
|---|---|
| `src/llm/provider.py::chat_with_tools` | 直接复用（function calling 已实现） |
| 模型路由 / failover（`config/models.yaml`） | 新增 `gis_assistant` agent 类型，路由到 deepseek-v4-pro |
| `data_inspect` 的路径白名单 / 10MB 限制 | 移植为引擎层输入校验 |
| `src/utils/trace.py::TraceTracker` | 记录工具调用轨迹（与级别 1 对齐） |
| `data/gis_demo/gdp_demo.csv` | 验收示例数据 |
| 测试基建（pytest + monkeypatch fake LLM） | 沿用 |

不冲突：脚本模式（Phase 1）保持不动，工具模式作为独立原型并行验证；若评测通过，再决定是否在 SPEC 里追加为 Phase 2 正式任务。

---

## 9.1 测试数据清单（2026-08-23 扩充）

完整清单见 [`data/README.md`](../data/README.md)。本次扩充内容：

- **行政区划边界**（DataV.GeoAtlas）：全国/北京/上海/重庆/港澳 区县级、粤/川/浙/苏/豫/鲁/鄂/陕 市级、广州/成都 区县级；
- **派生点图层**：全国省会、广东/四川/浙江市级、北京区级驻地点（buffer / voronoi / 空间连接 / 散点图）；
- **统计面图层**：`*_stats.geojson`（含 `gdp_2023` / `pop_2023`，可直接面分级设色）；
- **演示 CSV**：`china_population.csv`（省级人口/GDP）、`poi_demo.csv`（合成 POI，40 行）；
- **线 / 栅格**：`major_rivers.geojson`（示意水系）、`dem_demo.tif`（演示 DEM，`load_raster` 用）；
- **修复**：`gis_bench_data/cities.geojson` 城市名乱码（北京/上海/广州）。

下载与生成命令：

```bash
python scripts/download_test_data.py                     # 拉取 DataV 边界
venv\Scripts\python.exe scripts\generate_test_data.py    # 生成派生数据
```

---

## 10. 里程碑（Task 拆分，完成后在本文档标记 ✅）

- [ ] **Task A 引擎层**：`src/gis_toolkit/engine.py` —— GeoPandas 实现 9 个工具 + 输出目录/文件名净化 + 单测（fake 数据）；
- [x] **Task B 工具 schema + Agent**：`src/gis_toolkit/schemas.py`（9 个 OpenAI 工具描述）+ `src/gis_toolkit/agent.py`（循环协议）+ 模型路由注册 `gis_assistant`（7 个循环测试全绿）；
- [x] **Task C CLI 演示 + 真实冒烟**：`python -m src.gis_toolkit.demo`，gdp_demo.csv 分级设色端到端跑通（真实 DeepSeek 工具调用 4 步：load→inspect→choropleth+summarize→finish），轨迹落盘 `data/gis_traces/`；
- [x] **Task D 基准任务集**：`src/gis_toolkit/bench.py` 首批 4 个任务（choropleth / summarize / buffer / scatter）+ 规则校验，真实 LLM 跑批 **4/4 通过**（报告落 `data/gis_bench_results/`）；
- [x] **Task E 接入 API（可选）**：`POST /api/v1/gis-assistant/run` + WebSocket `action=build_gis_assistant`，复用现有 server 基建（4 个 API 测试全绿 + 真实 LLM 冒烟 PASS）。

---

## 11. 开放问题（评审时确认）

1. **引擎选型**：本期就用 GeoPandas，还是直接上 PyQGIS？（建议 GeoPandas 先行——环境已验证可用，QGIS 装机成本高；接口抽象后切换成本低）
2. **工具粒度**：9 个够不够？是否需要 `crs_transform`（坐标系变换）作为第 10 个高频工具？
3. **图层管理**：单图层够用吗，还是需要 `list_layers` / `switch_layer`（多图层会话）？
4. **轨迹落盘位置**：`data/gis_traces/` 还是进 `TraceTracker` 现有存储？
5. **是否进 SPEC**：原型验证通过后，把工具模式追加为 SPEC Phase 2 正式任务，还是保持独立？

---

## 12. 一句话总结

**工具调用版 GIS 助手 = 把「生成脚本」换成「操作引擎」**：LLM 通过 9 个工具操作 GeoPandas（未来 PyQGIS），每一步调用都留轨迹，用轨迹 + 产物 + 基准任务集证明「他真的会操作 GIS 工具」。
