# GIS 智能助手 — Settings 设置模块设计文档（Marvis 交接）

> 用途：实现方（Marvis）按本文档开发设置模块；完成后由 Codex 按第 9 节逐项审计验收。
> 版本：v0.1（设计稿）｜ 日期：2026-08-25 ｜ 工作目录：`H:\ai-dev-platform`（分支 `feat/gis-mcp-server`）
> 需求来源：用户提出「做一个 Setting 模块，可在里面配置模型、主题等，并支持更多模型（含本地部署的 Ollama）」

---

## 1. 目标与范围

**一句话**：新增前端「设置」入口 + 后端用户设置/模型管理 API，让用户在 UI 上完成：
1. **模型**：选择默认模型；新增/删除自定义模型；测试模型连通性；支持 OpenAI 兼容供应商与本地 Ollama；
2. **外观**：明暗主题切换（复用现有 `useTheme`）；
3. **偏好**：默认权限模式（readonly/auto/ask）等会话默认值。

**本期不做（非目标）**
- 不做多用户权限体系/登录（沿用现有 `X-API-Key` + `user_id` 维度）；
- 不做模型负载均衡、动态 failover 策略编辑（沿用注册表 failover 链）；
- 不做「系统级」模型编排（不改 Agent 工具循环）。

---

## 2. 现状盘点（已可复用，勿重做）

| 资产 | 位置 | 状态 |
|---|---|---|
| 模型注册表（YAML 驱动，新增模型不用改代码） | `config/models.yaml` + `src/llm/models.py` | ✅ 已有 |
| OpenAI 兼容客户端（`base_url` 支持任意端点） | `src/llm/provider.py::_client_for` | ✅ 已有，Ollama 天然可接 |
| 用户级模型偏好参数 | `GisAssistantRequest.model_preference` → `agent.run(model_id=...)` | ✅ 已有（前端未暴露） |
| 模型列表 API | `GET /api/v1/models`（返回 id/label/capabilities） | ✅ 已有（信息不全） |
| 用户偏好存储（key/value/confidence） | `src/orchestrator/long_term_memory.py::UserPreference` + `user_preferences` 表 | ✅ 已有，可复用 |
| 明暗主题 | `frontend/src/composables/useTheme.ts` + `App.vue` + `style.css` | ✅ 已有（按钮已加） |
| 权限模式（会话级） | `src/gis_toolkit/approval.py::ApprovalGate` | ✅ 已有 |

**缺什么（本期开发）**
- 前端设置入口与设置面板（抽屉）；
- 用户设置读写 API（默认模型 / 主题 / 默认权限模式）；
- 用户自定义模型 API（新增/删除/测试连通），与内置注册表叠加；
- `models.yaml` 预置 Ollama 本地条目 + 文档。

---

## 3. 总体架构

```
前端顶栏「齿轮」→ n-drawer 设置面板
   ├─ 模型分区：默认模型下拉 + 添加/删除自定义 + 测试连通
   ├─ 外观分区：明暗主题（联动 useTheme）
   └─ 偏好分区：默认权限模式
        │
        ▼
FastAPI 设置 API
   ├─ GET/PUT /api/v1/settings            → 用户标量偏好（UserPreference 表）
   ├─ GET/POST/DELETE /api/v1/models       → 用户自定义模型（user_models 表）
   └─ POST /api/v1/models/{id}/test        → 连通性测试（发最小请求）
        │
        ▼
LLM 调用链
   load_registry()（内置 models.yaml） ⊕ user_models（用户自定义）→ LLMProvider
```

**关键设计原则**
- **两层模型源**：内置注册表（`models.yaml`，随仓库分发）为只读基线；用户自定义模型存 DB，运行时与内置叠加，`id` 冲突时用户自定义优先；
- **OpenAI 兼容协议收口**：DeepSeek / MiniMax / OpenRouter / Ollama / 任意自建网关都走 `base_url` + OpenAI SDK，不引入第二套 SDK；
- **配置生效即时性**：设置改动后下一次请求立即生效（注册表每次请求 `load_registry()` 叠加，不做常驻缓存；如后续需要可加 `lru_cache` + 失效标记）。

---

## 4. 数据与存储设计

### 4.1 用户标量偏好（复用 `user_preferences` 表）

沿用 `UserPreference`（key / value / category / confidence）。统一 key：

| key | value 格式 | 说明 |
|---|---|---|
| `settings:v1` | JSON：`{"model_id": "...", "theme": "dark", "permission_mode": "ask"}` | 用户设置快照（整块覆盖写） |

- 归属维度：`agent_name = settings:{user_id}`（与 GIS lesson 的 `gis_assistant:{user_id}` 同模式）；
- 读：`get_user_preference(key)` 按 `(key, agent_name)` 查；写：`save_user_preference`（INSERT OR REPLACE）；
- 兜底：无记录时返回系统默认（`model_id=注册表默认、theme=dark、permission_mode=ask`）。

### 4.2 用户自定义模型（新增 `user_models` 表）

在 `long_term_memory.db`（沿用现有连接管理）新增表：

```sql
CREATE TABLE IF NOT EXISTS user_models (
    id          TEXT PRIMARY KEY,        -- 规范化 id，如 ollama-local / my-gateway
    user_key    TEXT NOT NULL,           -- 归属：settings:{user_id}
    label       TEXT NOT NULL,
    provider    TEXT NOT NULL DEFAULT 'openai-compatible',
    model       TEXT NOT NULL,           -- 发送给服务的模型名（Ollama 为本地模型名）
    base_url    TEXT NOT NULL,           -- 如 http://localhost:11434/v1
    api_key     TEXT,                    -- 明文存库（见 6 安全说明），可空（本地无 key）
    capabilities TEXT NOT NULL DEFAULT '["chat","tools"]',
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_models_user ON user_models(user_key);
```

- 归属隔离：`user_key = settings:{user_id}`，不同用户互不可见；
- 实现位置：新增 `src/gis_toolkit/user_settings.py`（封装读写，供 server 与 models 层复用），表结构放 `src/llm/models.py` 的建表辅助或 `user_settings.py` 内；
- `GET /api/v1/models` 返回时：内置 + 当前用户自定义合并，`is_custom: true` 标记自定义项。

### 4.3 模型加载叠加

扩展 `src/llm/models.py`：

```python
def load_registry(user_key: str | None = None) -> ModelRegistry:
    """内置 models.yaml ⊕ 用户自定义 user_models"""
    # 现有逻辑不变
    if user_key:
        custom = user_settings.list_models(user_key)
        # custom 覆盖同名内置 id
```

- `LLMProvider` 初始化与 `/api/v1/models` 都改走 `load_registry(user_key=...)`；
- `ModelConfig` 增加 `is_custom` / `requires_key` / `has_key` 字段（`to_dict()` 输出给前端）。

---

## 5. API 契约

### 5.1 用户设置

```
GET /api/v1/settings            (X-API-Key + user_id)
→ 200 {"model_id": "deepseek-v4-pro", "theme": "dark", "permission_mode": "ask"}

PUT /api/v1/settings
body  {"model_id"?: "...", "theme"?: "dark"|"light", "permission_mode"?: "readonly"|"auto"|"ask"}
→ 200 {同上（合并后的完整快照）}
```

- `theme` 仅作服务端持久化（前端仍以 `localStorage` 即时渲染，登录态同步服务端）；
- `model_id` 非法值：拒绝写入（400，返回合法值列表）。

### 5.2 模型管理

```
GET /api/v1/models
→ 200 {
    "models": [
      {"id","label","provider","model","base_url","capabilities",
       "requires_key": bool, "has_key": bool, "is_custom": bool}
    ],
    "default": "deepseek-v4-pro",
    "user_model_id": "deepseek-v4-pro"   // 用户设置中的选择（未设置时=default）
  }

POST /api/v1/models
body  {"label","provider"?: "openai-compatible","model","base_url","api_key"?: "","capabilities"?: [...]}
→ 201 {"id": "my-gateway", ...}          // id 由服务端从 label 生成 slug，冲突则追加序号

DELETE /api/v1/models/{model_id}          // 仅允许删用户自定义（is_custom）
→ 200 {"ok": true}

POST /api/v1/models/{model_id}/test
→ 200 {"ok": true, "latency_ms": 1234, "message": "..."}
→ 200 {"ok": false, "message": "连接失败: ..."}   // 不抛 5xx，测试失败也返回 200 + ok:false
```

- `POST /models` 校验：`base_url` 必须 http(s) 开头；`label` 非空；重复 `(user_key, base_url, model)` 拒绝；
- `DELETE` 内置模型返回 403；删除的是当前用户设置里的 `model_id` 时，设置回退到 default。

### 5.3 连通性测试实现

```python
def test_model_connection(base_url: str, model: str, api_key: str | None, timeout: float = 8.0) -> dict:
    client = OpenAI(base_url=base_url, api_key=api_key or "none", timeout=timeout)
    # 发 1 条最小 chat 请求（max_tokens=8），成功即 ok
```

- 使用线程池/`run_in_executor` 避免阻塞事件循环；
- 本地 Ollama 未启动时返回 `ok:false + 明确提示（连不上 11434）`。

---

## 6. 安全与合规

1. **API key 不回显**：`GET /models` 只返回 `has_key`（是否有 key），不返回明文；编辑模型只允许整体覆盖写入，不做「读回再改」；
2. **明文入库说明**：MVP 阶段自定义 key 明文存 `long_term_memory.db`（本地单机，`.gitignore` 已忽略该库）；上线前可升级为加密列（`cryptography` Fernet，密钥进 `.env`），本期不做；
3. **内置 key 保持 `.env`**：内置模型（deepseek 等）继续走 `api_key_env`，不从 DB 读；
4. **本地模型白名单**：`base_url` 指向本机（`localhost`/`127.0.0.1`）时不强制要求 key；
5. **输入净化**：`label`/`model`/`base_url` 做长度与字符校验（≤200 字符，禁换行），防注入；所有写操作走 `user_id` 隔离。

---

## 7. Ollama 专项

### 7.1 预置注册表条目（改 `config/models.yaml`）

```yaml
  ollama-local:
    label: "Ollama 本地"
    provider: openai-compatible
    model: qwen2.5:7b
    base_url: "http://localhost:11434/v1"
    # 无 api_key_env：本地无 key
    input_price_per_m: 0.0
    output_price_per_m: 0.0
    capabilities: [chat, tools]
```

`fallback_chains` 增加：`ollama-local: [deepseek-v4-pro]`（本地挂了自动走云端兜底，复用现有 failover）。

### 7.2 接入要点

- Ollama 提供 OpenAI 兼容端点 `/v1`，`base_url = http://localhost:11434/v1`，`api_key` 任意值（Provider 缺省 `"none"` 即可）；
- 用户在设置里「添加模型」填 `base_url=http://localhost:11434/v1`、`model=本地已拉取的模型名（如 qwen2.5:7b）`，可留空 key；
- 工具调用：Ollama 新版支持 function calling，`capabilities: [chat, tools]` 保持与云端一致；
- 预置条目只保证「可用」，实际模型名取决于用户本机 `ollama list`；设置面板的测试连通会给出真实报错信息。

---

## 8. 前端设计

### 8.1 入口

顶栏右侧（主题按钮旁）新增「齿轮」按钮（内联 SVG，复用现有按钮风格 `.gis-theme-btn` 样式），点击打开 `n-drawer`（Naive UI，宽度 ~380px，`placement="right"`）。

### 8.2 面板分区

1. **模型**
   - 默认模型下拉：`GET /models` 返回列表，`value = id`，`label = label (+ (自定义) 标记)`；切换即 `PUT /settings {model_id}`；
   - 「+ 添加模型」折叠表单：label / base_url / model / api_key(可空) / capabilities(默认 chat+tools) → `POST /models` → 刷新列表；
   - 每个自定义模型行尾：「测试」按钮（`POST /models/{id}/test`，内联显示 成功/失败+原因）与「删除」；
   - 内置模型不显示删除，只显示测试。
2. **外观**
   - 明/暗切换（复用 `useTheme()`，直接改 `isDark.value`）；选择同时 `PUT /settings {theme}` 同步服务端。
3. **偏好**
   - 默认权限模式下拉：询问审批 / 自动执行 / 只读模式（会话初始值，仍可在顶栏临时切换）。

### 8.3 交互细节

- 打开抽屉时拉取 `GET /settings` + `GET /models`；关闭不保留脏状态；
- 模型切换后提示「下次对话生效」；
- 测试连通中按钮 loading，避免重复点击；
- 移动端（<768px）抽屉宽度改 100%。

---

## 9. 测试与验收

### 9.1 单元测试（pytest）

新增 `tests/test_user_settings.py`：
1. 设置 CRUD：PUT 写入、GET 读取、无记录返回默认、非法 model_id 400；
2. 自定义模型 CRUD：POST 生成 id、DELETE 隔离（A 用户删不到 B 用户）、内置模型 DELETE 403；
3. 注册表叠加：`load_registry(user_key)` 内置+自定义合并、同名 id 用户优先；
4. 连通性测试：mock OpenAI 客户端成功/失败两分支。

### 9.2 前端验证

构建后 `npm run build` 通过；`playwright` 打开页面确认：抽屉打开、模型下拉渲染、添加/删除/测试流程、主题切换联动。

### 9.3 手工验收清单

- [ ] 顶栏齿轮打开设置抽屉；
- [ ] 切换默认模型后，新对话按所选模型执行（`/api/v1/gis-assistant/run` 携带所选 model_id）；
- [ ] 添加自定义模型（Ollama 场景：`base_url=http://localhost:11434/v1`）→ 测试连通：Ollama 在跑则 ok，未启动则给出明确失败原因；
- [ ] 删除自定义模型后列表刷新，当前默认回退；
- [ ] 主题切换前后端一致，刷新保持；
- [ ] 默认权限模式改动后新会话生效。

---

## 10. 开发任务拆分（按提交顺序）

### P0 — 后端基础（先合入可运行）
1. `src/gis_toolkit/user_settings.py`：`user_models` 建表 + 用户设置/自定义模型 CRUD；
2. `src/llm/models.py`：`load_registry(user_key)` 叠加 + `ModelConfig` 增 `is_custom/requires_key/has_key`；
3. server：`GET/PUT /api/v1/settings`、`GET/POST/DELETE /api/v1/models`；
4. 单测 `tests/test_user_settings.py`。

### P1 — 前端设置面板
5. `frontend/src/api/gis.ts` 增加 settings/models API 封装；
6. `GisAssistant.vue` 顶栏齿轮 + `n-drawer` 设置面板（模型/外观/偏好三分区）；
7. 构建同步 `src/web/static/`。

### P2 — Ollama 与打磨
8. `config/models.yaml` 预置 `ollama-local` + failover；
9. 连通性测试接口 `POST /models/{id}/test`（含 loading/内联结果）；
10. 前端体验打磨 + 手工验收。

---

## 11. 开发规范（沿用）

1. **测试不过不准提交**：`scripts\check.bat` 全绿（ruff + pytest）；
2. **提交信息**：`<type>(<scope>): <描述>`，type ∈ feat/fix/docs/style/refactor/test/chore；
3. **禁止提交**：`data/projects.db`、`long_term_memory.db`、`CLAUDE.md`、日志、`data/gis_*` 产物目录；
4. **风格**：中文注释；公共函数类型注解；行宽 ≤100；
5. **分支**：继续在 `feat/gis-mcp-server` 或建 `feat/settings-module` 并保持可合并。

## 12. 验证命令

```bash
venv\Scripts\python.exe -m pytest tests/test_user_settings.py -q      # 设置模块单测
venv\Scripts\python.exe -m pytest tests -q --basetemp=.pytest_tmp\basetemp   # 全量回归
venv\Scripts\python.exe -m ruff check src tests                        # lint
cd frontend && npm run build                                           # 前端构建
venv\Scripts\python.exe .pytest_tmp\sync_frontend.py                   # 同步静态产物
```

## 13. 审计检查点（Codex 验收标准）

1. **变更说明**：改了哪些文件、新增 API、对应验收项；
2. **测试证据**：`test_user_settings.py` 全过 + 全量回归无新增失败；
3. **安全边界**：key 不回显、用户隔离（user_key）、内置模型不可删、输入净化；
4. **一致性**：`config/models.yaml`（预置）与 `user_models`（自定义）在 `/models` 合并展示，Agent 实际按所选 id 调用；
5. **前端**：抽屉三分区齐全，构建产物已同步 `src/web/static/`，手工验收清单勾选。
