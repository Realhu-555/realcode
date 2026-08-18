"""GisToolAgent — 工具调用循环（设计文档 6 节）

LLM 通过 function calling 操作 GisEngine，每个工具调用的 (工具名, 参数, 返回) 落轨迹。
终止条件：finish 工具 / 无工具调用 / 步数上限。
"""

from __future__ import annotations

import json
from pathlib import Path

from src.gis_toolkit.engine import GisEngine, GisEngineError, _jsonable
from src.gis_toolkit.schemas import TOOL_SCHEMAS
from src.llm.provider import LLMProvider

SYSTEM_PROMPT = """你是 GIS 智能助手，通过工具调用操作 GIS 引擎，完成用户的 GIS 分析任务。

工作方式：
1. 先用 load_data 加载用户数据，再用 inspect_data 查看字段、CRS、范围后再决策；
2. 每个工具执行后都会返回当前图层摘要（行数/字段/CRS/几何类型），据此决定下一步；
3. 出图用 choropleth（分级设色）/ scatter_plot（散点）；统计用 summarize；空间操作用 buffer / overlay；
4. 产物一律写相对文件名（如 choropleth.png / summary.csv），引擎会保存到输出目录；
5. 工具返回 status=error 时，根据 error 信息修正参数后重试，不要重复同样的错误；
6. 全部产物完成后再调用 finish(outputs=[...], summary="...") 声明产出，结束任务。

约束：
- 只能使用工具返回的信息，禁止编造数据或字段；
- 不要臆造数据文件路径，只能使用用户提供或已存在的文件；
- 步数有限，避免无意义的重复调用。"""


class GisToolAgent:
    """GIS 工具调用 Agent：思考 → 调工具 → 观察，直到 finish 或达到步数上限"""

    def __init__(
        self,
        engine: GisEngine | None = None,
        max_steps: int = 12,
        agent_type: str = "gis_assistant",
        model_id: str | None = None,
    ) -> None:
        self.engine = engine or GisEngine()
        self.llm = LLMProvider()
        self.max_steps = max_steps
        self.agent_type = agent_type
        self.model_id = model_id

    @staticmethod
    def _demo_file_hint() -> str:
        """无显式数据文件时，提示引擎工作目录内可用的演示数据"""
        demo_dir = Path("data/gis_demo")
        if not demo_dir.is_dir():
            return ""
        allowed = {".csv", ".geojson", ".json", ".zip"}
        files = sorted(
            p for p in demo_dir.iterdir() if p.is_file() and p.suffix.lower() in allowed
        )
        if not files:
            return ""
        lines = "\n".join(f"- {p.as_posix()}（演示数据集）" for p in files)
        return (
            "引擎工作目录中可用的数据文件（用户未显式提供时可直接 load_data 使用）：\n"
            + lines
        )

    def run(
        self,
        user_request: str,
        data_file: str | None = None,
        session=None,
        ltm_hint: str = "",
    ) -> dict:
        """执行一次 GIS 助手会话，返回轨迹与结果

        多轮对话：传入 session（GisSession）时复用引擎状态与对话历史；
        ltm_hint 为长期记忆检索注入的提示文本。

        Returns:
            {
              "final": 最终答复,
              "outputs": 声明的产物,
              "trajectory": [{step, tool, args, result}],
              "steps": 实际步数,
              "timed_out": 是否达到步数上限,
            }
        """
        system_content = SYSTEM_PROMPT
        demo_hint = self._demo_file_hint()
        if demo_hint:
            system_content += "\n\n" + demo_hint
        if ltm_hint:
            system_content += "\n\n" + ltm_hint

        user_content = user_request
        if data_file and self.engine._layer is not None:
            user_content = (
                f"当前已加载数据文件: {data_file}。"
                f"可先调用 inspect_data 查看字段与 CRS，再继续后续任务。\n\n用户请求: {user_request}"
            )
        elif data_file:
            user_content = (
                f"数据文件已就绪: {data_file}。请先用 load_data 加载该文件，再用 inspect_data 查看。\n\n用户请求: {user_request}"
            )

        messages: list[dict] = [{"role": "system", "content": system_content}]
        if session is not None and getattr(session, "messages", None):
            messages.extend(session.messages)
        messages.append({"role": "user", "content": user_content})

        trajectory: list[dict] = []
        last_result: dict = {}
        final = ""
        outputs: list[str] = []
        timed_out = False
        steps_used = self.max_steps

        for step in range(1, self.max_steps + 1):
            steps_used = step
            resp = self.llm.chat_with_tools(
                messages, TOOL_SCHEMAS, agent_type=self.agent_type, model_id=self.model_id
            )
            content = resp.get("content")
            tool_calls = resp.get("tool_calls") or []
            if not tool_calls:
                messages.append({"role": "assistant", "content": content or ""})
                final = content or ""
                break

            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            finished = False
            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name") or ""
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                    if not isinstance(args, dict):
                        args = {}
                except json.JSONDecodeError:
                    args = {}
                try:
                    result = self._execute(name, args)
                except GisEngineError as exc:
                    result = {"status": "error", "error": str(exc)}
                except Exception as exc:  # 引擎兜底，防止单工具异常中断整个会话
                    result = {"status": "error", "error": f"工具执行异常: {exc}"}
                trajectory.append({"step": step, "tool": name, "args": args, "result": result})
                if result.get("status") == "finished":
                    finished = True
                    last_result = result
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.get("id") or f"call_{step}_{len(trajectory)}",
                        "content": json.dumps(result, ensure_ascii=False, default=_jsonable),
                    }
                )
            if finished:
                final = last_result.get("explanation") or ""
                outputs = last_result.get("outputs") or []
                break
        else:
            timed_out = True

        if session is not None:
            session.append_round(
                messages[1:],
                user_request,
                final,
                {"steps": steps_used, "outputs": outputs, "trajectory": trajectory, "timed_out": timed_out},
            )

        return self._wrap(
            trajectory,
            steps_used,
            final=final,
            outputs=outputs,
            last=last_result,
            timed_out=timed_out,
        )

    # ── 内部 ──
    def _execute(self, name: str, args: dict) -> dict:
        """把工具调用分发给引擎实现"""
        impl = getattr(self.engine, name, None)
        if impl is None:
            raise GisEngineError(f"未知工具: {name}")
        return impl(**args)

    @staticmethod
    def _wrap(
        trajectory: list[dict],
        steps: int,
        final: str,
        outputs: list[str],
        last: dict,
        timed_out: bool = False,
    ) -> dict:
        return {
            "final": final,
            "outputs": outputs,
            "trajectory": trajectory,
            "steps": steps,
            "timed_out": timed_out,
            "last_result": last,
        }
