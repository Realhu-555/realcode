"""端到端测试：后端 Agent"""

from src.agents.backend import BackendAgent
from src.orchestrator.state import Stage

TECH_PLAN_FIXTURE = """---TECH_PLAN_START---
## 技术选型

### 后端
- **框架**: FastAPI（Python 3.12+）
- **数据库**: SQLite
- **ORM**: SQLAlchemy

### 前端
- **框架**: React 18 + TypeScript
- **样式**: Tailwind CSS

## API 设计

### 文章
| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | /api/posts | 获取文章列表 | - | { items: [...] } |
| GET | /api/posts/{id} | 获取单篇文章 | - | { id, title, ... } |
| POST | /api/posts | 创建文章 | { title, content, tags } | { id, ... } |
| PUT | /api/posts/{id} | 更新文章 | { title, content, tags } | { id, ... } |
| DELETE | /api/posts/{id} | 删除文章 | - | { ok: true } |

### 评论
| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | /api/posts/{id}/comments | 获取评论 | - | { items: [...] } |
| POST | /api/posts/{id}/comments | 发表评论 | { author, content } | { id, ... } |

## 数据库设计

```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id),
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 项目结构
```
backend/
├── main.py
├── database.py
├── models.py
├── schemas.py
└── routers/
    ├── posts.py
    └── comments.py

frontend/
├── src/
│   ├── App.tsx
│   ├── pages/
│   ├── components/
│   ├── api/
│   └── types/
```
---TECH_PLAN_END---"""


def test_backend_agent_generates_code():
    """后端 Agent 从技术方案生成可运行代码"""
    agent = BackendAgent()
    state = {
        "user_idea": "博客",
        "prd": "...",
        "tech_plan": TECH_PLAN_FIXTURE,
        "ask_user": None,
        "current_stage": Stage.BACKEND,
        "messages": [],
    }

    result = agent.run(state)
    code = result.get("backend_code")

    assert code is not None, "应该产出后端代码"
    assert "from fastapi" in code.lower() or "FastAPI" in code
    assert "main.py" in code or "main" in code
    assert result["current_stage"] == Stage.TESTING


def test_backend_agent_handles_missing_tech_plan():
    """无技术方案时返回错误"""
    agent = BackendAgent()
    state = {
        "user_idea": "",
        "prd": None,
        "tech_plan": None,
        "ask_user": None,
        "current_stage": Stage.BACKEND,
        "messages": [],
    }

    result = agent.run(state)
    assert result.get("error_message") is not None
