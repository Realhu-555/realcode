"""前端开发 Agent - ReAct 模式"""

from src.agents.react import ReActAgent
from src.agents.tools import create_default_tools
from src.orchestrator.memory import MemoryType
from src.orchestrator.state import (
    add_memory,
    create_output_artifact,
    extract_upstream_content,
)


class FrontendReActAgent(ReActAgent):
    """前端开发 Agent，使用 ReAct 模式"""

    def __init__(self) -> None:
        tools = create_default_tools()
        super().__init__(name="frontend", tools=tools, max_steps=15)

    def run(self, state: dict) -> dict:
        """执行前端开发任务"""
        tech_plan = state.get("tech_plan")
        if not tech_plan:
            return {
                **state,
                "error_message": "缺少技术方案，无法生成前端代码",
                "current_stage": "error",
            }

        tech_plan_content = extract_upstream_content(tech_plan)

        task = f"""根据以下技术方案生成前端代码：

{tech_plan_content}

请使用工具完成以下工作：
1. 使用 file_write 创建 package.json
2. 使用 file_write 创建 src/App.tsx
3. 使用 file_write 创建 src/main.tsx
4. 使用 terminal 执行 npm run build 检查"""

        result = super().run(state, task)

        # 更新版本号
        current_version = 1
        if state.get("frontend_code") and isinstance(state["frontend_code"], dict):
            current_version = state["frontend_code"].get("version", 1) + 1

        frontend_code_artifact = create_output_artifact(
            content=result.get("final_answer", ""),
            status="revised" if (state.get("bugs") or []) else "draft",
            version=current_version,
        )

        updated_state = add_memory(
            result,
            content="前端代码已生成",
            memory_type=MemoryType.CONTEXT,
            source="frontend",
            stage="frontend",
        )

        return {
            **updated_state,
            "frontend_code": frontend_code_artifact,
            "current_stage": "testing",
        }
