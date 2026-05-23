# 测试通过率数据分析功能 — 设计文档

> **项目**: ai-dev-platform  
> **版本**: v1.0  
> **日期**: 2026-05-10  
> **状态**: 设计阶段  

---

## 目录

1. [功能概述](#1-功能概述)
2. [数据模型](#2-数据模型)
3. [API 设计](#3-api-设计)
4. [前端展示](#4-前端展示)
5. [实现步骤](#5-实现步骤)
6. [技术约束](#6-技术约束)

---

## 1. 功能概述

### 1.1 背景

当前平台的测试流程由 `TesterAgent` 完成，其产出是 `test_report`（字符串），存入 `ProjectState.test_report` 后直接流转至部署阶段。存在以下问题：

- **测试结果不可追溯**：`test_report` 为纯文本，无法结构化查询历史构建的通过率。
- **无趋势分析**：无法观察某类项目/某段时间内的测试质量变化。
- **失败模式无归因**：不知道哪些测试用例反复失败、失败的根因是什么。
- **无跨项目对比**：不同项目之间的测试表现无法横向对比。

### 1.2 目标

构建一套**测试通过率数据分析系统**，在 TesterAgent 执行完毕后自动采集结构化测试数据，提供：

| 能力 | 说明 |
|------|------|
| **实时采集** | 每次流水线运行后自动记录测试结果 |
| **历史追溯** | 按项目/时间/Agent 维度查询历史数据 |
| **趋势分析** | 折线图展示通过率随时间/构建次数的变化 |
| **失败归因** | 分类统计失败原因（断言错误、超时、依赖缺失等） |
| **跨项目对比** | 不同项目/技术栈的测试质量横向对比 |

### 1.3 用户场景

```
场景 A：开发者想知道"最近一周生成的项目，测试通过率是多少"
场景 B：开发者发现"后端代码的测试失败率高于前端代码"
场景 C：开发者想看"某个项目经过 5 次迭代后，测试通过率是否有提升"
场景 D：开发者想知道"Python 项目的测试通过率是否比 Node 项目高"
```

---

## 2. 数据模型

### 2.1 存储方案

采用 **SQLite** 作为主存储，原因：

- 零依赖，无需额外部署数据库
- 与现有项目轻量级定位一致
- 通过 SQLAlchemy ORM 提供异步访问
- 后续可平滑迁移至 PostgreSQL

### 2.2 核心表结构

```
┌─────────────────────────────┐
│        pipeline_runs        │  ← 每次完整流水线执行
│  id (PK)                    │
│  project_id                 │
│  project_name               │
│  user_idea                  │
│  stage                      │  ← 当前到达的阶段
│  status                     │  ← running / success / failed / error
│  started_at                 │
│  finished_at                │
│  duration_ms                │
│  model_used                 │  ← 使用的 LLM 模型
│  agent_versions             │  ← Agent 版本快照(JSON)
└─────────────────────────────┘
            │ 1:N
            ▼
┌─────────────────────────────┐
│        test_results         │  ← 单次测试执行结果
│  id (PK)                    │
│  pipeline_run_id (FK)       │
│  test_suite_name            │  ← 测试套件名称
│  total_tests                │
│  passed                     │
│  failed                     │
│  skipped                    │
│  error_count                │
│  pass_rate                  │  ← 通过率(0.0~1.0)
│  duration_ms                │
│  raw_output                 │  ← 原始测试报告文本
│  executed_at                │
└─────────────────────────────┘
            │ 1:N
            ▼
┌─────────────────────────────┐
│       test_failures         │  ← 每个失败用例的详情
│  id (PK)                    │
│  test_result_id (FK)        │
│  test_name                  │
│  test_file                  │  ← 所在文件路径
│  failure_type               │  ← assertion / timeout / import / runtime / logic
│  failure_message            │  ← 错误信息
│  stack_trace                │  ← 堆栈(截取前 2000 字符)
│  agent_source               │  ← 生成该代码的 Agent(backend / frontend)
│  category                   │  ← 归类：api / ui / database / auth / other
└─────────────────────────────┘
```

### 2.3 SQLAlchemy 模型定义

```python
# src/analytics/models.py

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Text, DateTime,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class RunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


class FailureType(str, enum.Enum):
    ASSERTION = "assertion"
    TIMEOUT = "timeout"
    IMPORT = "import"
    RUNTIME = "runtime"
    LOGIC = "logic"
    OTHER = "other"


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(64), index=True, nullable=False)
    project_name = Column(String(256), nullable=False)
    user_idea = Column(Text, nullable=False)
    stage = Column(String(32), nullable=False)
    status = Column(SAEnum(RunStatus), default=RunStatus.RUNNING, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    model_used = Column(String(128), nullable=True)
    agent_versions = Column(JSON, nullable=True)

    test_results = relationship("TestResult", back_populates="pipeline_run",
                                cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id"), index=True)
    test_suite_name = Column(String(128), nullable=False)
    total_tests = Column(Integer, nullable=False, default=0)
    passed = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    skipped = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    pass_rate = Column(Float, nullable=False, default=0.0)
    duration_ms = Column(Integer, nullable=True)
    raw_output = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    pipeline_run = relationship("PipelineRun", back_populates="test_results")
    failures = relationship("TestFailure", back_populates="test_result",
                            cascade="all, delete-orphan")


class TestFailure(Base):
    __tablename__ = "test_failures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), index=True)
    test_name = Column(String(512), nullable=False)
    test_file = Column(String(512), nullable=True)
    failure_type = Column(SAEnum(FailureType), nullable=False, index=True)
    failure_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    agent_source = Column(String(32), nullable=True)  # "backend" / "frontend"
    category = Column(String(32), nullable=True, index=True)  # api/ui/database/auth/other

    test_result = relationship("TestResult", back_populates="failures")
```

### 2.4 项目目录结构（新增）

```
src/
├── analytics/                    # ← 新增模块
│   ├── __init__.py
│   ├── models.py                 # SQLAlchemy 数据模型
│   ├── database.py               # 数据库初始化 & 会话管理
│   ├── collector.py              # 测试数据采集器
│   ├── parser.py                 # 测试报告解析器
│   └── queries.py                # 查询 & 聚合函数
├── web/
│   └── server.py                 # 新增 analytics 路由
tests/
├── test_analytics_models.py      # 模型单元测试
├── test_analytics_parser.py      # 解析器测试
├── test_analytics_queries.py     # 查询逻辑测试
└── test_analytics_api.py         # API 集成测试
```

---

## 3. API 设计

### 3.1 基础信息

- **Base URL**: `/api/v1/analytics`
- **数据格式**: JSON
- **认证**: 与现有 `/ws` 端点保持一致（当前无认证，后续可扩展）

### 3.2 接口列表

#### 3.2.1 记录测试结果（内部调用）

```
POST /api/v1/analytics/test-results
```

**请求体**：

```json
{
  "pipeline_run_id": 42,
  "test_suite_name": "pytest",
  "total_tests": 25,
  "passed": 20,
  "failed": 3,
  "skipped": 2,
  "error_count": 0,
  "duration_ms": 8500,
  "raw_output": "===== 25 passed, 3 failed, 2 skipped in 8.5s =====",
  "failures": [
    {
      "test_name": "tests/test_api.py::test_create_user",
      "test_file": "tests/test_api.py",
      "failure_type": "assertion",
      "failure_message": "assert 404 == 200",
      "stack_trace": "Traceback (most recent call last):\n  File ...",
      "agent_source": "backend",
      "category": "api"
    }
  ]
}
```

**响应**（201 Created）：

```json
{
  "id": 1,
  "pipeline_run_id": 42,
  "pass_rate": 0.8,
  "failure_count": 3,
  "created_at": "2026-05-10T18:30:00Z"
}
```

#### 3.2.2 获取测试通过率趋势

```
GET /api/v1/analytics/trends
```

**查询参数**：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `project_id` | string | 否 | - | 筛选项目 |
| `days` | int | 否 | 30 | 查看最近 N 天 |
| `interval` | string | 否 | `day` | 聚合粒度：`day` / `week` / `month` |
| `agent_source` | string | 否 | - | 筛选 Agent：`backend` / `frontend` |

**响应**（200 OK）：

```json
{
  "data_points": [
    {
      "date": "2026-05-01",
      "avg_pass_rate": 0.75,
      "total_runs": 12,
      "total_tests": 300,
      "total_passed": 225
    },
    {
      "date": "2026-05-02",
      "avg_pass_rate": 0.82,
      "total_runs": 8,
      "total_tests": 200,
      "total_passed": 164
    }
  ],
  "summary": {
    "overall_pass_rate": 0.79,
    "total_runs": 156,
    "trend_direction": "improving",
    "trend_change_pct": 5.2
  }
}
```

#### 3.2.3 失败原因分析

```
GET /api/v1/analytics/failure-analysis
```

**查询参数**：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `project_id` | string | 否 | - | 筛选项目 |
| `days` | int | 否 | 30 | 时间范围 |
| `failure_type` | string | 否 | - | 筛选失败类型 |
| `agent_source` | string | 否 | - | 筛选 Agent |

**响应**（200 OK）：

```json
{
  "by_failure_type": [
    { "type": "assertion", "count": 45, "percentage": 38.5 },
    { "type": "import", "count": 28, "percentage": 23.9 },
    { "type": "timeout", "count": 20, "percentage": 17.1 },
    { "type": "runtime", "count": 15, "percentage": 12.8 },
    { "type": "logic", "count": 9, "percentage": 7.7 }
  ],
  "by_category": [
    { "category": "api", "count": 52, "percentage": 44.4 },
    { "category": "ui", "count": 31, "percentage": 26.5 },
    { "category": "database", "count": 20, "percentage": 17.1 },
    { "category": "auth", "count": 14, "percentage": 12.0 }
  ],
  "top_recurring": [
    {
      "test_name": "tests/test_api.py::test_create_user",
      "failure_count": 8,
      "last_failure_type": "assertion",
      "last_message": "assert 404 == 200",
      "agent_source": "backend"
    }
  ]
}
```

#### 3.2.4 跨项目对比

```
GET /api/v1/analytics/compare
```

**查询参数**：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `project_ids` | string | 是 | - | 逗号分隔的项目 ID |
| `days` | int | 否 | 30 | 时间范围 |

**响应**（200 OK）：

```json
{
  "projects": [
    {
      "project_id": "proj_abc",
      "project_name": "个人博客",
      "total_runs": 15,
      "avg_pass_rate": 0.85,
      "avg_duration_ms": 7200,
      "top_failure_category": "api"
    },
    {
      "project_id": "proj_def",
      "project_name": "任务管理工具",
      "total_runs": 8,
      "avg_pass_rate": 0.72,
      "avg_duration_ms": 9100,
      "top_failure_category": "ui"
    }
  ]
}
```

#### 3.2.5 获取最新构建概览

```
GET /api/v1/analytics/overview
```

**查询参数**：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `limit` | int | 否 | 20 | 返回条数 |

**响应**（200 OK）：

```json
{
  "recent_runs": [
    {
      "pipeline_run_id": 42,
      "project_name": "个人博客",
      "status": "success",
      "pass_rate": 0.92,
      "total_tests": 25,
      "failed": 2,
      "duration_ms": 7500,
      "finished_at": "2026-05-10T18:30:00Z"
    }
  ],
  "stats": {
    "total_runs": 156,
    "overall_pass_rate": 0.79,
    "runs_today": 5,
    "avg_pass_rate_today": 0.83
  }
}
```

#### 3.2.6 手动触发重新分析

```
POST /api/v1/analytics/reanalyze/{pipeline_run_id}
```

**响应**（200 OK）：

```json
{
  "pipeline_run_id": 42,
  "status": "reanalyzed",
  "pass_rate": 0.88,
  "updated_at": "2026-05-10T19:00:00Z"
}
```

### 3.3 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "project_ids 参数不能为空",
    "details": null
  }
}
```

| HTTP 状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | `VALIDATION_ERROR` | 请求参数校验失败 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |

---

## 4. 前端展示

### 4.1 页面规划

新增独立页面 `/analytics`，通过顶部导航栏访问。

```
┌──────────────────────────────────────────────────────┐
│  AI Dev Platform    [构建历史] [数据分析] [设置]      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ 📊 测试通过率概览                                │ │
│  │                                                 │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │ │
│  │  │ 总构建数  │ │ 今日通过率│ │ 失败用例  │       │ │
│  │  │   156    │ │  83.2%   │ │   12     │       │ │
│  │  └──────────┘ └──────────┘ └──────────┘       │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ 📈 通过率趋势图                                  │ │
│  │  [折线图]                                       │ │
│  │  X轴: 日期  Y轴: 通过率(%)                       │ │
│  │  支持切换：日/周/月 粒度                          │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌──────────────┐ ┌────────────────────────────────┐ │
│  │ 🍩 失败原因  │ │ 📊 按 Agent 分布               │ │
│  │   分布       │ │                                │ │
│  │  [环形图]    │ │  [柱状图]                      │ │
│  │              │ │  backend: 65%  frontend: 35%   │ │
│  └──────────────┘ └────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ 🔁 反复失败的测试用例 Top 10                     │ │
│  │                                                 │ │
│  │  1. test_create_user    ▓▓▓▓▓▓▓▓░░  8次失败    │ │
│  │  2. test_auth_token     ▓▓▓▓░░░░░░  5次失败    │ │
│  │  3. test_db_connect     ▓▓▓░░░░░░░  4次失败    │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ 📋 最近构建记录                                  │ │
│  │                                                 │ │
│  │  #42  个人博客    ✅ 92%  8.5s   2026-05-10    │ │
│  │  #41  任务管理    ❌ 68%  12.1s  2026-05-10    │ │
│  │  #40  电商后台    ✅ 85%  9.2s   2026-05-09    │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 4.2 图表类型与技术选型

| 图表 | 用途 | 推荐库 | 备选 |
|------|------|--------|------|
| **折线图** | 通过率随时间变化趋势 | Chart.js | ECharts |
| **环形图/饼图** | 失败原因类型分布 | Chart.js | D3.js |
| **柱状图** | 按 Agent/项目对比通过率 | Chart.js | ECharts |
| **水平条形图** | Top N 反复失败用例 | Chart.js | - |
| **数字卡片** | KPI 概览（总构建数、今日通过率等） | 原生 HTML/CSS | - |

**推荐选型：Chart.js**

- 轻量（~60KB），与现有前端技术栈（纯 HTML+CSS+JS）兼容
- 无需 Node.js 构建工具链
- 支持响应式和交互式图表

### 4.3 筛选与交互

```html
<!-- 筛选栏组件 -->
<div class="analytics-filters">
  <select id="project-filter">
    <option value="">所有项目</option>
    <!-- 动态加载项目列表 -->
  </select>

  <select id="time-range">
    <option value="7">最近 7 天</option>
    <option value="30" selected>最近 30 天</option>
    <option value="90">最近 90 天</option>
    <option value="365">全部</option>
  </select>

  <select id="agent-filter">
    <option value="">所有 Agent</option>
    <option value="backend">后端 Agent</option>
    <option value="frontend">前端 Agent</option>
  </select>

  <button onclick="refreshAnalytics()">刷新</button>
</div>
```

### 4.4 前端文件结构

```
src/web/static/
├── analytics.html              # 数据分析主页面
├── js/
│   ├── analytics.js            # 数据分析核心逻辑
│   ├── charts.js               # 图表渲染模块
│   └── filters.js              # 筛选交互模块
└── css/
    └── analytics.css           # 数据分析页面样式
```

### 4.5 响应式设计

- **桌面**（>1024px）：双栏布局，左侧趋势图 + 右侧分布图
- **平板**（768-1024px）：单栏，图表纵向堆叠
- **手机**（<768px）：隐藏次要图表，保留 KPI 卡片和趋势图

---

## 5. 实现步骤

按优先级从高到低排序，每步均可独立交付。

### Phase 1：数据采集基础（优先级 P0）

> 目标：跑通"采集 → 存储 → 查询"最小闭环

| 步骤 | 任务 | 预估工时 | 依赖 |
|------|------|----------|------|
| 1.1 | 创建 `src/analytics/` 模块目录 | 0.5h | - |
| 1.2 | 编写 `models.py` — SQLAlchemy 模型 | 2h | - |
| 1.3 | 编写 `database.py` — 数据库初始化、会话管理 | 2h | 1.2 |
| 1.4 | 编写 `parser.py` — 解析 pytest JSON 输出 | 3h | - |
| 1.5 | 编写 `collector.py` — 测试数据采集器 | 2h | 1.3, 1.4 |
| 1.6 | 集成到 `TesterAgent` — 在 `run()` 末尾调用 collector | 2h | 1.5 |
| 1.7 | 编写单元测试 `test_analytics_models.py` | 2h | 1.2 |
| 1.8 | 编写单元测试 `test_analytics_parser.py` | 2h | 1.4 |

**Phase 1 产出**：
- 流水线每次运行后自动将测试结果写入 SQLite
- 可通过 Python 代码查询历史数据

### Phase 2：查询与 API（优先级 P0）

> 目标：通过 RESTful API 暴露数据

| 步骤 | 任务 | 预估工时 | 依赖 |
|------|------|----------|------|
| 2.1 | 编写 `queries.py` — 聚合查询函数 | 3h | 1.3 |
| 2.2 | 新增 `src/web/routes/analytics.py` — API 路由 | 3h | 2.1 |
| 2.3 | 在 `server.py` 中挂载 analytics 路由 | 1h | 2.2 |
| 2.4 | 编写 API 集成测试 `test_analytics_api.py` | 3h | 2.2 |
| 2.5 | 编写查询逻辑测试 `test_analytics_queries.py` | 2h | 2.1 |

**Phase 2 产出**：
- 6 个 RESTful API 端点可用
- 所有查询逻辑有测试覆盖

### Phase 3：前端展示（优先级 P1）

> 目标：可视化测试数据

| 步骤 | 任务 | 预估工时 | 依赖 |
|------|------|----------|------|
| 3.1 | 引入 Chart.js（CDN 或静态文件） | 0.5h | - |
| 3.2 | 编写 `analytics.html` 页面骨架 | 2h | - |
| 3.3 | 编写 `charts.js` — 折线图、环形图、柱状图渲染 | 4h | 2.2 |
| 3.4 | 编写 `filters.js` — 筛选交互逻辑 | 2h | 2.2 |
| 3.5 | 编写 `analytics.js` — 页面主逻辑、数据获取 | 3h | 3.2, 3.3, 3.4 |
| 3.6 | 编写 `analytics.css` — 页面样式 | 2h | 3.2 |
| 3.7 | 添加导航栏入口 | 0.5h | 3.2 |

**Phase 3 产出**：
- 完整的数据分析页面
- 支持多维度筛选和交互式图表

### Phase 4：增强功能（优先级 P2）

> 目标：提升分析深度

| 步骤 | 任务 | 预估工时 | 依赖 |
|------|------|----------|------|
| 4.1 | 测试报告解析增强（支持 JUnit XML、TAP 格式） | 4h | 1.4 |
| 4.2 | 失败归因自动化（用 LLM 分类失败原因） | 4h | 1.5 |
| 4.3 | 跨项目对比功能 | 3h | 2.1 |
| 4.4 | 数据导出（CSV / JSON 下载） | 2h | 2.1 |
| 4.5 | 趋势预测（基于历史数据的简单线性回归） | 3h | 2.1 |

### 工时汇总

| Phase | 工时 | 累计 |
|-------|------|------|
| Phase 1 | ~15.5h | 15.5h |
| Phase 2 | ~12h | 27.5h |
| Phase 3 | ~14h | 41.5h |
| Phase 4 | ~16h | 57.5h |

---

## 6. 技术约束

### 6.1 与 LangGraph 的集成

当前 `TesterAgent.run()` 的返回值直接更新 `ProjectState`，数据采集必须在**不改变现有状态流转**的前提下进行。

**集成点：`TesterAgent.run()` 方法**

```python
# 修改前（src/agents/tester.py）
class TesterAgent(BaseAgent):
    def run(self, state: dict) -> dict:
        # ... LLM 调用 ...
        response = self.llm.chat(messages, agent_type="tester")
        return {
            **state,
            "test_report": response,
            "current_stage": "deployment",
            "messages": state.get("messages", []) + [...],
        }

# 修改后
class TesterAgent(BaseAgent):
    def run(self, state: dict) -> dict:
        # ... LLM 调用 ...
        response = self.llm.chat(messages, agent_type="tester")

        # ← 新增：采集测试数据（异步不阻塞主流程）
        try:
            from src.analytics.collector import collect_test_data
            collect_test_data(state, response)
        except Exception:
            pass  # 采集失败不影响主流程

        return {
            **state,
            "test_report": response,
            "current_stage": "deployment",
            "messages": state.get("messages", []) + [...],
        }
```

**关键设计原则**：

| 原则 | 实现方式 |
|------|----------|
| **非侵入式** | 采集逻辑用 try/except 包裹，失败不影响主流程 |
| **同步写入** | 首版采用同步写入 SQLite，避免引入异步复杂度 |
| **幂等性** | 同一 `pipeline_run_id` 重复采集时更新而非插入 |
| **状态无关** | 采集器不修改 `ProjectState`，只读取必要字段 |

### 6.2 测试报告解析策略

当前 `test_report` 是 LLM 生成的自由文本，不是结构化的 pytest 输出。需要双轨解析：

```
策略 A：拦截 pytest 原始输出
  ├── 在 Sandbox 执行 pytest 时捕获 JSON 格式输出
  ├── 解析 pytest --json-report 插件的结构化数据
  └── 直接提取测试用例级别的通过/失败信息

策略 B：解析 LLM 生成的报告（降级方案）
  ├── 用正则从 test_report 中提取 数字/总数/通过/失败
  ├── 示例正则：r'(\d+)\s*(?:passed|通过).*?(\d+)\s*(?:failed|失败)'
  └── 置信度较低，标记为 "parsed_llm_report"
```

**推荐**：优先实现策略 A，策略 B 作为兜底。

### 6.3 并发安全

- SQLite 的 WAL 模式支持并发读，单写入不阻塞
- 写入时使用 `BEGIN IMMEDIATE` 事务避免锁竞争
- 后续如果并发量大，可迁移至 PostgreSQL

### 6.4 数据清理策略

```python
# 自动清理 90 天前的数据
RETENTION_DAYS = 90

# 可通过 API 手动触发清理
POST /api/v1/analytics/cleanup
{
  "older_than_days": 90,
  "dry_run": true
}
```

### 6.5 依赖管理

新增依赖（`pyproject.toml`）：

```toml
dependencies = [
    # 现有依赖...
    "sqlalchemy>=2.0,<3.0",
    "aiosqlite>=0.20.0",   # 异步 SQLite 驱动（可选）
]

[project.optional-dependencies]
analytics = [
    "sqlalchemy>=2.0,<3.0",
]
```

### 6.6 数据库初始化

```python
# src/analytics/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = "sqlite:///./data/analytics.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    # 启用 WAL 模式
    execution_options={"isolation_level": "READ COMMITTED"},
)

SessionLocal = sessionmaker(bind=engine)


def init_db():
    """创建所有表（幂等）"""
    Base.metadata.create_all(bind=engine)


def get_session():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 6.7 与 Web 端点的集成

在 `src/web/server.py` 中新增路由挂载：

```python
# src/web/server.py — 新增

from fastapi import APIRouter
from src.web.routes.analytics import router as analytics_router

# 在 app 初始化后
app.include_router(analytics_router, prefix="/api/v1/analytics")
```

路由文件：

```python
# src/web/routes/analytics.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.analytics.database import get_session
from src.analytics import queries

router = APIRouter()


@router.get("/trends")
async def get_trends(
    project_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    interval: str = Query(default="day", regex="^(day|week|month)$"),
    agent_source: str | None = None,
    db: Session = Depends(get_session),
):
    data = queries.get_pass_rate_trends(
        db, project_id=project_id, days=days,
        interval=interval, agent_source=agent_source,
    )
    return data


@router.get("/failure-analysis")
async def get_failure_analysis(
    project_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    failure_type: str | None = None,
    agent_source: str | None = None,
    db: Session = Depends(get_session),
):
    data = queries.get_failure_analysis(
        db, project_id=project_id, days=days,
        failure_type=failure_type, agent_source=agent_source,
    )
    return data
```

---

## 附录

### A. 测试报告样例

**LLM 生成的 test_report（当前格式）**：

```
## 测试报告

### 测试概览
- 总用例数: 25
- 通过: 20
- 失败: 3
- 跳过: 2

### 失败用例
1. **test_create_user** (tests/test_api.py)
   - 错误类型: AssertionError
   - 描述: 期望返回 200，实际返回 404

2. **test_auth_token** (tests/test_auth.py)
   - 错误类型: ImportError
   - 描述: 无法导入 auth 模块
```

**pytest JSON 输出（策略 A 目标格式）**：

```json
{
  "duration": 8.5,
  "exitcode": 1,
  "tests": [
    {
      "nodeid": "tests/test_api.py::test_create_user",
      "outcome": "passed",
      "duration": 0.12
    },
    {
      "nodeid": "tests/test_api.py::test_get_user",
      "outcome": "failed",
      "duration": 0.08,
      "call": {
        "longrepr": "assert 404 == 200",
        "crash": {
          "path": "tests/test_api.py",
          "lineno": 15
        }
      }
    }
  ],
  "summary": {
    "passed": 20,
    "failed": 3,
    "skipped": 2,
    "error": 0
  }
}
```

### B. 参考资料

- [pytest-json-report](https://github.com/pytest-dev/pytest-json-report) — pytest JSON 报告插件
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/) — ORM 参考
- [Chart.js 文档](https://www.chartjs.org/docs/latest/) — 前端图表库
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/) — 状态图参考
