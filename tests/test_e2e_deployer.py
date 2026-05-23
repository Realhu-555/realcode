"""端到端测试：部署 Agent"""
import pytest
from src.agents.deployer import DeployerAgent
from src.orchestrator.state import Stage


def test_deployer_produces_deploy_doc():
    """部署 Agent 产出部署说明"""
    agent = DeployerAgent()
    state = {
        "user_idea": "博客",
        "prd": "...",
        "tech_plan": "...",
        "backend_code": "```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```",
        "frontend_code": "```tsx\nfunction App() { return <div>Hello</div>; }\n```",
        "test_report": "所有检查通过",
        "ask_user": None,
        "current_stage": Stage.DEPLOYMENT,
        "messages": [],
    }

    result = agent.run(state)
    output = result.get("zip_path") or result.get("deploy_doc")

    assert output is not None, "应该产出部署文档或 zip 路径"
    assert result["current_stage"] == Stage.DONE


def test_deployer_packs_zip():
    """部署 Agent 打包项目为 zip"""
    agent = DeployerAgent()
    state = {
        "user_idea": "博客",
        "prd": "...",
        "tech_plan": "...",
        "backend_code": "print('hello')",
        "frontend_code": "console.log('hi')",
        "test_report": "通过",
        "ask_user": None,
        "current_stage": Stage.DEPLOYMENT,
        "messages": [],
    }

    result = agent.run(state)
    assert result["current_stage"] == Stage.DONE
    assert result.get("zip_path") is not None
