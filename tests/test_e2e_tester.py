"""端到端测试：测试 Agent"""

from src.agents.tester import TesterAgent
from src.orchestrator.state import Stage

TECH_PLAN = """---TECH_PLAN_START---
## API 设计

### 文章
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/posts | 获取文章列表 |
| POST | /api/posts | 创建文章 |

## 数据库设计
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL
);
```

## 页面结构
- **首页**：文章列表
- **文章详情页**：阅读文章
---TECH_PLAN_END---"""


BACKEND_CODE = """---BACKEND_START---
### main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
@app.get("/health")
def health():
    return {"status": "ok"}
@app.get("/api/posts")
def list_posts():
    return {"items": []}
@app.post("/api/posts")
def create_post():
    return {"id": 1, "title": "test"}
```
---BACKEND_END---"""


FRONTEND_CODE = """---FRONTEND_START---
### src/App.tsx
```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
```
---FRONTEND_END---"""


def test_tester_produces_report():
    """测试 Agent 审查代码并产出测试报告"""
    agent = TesterAgent()
    state = {
        "user_idea": "博客",
        "prd": "...",
        "tech_plan": TECH_PLAN,
        "backend_code": BACKEND_CODE,
        "frontend_code": FRONTEND_CODE,
        "ask_user": None,
        "current_stage": Stage.TESTING,
        "messages": [],
    }

    result = agent.run(state)
    report = result.get("test_report")

    assert report is not None, "应该产出测试报告"
    assert "TEST_REPORT_START" in report or "审查" in report or "测试" in report
    assert result["current_stage"] == Stage.DEPLOYMENT


def test_tester_handles_missing_code():
    """无代码时返回错误"""
    agent = TesterAgent()
    state = {
        "user_idea": "",
        "prd": None,
        "tech_plan": None,
        "backend_code": None,
        "frontend_code": None,
        "ask_user": None,
        "current_stage": Stage.TESTING,
        "messages": [],
    }

    result = agent.run(state)
    assert result.get("error_message") is not None
