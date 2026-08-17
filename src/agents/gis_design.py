"""design 方案 Agent — 技术方案（数据源/坐标系/算子/出图）"""

from src.agents.base import BaseAgent
from src.agents.gis_common import TECH_PLAN_PATTERN, extract_block
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer


class DesignAgent(BaseAgent):
    """GIS 技术方案 Agent（SPEC 4.2）"""

    def __init__(self) -> None:
        super().__init__(name="design", tools=[])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        ctx = PromptContext(
            agent_name="GIS 技术方案专家",
            gis={
                "user_request": state.get("user_request", ""),
                "task_plan": state.get("task_plan") or "（无）",
                "data_schema": state.get("data_schema") or "（无）",
            },
        )
        system_prompt = renderer.render(
            renderer.load_template("gis_design.md"), ctx.to_template_vars()
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请根据任务方案输出技术方案。"},
        ]
        content = self.llm.chat(
            messages, agent_type="design", model_id=state.get("model_preference")
        )
        if not content.strip():
            return {
                **state,
                "current_stage": "error",
                "error_message": "design Agent 返回空内容（LLM 空响应）",
            }
        return {
            **state,
            "tech_plan": extract_block(content, TECH_PLAN_PATTERN),
            "current_stage": "codegen",
            "messages": [{"from": "design", "type": "output", "content": content}],
        }
