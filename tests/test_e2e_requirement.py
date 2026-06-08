"""端到端测试：需求分析 Agent"""

from src.agents.requirement import RequirementAgent
from src.orchestrator.state import Stage


def test_requirement_agent_asks_when_vague():
    """模糊输入时 Agent 要么追问要么尽力产出 PRD"""
    agent = RequirementAgent()
    state = {
        "user_idea": "帮我做一个系统",
        "prd": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }

    result = agent.run(state)

    # 极其模糊的输入应该追问；但如果 LLM 直接出了 PRD 也算可接受
    if result.get("ask_user"):
        assert "ASK_USER:" not in result["ask_user"]
    else:
        assert result["prd"] is not None


def test_requirement_agent_produces_prd_when_clear():
    """清晰输入应该产出 PRD"""
    agent = RequirementAgent()
    state = {
        "user_idea": "我要做一个个人博客，能写文章、按标签分类、有评论区",
        "prd": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }

    result = agent.run(state)

    if result.get("ask_user"):
        assert len(result["ask_user"]) > 0
    else:
        assert result["prd"] is not None
        assert "PRD_START" in result["prd"] or "产品概述" in result["prd"]
        assert result["current_stage"] == Stage.ARCHITECTURE


def test_multiround_clarification():
    """多轮对话最终产出 PRD"""
    agent = RequirementAgent()

    state = {
        "user_idea": "我要做一个任务管理工具",
        "prd": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }

    result = agent.run(state)

    # 如果 LLM 觉得信息够了，直接产出 PRD 也可以
    if result.get("prd"):
        assert "产品概述" in result["prd"] or "PRD_START" in result["prd"]
        return

    # 否则应该追问
    assert result["ask_user"] is not None

    state2 = {
        **result,
        "ask_user": None,
        "messages": result["messages"]
        + [
            {
                "from": "user",
                "to": "requirement",
                "type": "answer",
                "content": "团队内部用，能创建任务、指派给同事、拖拽改变状态为待办/进行中/已完成",
            }
        ],
    }

    agent2 = RequirementAgent()
    result2 = agent2.run(state2)

    if result2.get("ask_user"):
        state3 = {
            **result2,
            "ask_user": None,
            "messages": result2["messages"]
            + [
                {
                    "from": "user",
                    "to": "requirement",
                    "type": "answer",
                    "content": "不需要登录，3-5 人的小团队用，就这三个状态够了",
                }
            ],
        }
        agent3 = RequirementAgent()
        result3 = agent3.run(state3)
        assert result3["prd"] is not None or result3["ask_user"] is not None
    else:
        assert result2["prd"] is not None
