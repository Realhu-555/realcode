"""GisToolAgent — 工具调用循环（设计文档 6 节）

LLM 通过 function calling 操作 GisEngine，每个工具调用的 (工具名, 参数, 返回) 落轨迹。
终止条件：finish 工具 / 无工具调用 / 步数上限。
"""

from __future__ import annotations

import json

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

    def run(self, user_request: str, data_file: str | None = None) -> dict:
        """执行一次 GIS 助手会话，返回轨迹与结果

        Returns:
            {
              "final": 最终答复,
              "outputs": 声明的产物,
              "trajectory": [{step, tool, args, result}],
              "steps": 实际步数,
              "timed_out": 是否达到步数上限,
            }
        """
        user_content = user_request
        if data_file and self.engine._layer is not None:
            user_content = (
                f"??????????????: {data_file}??"
                f"?? inspect_data ???????????????????\n\n?????{user_request}"
            )
        elif data_file:
            user_content = (
                f"??????: {data_file}???? load_data ???? inspect_data ???\n\n?????{user_request}"
            )

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        trajectory: list[dict] = []
        last_result: dict = {}

        for step in range(1, self.max_steps + 1):
            resp = self.llm.chat_with_tools(
                messages, TOOL_SCHEMAS, agent_type=self.agent_type, model_id=self.model_id
            )
            content = resp.get("content")
            tool_calls = resp.get("tool_calls") or []
            if not tool_calls:
                messages.append({"role": "assistant", "content": content or ""})
                return self._wrap(trajectory, step, final=content or "", outputs=[], last=last_result)

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
                return self._wrap(
                    trajectory, step, final=last_result.get("explanation") or "", outputs=last_result.get("outputs") or [], last=last_result
                )

        return self._wrap(trajectory, self.max_steps, final="", outputs=[], last=last_result, timed_out=True)

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
