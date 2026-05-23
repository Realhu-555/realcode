"""架构师 Agent"""
from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.llm.prompts.architect import ARCHITECT_PROMPT


class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="architect", system_prompt=ARCHITECT_PROMPT)
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        prd = state.get("prd")
        if not prd:
            return {
                **state,
                "error_message": "缺少 PRD 文档，无法进行架构设计",
                "current_stage": "error",
            }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"请根据以下 PRD 设计技术方案：\n\n{prd}"},
        ]

        response = self.llm.chat(messages, agent_type="architect")

        return {
            **state,
            "tech_plan": response,
            "current_stage": "backend",
            "messages": state.get("messages", []) + [{
                "from": "architect",
                "to": "backend",
                "type": "output",
                "content": response,
            }],
        }
