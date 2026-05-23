"""端到端完整流程测试：Requirement → Architect"""
import pytest
from src.agents.requirement import RequirementAgent
from src.agents.architect import ArchitectAgent
from src.orchestrator.state import Stage


def _run_requirement_with_clarification(state: dict, max_rounds: int = 6) -> dict:
    """运行需求分析，自动处理多轮追问"""
    result = state
    answers = [
        "公开的博客网站，所有人都可以评论，不需要登录也能发文章",
        "文章列表展示标题和摘要，每篇文章可以选多个标签，按时间排序",
        "每篇文章有独立页面，底部有评论区，游客可以留言",
        "后端用 Python，前端用 HTML+CSS+JS，部署到云服务器",
        "不需要其他特殊功能了，就这些核心需求",
        "就这些，够了",
    ]
    for i in range(max_rounds):
        agent = RequirementAgent()
        result = agent.run(result)
        if not result.get("ask_user"):
            break
        answer = answers[i] if i < len(answers) else "不需要，就这些核心功能够了"
        result = {
            **result,
            "ask_user": None,
            "messages": result["messages"] + [{
                "from": "user", "to": "requirement",
                "type": "answer", "content": answer,
            }],
        }
    return result


def test_full_flow_requirement_to_architect():
    """完整流程：用户想法 → PRD → 技术方案"""
    state = {
        "user_idea": "我要做一个个人博客，能写文章、按标签分类、有评论区",
        "prd": None,
        "tech_plan": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }

    result = _run_requirement_with_clarification(state)

    prd = result.get("prd")
    assert prd is not None, "RequirementAgent 应该产出 PRD"
    assert len(prd) > 50, "PRD 内容不能太短"

    # Step 2: 架构设计
    arch_agent = ArchitectAgent()
    arch_state = {
        **result,
        "current_stage": Stage.ARCHITECTURE,
    }

    arch_result = arch_agent.run(arch_state)
    tech_plan = arch_result.get("tech_plan")

    assert tech_plan is not None, "ArchitectAgent 应该产出技术方案"
    assert len(tech_plan) > 50, "技术方案内容不能太短"
    assert arch_result["current_stage"] == Stage.BACKEND


def test_full_flow_with_interactive_clarification():
    """多轮交互完整流程：模糊想法 → 追问 → PRD → 技术方案"""
    req_agent = RequirementAgent()
    req2 = RequirementAgent()

    # Round 1: 模糊输入 → 追问
    state1 = {
        "user_idea": "帮我做一个任务管理工具",
        "prd": None,
        "tech_plan": None,
        "ask_user": None,
        "current_stage": Stage.REQUIREMENT,
        "messages": [],
    }
    r1 = req_agent.run(state1)

    if r1.get("ask_user"):
        # Round 2: 回答追问 → 可能追问或 PRD
        state2 = {
            **r1,
            "ask_user": None,
            "messages": r1["messages"] + [{
                "from": "user", "to": "requirement", "type": "answer",
                "content": "给项目团队用的，要能创建任务、指派成员、拖拽改状态"
            }]
        }
        r2 = req2.run(state2)

        if r2.get("ask_user"):
            # Round 3: 继续回答
            req3 = RequirementAgent()
            state3 = {
                **r2,
                "ask_user": None,
                "messages": r2["messages"] + [{
                    "from": "user", "to": "requirement", "type": "answer",
                    "content": "不需要登录，5人的小组，状态分为待办/进行中/已完成"
                }]
            }
            final = req3.run(state3)
        else:
            final = r2
    else:
        final = r1

    prd = final.get("prd")
    assert prd is not None, "多轮对话后应该产出 PRD"

    # 传给架构师
    arch = ArchitectAgent()
    arch_result = arch.run({
        **final,
        "current_stage": Stage.ARCHITECTURE,
    })

    tech_plan = arch_result.get("tech_plan")
    assert tech_plan is not None
    assert len(tech_plan) > 50, "技术方案内容不能太短"
