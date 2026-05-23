"""端到端测试：架构师 Agent"""
import pytest
from src.agents.architect import ArchitectAgent
from src.orchestrator.state import Stage


def test_architect_produces_tech_plan():
    """给定 PRD，架构师产出技术方案"""
    agent = ArchitectAgent()
    state = {
        "user_idea": "个人博客",
        "prd": """---PRD_START---
## 产品概述
一个个人博客系统，支持文章发布、标签分类和评论功能。

## 目标用户
- 博主：需要发布和管理文章
- 读者：浏览文章并发表评论

## 核心功能（按优先级排列）
1. 文章管理：创建、编辑、删除文章，支持 Markdown 编辑（优先级：高）
2. 标签分类：为文章添加标签，按标签筛选文章（优先级：高）
3. 评论系统：读者可以对文章发表评论（优先级：中）
4. 关于页面：展示博主个人信息（优先级：低）

## 页面结构
- **首页**
  - 包含元素：文章列表、标签云
  - 用户操作：浏览文章、按标签筛选
- **文章详情页**
  - 包含元素：文章内容、评论区
  - 用户操作：阅读、发表评论
- **管理后台**
  - 包含元素：文章编辑器、文章列表管理
  - 用户操作：创建/编辑/删除文章
- **关于页**
  - 包含元素：博主信息
  - 用户操作：浏览

## 数据模型概要
- **文章**：标题、内容、标签、创建时间
  - 关键字段：id, title, content, tags, created_at, updated_at
- **评论**：关联文章、作者名、内容、时间
  - 关键字段：id, post_id, author, content, created_at

## 非功能需求
- 页面加载时间 < 2 秒
- 支持移动端响应式布局
---PRD_END---""",
        "ask_user": None,
        "current_stage": Stage.ARCHITECTURE,
        "messages": [],
    }

    result = agent.run(state)
    tech_plan = result.get("tech_plan")

    assert tech_plan is not None
    assert "TECH_PLAN_START" in tech_plan or "技术选型" in tech_plan
    assert "API" in tech_plan or "API" in tech_plan or "api" in tech_plan
    assert "数据库" in tech_plan or "CREATE TABLE" in tech_plan
    assert result["current_stage"] == Stage.BACKEND


def test_architect_handles_missing_prd():
    """PRD 为空时抛异常或返回错误"""
    agent = ArchitectAgent()
    state = {
        "user_idea": "",
        "prd": None,
        "ask_user": None,
        "current_stage": Stage.ARCHITECTURE,
        "messages": [],
    }

    result = agent.run(state)
    # 应该返回错误信息
    assert result.get("error_message") is not None or result.get("tech_plan") is None
