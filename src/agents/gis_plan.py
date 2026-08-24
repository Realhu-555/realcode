"""plan 规划 Agent — 任务拆解 + ASK_USER 追问"""

from src.agents.base import BaseAgent
from src.agents.gis_common import parse_ask_user
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer


class PlanAgent(BaseAgent):
    """GIS 任务规划 Agent（SPEC 4.1）"""

    def __init__(self) -> None:
        super().__init__(name="plan", tools=[])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        ctx = PromptContext(
            agent_name="GIS 任务规划专家",
            gis={
                "user_request": state.get("user_request", ""),
                "data_schema": state.get("data_schema") or "（无）",
            },
        )
        system_prompt = renderer.render(
            renderer.load_template("gis_plan.md"), ctx.to_template_vars()
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户需求：{state.get('user_request', '')}"},
        ]
        content = self.llm.chat(messages, agent_type="plan", model_id=state.get("model_preference"))

        question = parse_ask_user(content)
        if question:
            return {
                **state,
                "ask_user": question,
                "current_stage": "plan",
                "messages": [{"from": "plan", "type": "question", "content": question}],
            }
        return {
            **state,
            "task_plan": content,
            "ask_user": None,
            "current_stage": "design",
            "messages": [{"from": "plan", "type": "output", "content": content}],
        }
