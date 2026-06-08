"""前端开发 Agent"""

from src.agents.base import BaseAgent
from src.llm.prompts.frontend import FRONTEND_PROMPT
from src.llm.provider import LLMProvider


class FrontendAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="frontend", system_prompt=FRONTEND_PROMPT)
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        tech_plan = state.get("tech_plan")
        if not tech_plan:
            return {
                **state,
                "error_message": "缺少技术方案，无法生成前端代码",
                "current_stage": "error",
            }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"请根据以下技术方案生成前端代码：\n\n{tech_plan}"},
        ]

        response = self.llm.chat(messages, agent_type="frontend")

        return {
            **state,
            "frontend_code": response,
            "current_stage": "testing",
            "messages": state.get("messages", [])
            + [
                {
                    "from": "frontend",
                    "to": "tester",
                    "type": "output",
                    "content": response,
                }
            ],
        }
