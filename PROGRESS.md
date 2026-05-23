# AI Dev Platform — 开发进度

> 最后更新：2026-05-01

## 总览

| 阶段 | 状态 | 测试数 | 完成日期 |
|------|------|--------|----------|
| Phase 1 — MVP 需求分析 | 🟢 已完成 | 35 | 2026-05-01 |
| Phase 2 — 架构设计 | 🟢 已完成 | 39 | 2026-05-01 |
| Phase 3 — 代码生成 | 🟢 已完成 | 43 | 2026-05-01 |
| Phase 4 — 测试验证 | 🟢 已完成 | 45 | 2026-05-01 |
| Phase 5 — 打包交付 | 🟢 已完成 | 47 | 2026-05-01 |
| Phase 6 — Web 界面 | 🟢 已完成 | 47 | 2026-05-01 |

---

## 各阶段详情

### Phase 1 — 需求分析 ✅
| Task | 内容 | 测试 |
|------|------|------|
| 1.1 | 项目骨架 | - |
| 1.2 | Agent 基类 + LLM Provider | 7 |
| 1.3 | 共享状态 + LangGraph 图 | 9 |
| 1.4 | 需求分析 Agent + Prompt | 3 E2E |
| 1.5 | 本地沙箱执行器 | 16 |
| 1.6 | E2E 测试 | 3 |

### Phase 2 — 架构设计 ✅
| Task | 内容 | 测试 |
|------|------|------|
| 2.1 | 架构师 Agent + Prompt | 2 E2E |
| 2.2 | E2E 流程 (Requirement→Architect) | 2 E2E |

### Phase 3 — 代码生成 ✅
| Task | 内容 | 测试 |
|------|------|------|
| 3.1 | 后端 Agent + Prompt | 2 E2E |
| 3.2 | 前端 Agent + Prompt | 2 E2E |

### Phase 4 — 测试验证 ✅
| Task | 内容 | 测试 |
|------|------|------|
| 4.1 | 测试 Agent + Prompt | 2 E2E |

### Phase 5 — 打包交付 ✅
| Task | 内容 | 测试 |
|------|------|------|
| 5.1 | 部署 Agent + Prompt | 2 E2E |

### Phase 6 — Web 界面 ✅
| Task | 内容 |
|------|------|
| 6.1 | FastAPI + WebSocket 服务 | 实时推送流水线进度 |
| 6.2 | 前端 UI (`index.html`) | 输入想法 → 查看各阶段产出 |

---

## 当前统计

| 指标 | 数值 |
|------|------|
| 源文件 | 21 |
| 测试文件 | 13 |
| 总测试 | 47 |
| 通过 | 47 |
| 失败 | 0 |

---

## Agent 全景图

```
用户输入想法 (Web UI)
  → RequirementAgent (MiniMax 2.7)   追问 → PRD
  → ArchitectAgent   (DeepSeek V4)    PRD → 技术方案
  → BackendAgent     (DeepSeek V4)    技术方案 → FastAPI 代码  ┐
  → FrontendAgent    (MiniMax 2.7)   技术方案 → React 代码    ┘ 并行
  → TesterAgent      (MiniMax 2.7)   审查代码 → 测试报告
  → DeployerAgent    (MiniMax 2.7)   打包 zip → 交付
```

### Web 服务
- **FastAPI**: `src/web/server.py`（REST + WebSocket）
- **前端**: `src/web/static/index.html`
- **WebSocket 端点**: `/ws`（action: build / answer）
- **主页**: `/`（输入想法 → 触发流水线 → 实时看进度）

---

## 技术决策记录

| # | 日期 | 决策 | 原因 |
|---|------|------|------|
| 1 | 2026-05-01 | DeepSeek `deepseek-v4-pro` / MiniMax `MiniMax-M2.7` | 用户确认的模型名 |
| 2 | 2026-05-01 | DeepSeek base_url 需 `/v1` 后缀 | OpenAI SDK 路径拼接 |
| 3 | 2026-05-01 | `current_stage` 使用 Annotated reducer | 并行分支写入冲突 |
| 4 | 2026-05-01 | Provider 模块顶部自动 load_dotenv | 避免重复调用 |
| 5 | 2026-05-01 | `list_files()` 返回 POSIX 路径 | Windows 反斜杠兼容 |
| 6 | 2026-05-01 | ASK_USER 检测使用正则 | LLM 输出格式不稳定 |
| 7 | 2026-05-01 | RequirementAgent 硬限制 3 轮追问 | LLM 不遵守 Prompt 约束 |
| 8 | 2026-05-01 | DeployerAgent 沙箱写文件后打包 | 隔离 + 自动清理 |
| 9 | 2026-05-01 | 剥离 `<think>` 推理块后再检测 ASK_USER | MiniMax M2.7 输出含推理内容 |
| 10 | 2026-05-01 | 追问后 question 再 strip 一次 ASK_USER 标记 | LLM 可能在问答中输出多段 ASK_USER |
| 11 | 2026-05-01 | `run_pipeline` 改为分步可恢复架构 | 追问时需中断流水线，answer 时从断点恢复 |
| 12 | 2026-05-01 | `client_id` 改用 `uuid4().hex` | `str(id(ws))` 可能重复 |
| 13 | 2026-05-01 | 前端结果拼接改用 `innerHTML +=`，带 id 去重 | 避免后续阶段覆盖之前的产出卡片 |
| 14 | 2026-05-01 | Deployer 代码为空时写占位文件 | 防止 zip 内缺少文件 |
| 15 | 2026-05-01 | E2E 测试移除脆弱的英文关键词断言 | LLM 中文输出不含 "API" 等词导致 flaky |
