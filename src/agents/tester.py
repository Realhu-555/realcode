"""测试 Agent"""
from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.llm.prompts.tester import TESTER_PROMPT


class TesterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="tester", system_prompt=TESTER_PROMPT)
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        backend = state.get("backend_code")
        frontend = state.get("frontend_code")

        if not backend and not frontend:
            return {
                **state,
                "error_message": "没有代码可供测试",
                "current_stage": "error",
            }

        parts = []
        if state.get("tech_plan"):
            parts.append(f"## 技术方案\n{state['tech_plan']}")
        if backend:
            parts.append(f"## 后端代码\n{backend}")
        if frontend:
            parts.append(f"## 前端代码\n{frontend}")

        user_message = "请审查以下代码并生成测试报告：\n\n" + "\n\n".join(parts)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.llm.chat(messages, agent_type="tester")

        return {
            **state,
            "test_report": response,
            "current_stage": "deployment",
            "messages": state.get("messages", []) + [{
                "from": "tester",
                "to": "deployer",
                "type": "output",
                "content": response,
            }],
        }
