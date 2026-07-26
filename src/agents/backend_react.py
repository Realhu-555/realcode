"""后端开发 Agent - ReAct 模式"""

from src.agents.react import ReActAgent
from src.agents.tools import create_default_tools
from src.orchestrator.memory import MemoryType
from src.orchestrator.state import (
    add_memory,
    create_output_artifact,
    extract_upstream_content,
)


class BackendReActAgent(ReActAgent):
    """后端开发 Agent，使用 ReAct 模式"""

    def __init__(self) -> None:
        tools = create_default_tools()
        super().__init__(name="backend", tools=tools, max_steps=15)

    def run(self, state: dict) -> dict:
        """执行后端开发任务"""
        tech_plan = state.get("tech_plan")
        if not tech_plan:
            return {
                **state,
                "error_message": "缺少技术方案，无法生成后端代码",
                "current_stage": "error",
            }

        tech_plan_content = extract_upstream_content(tech_plan)

        # 构建任务描述
        task = f"""根据以下技术方案生成后端代码：

{tech_plan_content}

请使用工具完成以下工作：
1. 使用 file_write 创建 main.py（FastAPI 入口）
2. 使用 file_write 创建 models.py（数据库模型）
3. 使用 file_write 创建 schemas.py（Pydantic 模型）
4. 使用 file_write 创建 database.py（数据库连接）
5. 使用 terminal 执行语法检查"""

        # 调用父类的 run 方法执行 ReAct 循环
        result = super().run(state, task)

        # 处理 bug 修复模式
        bugs = state.get("bugs") or []
        backend_bugs = [b for b in bugs if b.get("target") == "backend"]

        # 更新版本号
        current_version = 1
        if state.get("backend_code") and isinstance(state["backend_code"], dict):
            current_version = state["backend_code"].get("version", 1) + 1

        backend_code_artifact = create_output_artifact(
            content=result.get("final_answer", ""),
            status="revised" if backend_bugs else "draft",
            version=current_version,
        )

        # 从 bugs 列表中移除已修复的 backend bug
        fixed_bug_ids = {bug["id"] for bug in backend_bugs}
        remaining_bugs = [b for b in bugs if b["id"] not in fixed_bug_ids]

        # 记录到短期记忆
        memory_entry = (
            f"后端代码已修复 bug: {[b['id'] for b in backend_bugs]}"
            if backend_bugs
            else "后端代码已生成"
        )

        updated_state = add_memory(
            result,
            content=memory_entry,
            memory_type=MemoryType.CONTEXT,
            source="backend",
            stage="backend",
        )

        return {
            **updated_state,
            "backend_code": backend_code_artifact,
            "bugs": remaining_bugs,
            "current_stage": "testing",
        }
