"""后端开发 Agent"""

from src.agents.base import BaseAgent
from src.llm.prompts.backend import BACKEND_PROMPT
from src.llm.provider import LLMProvider


class BackendAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="backend", system_prompt=BACKEND_PROMPT)
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        tech_plan = state.get("tech_plan")
        if not tech_plan:
            return {
                **state,
                "error_message": "缺少技术方案，无法生成后端代码",
                "current_stage": "error",
            }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"请根据以下技术方案生成后端代码：\n\n{tech_plan}"},
        ]

        response = self.llm.chat(messages, agent_type="backend")

        return {
            **state,
            "backend_code": response,
            "current_stage": "testing",
            "messages": state.get("messages", [])
            + [
                {
                    "from": "backend",
                    "to": "tester",
                    "type": "output",
                    "content": response,
                }
            ],
        }
