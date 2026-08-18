# gis智能助手— 多 Agent 应用开发平台

> **当前主线：GIS 智能操作平台** —— 用户用自然语言描述 GIS 操作需求，系统自动完成
> 任务解析 → 步骤规划 → GIS 脚本生成 → 沙箱执行 → 结果校验 → 成果导出。
> 一句话定位：**把「说人话 → 出图/出数据」变成一条多 Agent 流水线。**
>
> 执行文档：`docs/SPEC-GIS智能操作平台.md`（Phase 1 MVP）｜ 引擎选型与分阶段演进：`docs/GIS-引擎选型与分阶段演进.md`

---

# GIS 智能操作平台

## 流水线

```
用户需求 + 数据文件（CSV / GeoJSON / ZIP）
    ↓
┌─────────────┐   ┌──────────────┐   ┌───────────────┐
│  plan 任务规划 │ → │ design 技术方案 │ → │ codegen 脚本生成 │
│ 拆解/追问/给schema │   │ 坐标系/算子/出图  │   │ GeoPandas 完整脚本 │
└─────────────┘   └──────────────┘   └───────┬───────┘
                                             ↓
┌─────────────┐   ┌──────────────┐   ┌───────────────┐
│ export 成果包  │ ← │ checker 结果校验│ ← │ exec 沙箱执行    │
│ zip+操作说明    │   │ 三层核对/重写回环 │   │ AST 扫描→运行→收产物 │
└─────────────┘   └──────────────┘   └───────────────┘
```

- **plan**：拆解用户需求，信息不足时输出 `[ASK_USER]` 追问；`data_inspect` 预注入数据 schema（唯一注册的 LLM 工具，只读 + 路径白名单 + 10MB）；
- **design**：确定坐标系（缺失默认 EPSG:4326）、分析算子（分级设色/缓冲区/相交…）、出图方案与输出文件清单；
- **codegen**：生成完整可运行脚本（GeoPandas + matplotlib），必须自包含 import、只用当前目录相对路径、只用输入数据文件；
- **exec**：纯代码节点——快照源数据 → AST 静态扫描（禁 `os.remove` 等危险调用）→ 沙箱执行 → 收集产物；
- **checker**：三层校验（规则断言 → 脚本打印的 figure/CRS 信息 → 可选视觉模型 OCR），FAIL 且重写轮次 < 2 时回 codegen 自愈；
- **export**：打包成果 zip（PNG / GeoJSON / CSV + `操作说明.md` + `校验报告.md`），产物落在 `data/gis_exports/`。

## 快速开始（MVP 验收示例）

```bash
cd ai-dev-platform
pip install -e ".[dev]"
echo "DEEPSEEK_API_KEY=sk-..." >> .env    # 必须
python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8080 --reload
```

```bash
# 1. 上传示例数据（31 省 GDP 点数据）
curl -X POST http://localhost:8080/api/v1/gis/upload   -H "X-API-Key: $DEEPSEEK_API_KEY"   -F "file=@data/gis_demo/gdp_demo.csv"

# 2. 发起构建，返回 stage=done 即成功
curl -X POST http://localhost:8080/api/v1/gis/build   -H "X-API-Key: $DEEPSEEK_API_KEY"   -H "Content-Type: application/json"   -d '{"user_request":"把 gdp_demo.csv 按省份做分级设色图","data_file":"data/gis_uploads/<user>/gdp_demo.csv"}'
```

> 已通过真实 LLM 端到端冒烟：`gdp_demo.csv` → 分级设色图 `choropleth.png` + 分级统计 `summary.csv`，checker 逐项 PASS。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/gis/upload` | 上传数据文件（.csv / .geojson / .json / .zip，≤10MB） |
| POST | `/api/v1/gis/build` | 同步启动 GIS 流水线，返回阶段 / 校验报告 / 产物 |
| WS | `/ws`（`action=build_gis`） | 异步流水线 + 阶段进度推送 |

## 目录结构（GIS 相关）

```
src/
├── agents/gis_{plan,design,codegen,checker}.py   # 四个 LLM Agent（流水线）
├── gis_toolkit/
│   ├── agent.py        # GisToolAgent：工具调用版 GIS 助手（多轮对话）
│   ├── engine.py       # GisEngine：默认引擎（geopandas）+ create_gis_engine 工厂
│   ├── qgis_engine.py  # QgsEngine：QGIS 真实引擎（常驻 worker 子进程）
│   ├── qgis_worker.py  # QGIS worker：PyQGIS 执行 9 工具（QGIS 自带 Python 运行）
│   ├── schemas.py      # 工具定义（load_data/inspect_data/choropleth/overlay...）
│   └── session.py      # GisSessionStore：会话持久化
├── orchestrator/graph.py                          # create_gis_graph() 编排
├── orchestrator/state.py                          # GisProjectState
├── orchestrator/long_term_memory.py               # 长期记忆（SQLite）
├── sandbox/security.py + executor.py              # AST 静态扫描 + 沙箱执行
├── tools/implementations/data_inspect.py          # 流水线唯一 LLM 工具（只读+白名单+10MB）
├── prompt/templates/gis_*.md                      # Jinja2 prompt 模板
└── web/server.py                                  # /api/v1/gis/* + gis-assistant/* 路由
frontend/src/views/GisAssistant.vue                # 会话式前端（流式输出 + 会话管理）
tests/test_gis_*.py + test_qgis_engine.py         # 184 个用例（sandbox/state/agents/tools/toolkit/graph/api/qgis）
data/gis_demo/gdp_demo.csv                         # 验收示例数据
```
---


## QGIS 真实引擎（可选）

默认引擎为 geopandas 本地模拟；安装 QGIS 后可切换为真实 GIS 渲染引擎：

- **安装**：OSGeo4W QGIS 3.40 LTR（本机 `D:\QGIS`），PyQGIS 环境自动发现，可用 `QGIS_PREFIX_PATH` 覆盖；
- **切换**：`GIS_ENGINE=qgis` 启动后端，同一套 9 工具 schema / Agent / 前端零改动；
- **架构**：`QgsEngine`（主进程，安全校验/产物管理）→ 常驻 `qgis_worker` 子进程（QGIS Python，图层运算）→ JSON-lines 协议；
- **安全边界不变**：输入路径白名单、文件名净化、固定产物目录均留在主进程，QGIS 表达式/处理脚本不向 LLM 暴露；
- **验证**：`tests/test_qgis_engine.py` 13 个用例（含 overlay 与 geopandas 对照、引擎切换、白名单）。

## GIS 助手 API（工具调用版）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/gis-assistant/run` | 单轮工具调用对话（可带 session_id 续聊） |
| GET | `/api/v1/gis-assistant/run/stream` | SSE 流式输出（text_delta / tool_call / tool_result） |
| GET | `/api/v1/gis-assistant/sessions` | 会话列表 |
| GET | `/api/v1/gis-assistant/sessions/{id}` | 会话详情（续聊恢复） |
| DELETE | `/api/v1/gis-assistant/sessions/{id}` | 删除会话 |
| GET | `/api/v1/gis-assistant/files/{sid}/{file}` | 访问会话产物文件（png/csv/geojson） |

## License

MIT
