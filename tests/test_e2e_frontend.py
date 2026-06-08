"""端到端测试：前端 Agent"""

from src.agents.frontend import FrontendAgent
from src.orchestrator.state import Stage

TECH_PLAN_FIXTURE = """---TECH_PLAN_START---
## 技术选型

### 后端
- **框架**: FastAPI
- **数据库**: SQLite

### 前端
- **框架**: React 18 + TypeScript
- **样式**: Tailwind CSS
- **路由**: React Router v6

## API 设计

### 文章
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/posts | 获取文章列表 |
| POST | /api/posts | 创建文章 |

## 页面结构
- **首页**：文章列表，标签筛选
- **文章详情页**：阅读文章，发表评论
- **管理后台**：创建/编辑文章

## 项目结构
```
frontend/
├── src/
│   ├── App.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── PostPage.tsx
│   │   └── AdminPage.tsx
│   ├── components/
│   │   ├── PostCard.tsx
│   │   └── CommentForm.tsx
│   ├── api/
│   │   └── client.ts
│   └── types/
│       └── index.ts
```
---TECH_PLAN_END---"""


def test_frontend_agent_generates_code():
    """前端 Agent 从技术方案生成 React 代码"""
    agent = FrontendAgent()
    state = {
        "user_idea": "博客",
        "prd": "...",
        "tech_plan": TECH_PLAN_FIXTURE,
        "ask_user": None,
        "current_stage": Stage.FRONTEND,
        "messages": [],
    }

    result = agent.run(state)
    code = result.get("frontend_code")

    assert code is not None, "应该产出前端代码"
    assert "React" in code or "react" in code or "tsx" in code
    assert result["current_stage"] == Stage.TESTING


def test_frontend_agent_handles_missing_tech_plan():
    """无技术方案时返回错误"""
    agent = FrontendAgent()
    state = {
        "user_idea": "",
        "prd": None,
        "tech_plan": None,
        "ask_user": None,
        "current_stage": Stage.FRONTEND,
        "messages": [],
    }

    result = agent.run(state)
    assert result.get("error_message") is not None
