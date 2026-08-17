"""checker 校验 Agent — 基于执行日志逐项核对"""

from src.agents.base import BaseAgent
from src.agents.gis_common import CHECK_REPORT_PATTERN, extract_block
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer


class CheckerAgent(BaseAgent):
    """GIS 结果校验 Agent（SPEC 4.5）"""

    def __init__(self) -> None:
        super().__init__(name="checker", tools=[])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        artifacts = state.get("artifacts") or []
        ctx = PromptContext(
            agent_name="GIS 结果校验专家",
            gis={
                "tech_plan": state.get("tech_plan") or "（无）",
                "exec_log": state.get("exec_log") or "（无执行日志）",
                "artifacts": ", ".join(artifacts) if artifacts else "（无产出文件）",
            },
        )
        system_prompt = renderer.render(
            renderer.load_template("gis_checker.md"), ctx.to_template_vars()
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请基于执行日志和产出清单输出校验报告。"},
        ]
        content = self.llm.chat(
            messages, agent_type="checker", model_id=state.get("model_preference")
        )
        if not content.strip():
            return {
                **state,
                "current_stage": "error",
                "error_message": "checker Agent 返回空内容（LLM 空响应）",
            }
        report = extract_block(content, CHECK_REPORT_PATTERN)
        return {
            **state,
            "check_report": report,
            "current_stage": "check",
            "messages": [{"from": "checker", "type": "output", "content": content}],
        }
