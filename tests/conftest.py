"""共享 fixtures"""

import pytest
from src.orchestrator.state import ContentStage
from src.sandbox.executor import SandboxExecutor


@pytest.fixture
def sandbox():
    """创建已初始化的沙箱"""
    sb = SandboxExecutor()
    sb.create("test_project")
    yield sb
    sb.cleanup()


@pytest.fixture
def base_content_state():
    """基础 ContentProjectState — 用户通过表单输入"""
    return {
        "input_mode": "form",
        "product_name": "RAG 智能问答系统",
        "product_description": "企业级知识库问答助手，上传文档即用",
        "target_users": "技术团队负责人、CTO",
        "key_selling_points": ["多格式文档支持", "引用可追溯", "安全防护"],
        "brand_tone": "专业",
        "competitors": ["ChatPDF", "AnythingLLM"],
        "user_idea": "",
        "image_urls": [],
        "strategy": None,
        "gzh_content": None,
        "zhihu_content": None,
        "xhs_content": None,
        "review_report": None,
        "current_stage": ContentStage.STRATEGY,
        "error_message": None,
        "ask_user": None,
        "messages": [],
        "brand_profile_id": None,
    }


@pytest.fixture
def base_state_after_strategy(base_content_state):
    """策略 Agent 产出后的 state"""
    return {
        **base_content_state,
        "strategy": "## 内容策略\n\n### 目标用户\n技术团队负责人（30-45岁）\n\n### 各渠道策略\n- 公众号：深度解读技术趋势\n- 知乎：技术选型对比\n- 小红书：场景化种草",
        "current_stage": ContentStage.CONFIRMING,
        "messages": [
            {"from": "celve", "type": "output", "content": "策略内容"}
        ],
    }


@pytest.fixture
def base_state_after_generation(base_state_after_strategy):
    """三渠道生成完成后的 state"""
    return {
        **base_state_after_strategy,
        "gzh_content": "## 公众号长文内容\n\n这是测试内容。",
        "zhihu_content": "## 知乎专业回答\n\n这是测试回答。",
        "xhs_content": "## 小红书种草笔记\n\n轻松分享。\n\n#标签1 #标签2",
        "current_stage": ContentStage.GENERATING,
    }
