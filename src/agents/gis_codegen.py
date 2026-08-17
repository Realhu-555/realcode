"""codegen 脚本 Agent — 生成 GeoPandas 脚本"""

from src.agents.base import BaseAgent
from src.agents.gis_common import SCRIPT_PATTERN, extract_block
from src.llm.provider import LLMProvider
from src.prompt.context import PromptContext
from src.prompt.renderer import renderer


class CodegenAgent(BaseAgent):
    """GIS 脚本生成 Agent（SPEC 4.3）"""

    def __init__(self) -> None:
        super().__init__(name="codegen", tools=[])
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        ctx = PromptContext(
            agent_name="GIS 脚本工程师",
            gis={
                "tech_plan": state.get("tech_plan") or "（无）",
                "data_schema": state.get("data_schema") or "（无）",
                "data_file": state.get("data_file") or "（无）",
                "rewrite_round": state.get("rewrite_round") or 0,
                "exec_log": state.get("exec_log") or "（首次生成，无执行日志）",
                "check_report": state.get("check_report") or "（首次生成，无校验反馈）",
            },
        )
        system_prompt = renderer.render(
            renderer.load_template("gis_codegen.md"), ctx.to_template_vars()
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请根据技术方案生成完整可运行的 Python 脚本。"},
        ]
        content = self.llm.chat(
            messages, agent_type="codegen", model_id=state.get("model_preference")
        )
        return {
            **state,
            "script": extract_block(content, SCRIPT_PATTERN),
            "current_stage": "exec",
            "messages": [{"from": "codegen", "type": "output", "content": content}],
        }
