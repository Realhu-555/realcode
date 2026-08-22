"""GisToolAgent — 工具调用循环（设计文档 6 节）

LLM 通过 function calling 操作 GisEngine，每个工具调用的 (工具名, 参数, 返回) 落轨迹。
终止条件：finish 工具 / 无工具调用 / 步数上限。
"""

from __future__ import annotations

import json
from pathlib import Path

from src.gis_toolkit.checker import check_outputs
from src.gis_toolkit.engine import GisEngine, GisEngineError, _jsonable
from src.gis_toolkit.schemas import TOOL_SCHEMAS
from src.llm.provider import LLMProvider

PRODUCT_TOOLS = {"choropleth", "scatter_plot", "render_map", "summarize", "export_geojson"}
COMPACT_THRESHOLD_TOKENS = 24000  # 会话历史估算 token 超过该值触发滚动摘要
HISTORY_WINDOW_MESSAGES = 40  # 发给 LLM 的最近消息条数（≈ 最近 5~10 轮）

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
        max_check_retries: int = 3,
        agent_type: str = "gis_assistant",
        model_id: str | None = None,
    ) -> None:
        self.engine = engine or GisEngine()
        self.llm = LLMProvider()
        self.max_steps = max_steps
        self.max_check_retries = max_check_retries
        self._check_failures: dict[str, int] = {}
        self.sub_agent = None  # T9：子任务执行器预留（默认 None，实现后注入）
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
        messages = self._prepare_messages(user_request, data_file, session, ltm_hint)

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
                    result = self._execute_with_check(name, args)
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
            self._maybe_roll_summary(session)

        return self._wrap(
            trajectory,
            steps_used,
            final=final,
            outputs=outputs,
            last=last_result,
            timed_out=timed_out,
        )

    def run_stream(
        self,
        user_request: str,
        data_file: str | None = None,
        session=None,
        ltm_hint: str = "",
        on_event=None,
    ) -> dict:
        """流式执行一次 GIS 助手会话，事件经 on_event 实时回调

        循环逻辑与 run 一致，差异：
        - LLM 调用使用 chat_with_tools_stream，文本增量逐 token 推送；
        - 每个工具调用/结果通过 on_event 推送，前端按到达顺序排版。

        on_event 事件：
            {"type": "text_delta", "delta": "..."}         LLM 文本增量
            {"type": "tool_call", "step": N, "tool": "...", "args": {...}}
            {"type": "tool_result", "step": N, "tool": "...", "result": {...}}
            {"type": "done", "final": "...", "outputs": [...], "steps": N, "timed_out": bool}
            {"type": "error", "error": "..."}               执行异常
        """
        messages = self._prepare_messages(user_request, data_file, session, ltm_hint)

        trajectory: list[dict] = []
        last_result: dict = {}
        final = ""
        outputs: list[str] = []
        timed_out = False
        steps_used = self.max_steps
        error: str | None = None

        for step in range(1, self.max_steps + 1):
            steps_used = step
            try:
                resp = self.llm.chat_with_tools_stream(
                    messages,
                    TOOL_SCHEMAS,
                    agent_type=self.agent_type,
                    model_id=self.model_id,
                    on_text_delta=lambda d: self._emit(
                        on_event, {"type": "text_delta", "delta": d}
                    ),
                )
            except Exception as exc:
                error = f"模型调用失败: {exc}"
                break
            content = resp.get("content")
            tool_calls = resp.get("tool_calls") or []
            if not tool_calls:
                messages.append({"role": "assistant", "content": content or ""})
                final = content or ""
                break

            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            if content and content.strip():
                self._emit(
                    on_event,
                    {"type": "tool_reason", "step": step, "reason": content.strip()},
                )
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
                self._emit(
                    on_event, {"type": "tool_call", "step": step, "tool": name, "args": args}
                )
                try:
                    result = self._execute_with_check(name, args)
                except GisEngineError as exc:
                    result = {"status": "error", "error": str(exc)}
                except Exception as exc:  # 引擎兜底，防止单工具异常中断整个会话
                    result = {"status": "error", "error": f"工具执行异常: {exc}"}
                trajectory.append({"step": step, "tool": name, "args": args, "result": result})
                self._emit(
                    on_event,
                    {"type": "tool_result", "step": step, "tool": name, "result": result},
                )
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

        if error is not None:
            self._emit(on_event, {"type": "error", "error": error})
        else:
            if session is not None:
                session.append_round(
                    messages[1:],
                    user_request,
                    final,
                    {"steps": steps_used, "outputs": outputs, "trajectory": trajectory, "timed_out": timed_out},
                )
                self._maybe_roll_summary(session)
            self._emit(
                on_event,
                {
                    "type": "done",
                    "final": final,
                    "outputs": outputs,
                    "steps": steps_used,
                    "timed_out": timed_out,
                },
            )

        return self._wrap(
            trajectory,
            steps_used,
            final=final,
            outputs=outputs,
            last=last_result,
            timed_out=timed_out,
        )

    def _prepare_messages(
        self,
        user_request: str,
        data_file: str | None,
        session,
        ltm_hint: str,
    ) -> list[dict]:
        """构造本轮 LLM 消息：system（含演示文件/长期记忆）+ 会话历史 + 用户请求"""
        system_content = SYSTEM_PROMPT
        demo_hint = self._demo_file_hint()
        if demo_hint:
            system_content += "\n\n" + demo_hint
        if session is not None and getattr(session, "summary", ""):
            system_content += f"\n\n## 历史会话摘要\n{session.summary}"
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
            messages.extend(session.messages[-HISTORY_WINDOW_MESSAGES:])
        messages.append({"role": "user", "content": user_content})
        return messages

    def _maybe_roll_summary(self, session) -> None:
        """会话历史超出 token 阈值时，用 LLM 生成滚动摘要并裁剪历史窗口"""
        est_tokens = (
            sum(len(str(m.get("content") or "")) for m in session.messages) // 3
        )
        if est_tokens <= COMPACT_THRESHOLD_TOKENS:
            return
        try:
            new_summary = self._roll_summary(session.summary, session.messages[-6:])
            if new_summary:
                session.summary = new_summary
        except Exception:
            return  # 摘要失败不阻断会话，下次再试
        session.messages = session.messages[-HISTORY_WINDOW_MESSAGES:]

    def _roll_summary(self, old_summary: str, recent: list[dict]) -> str:
        """把旧摘要与最近对话合并为新的简洁摘要"""
        prompt = [
            {
                "role": "system",
                "content": (
                    "你是 GIS 助手的会话摘要器。把旧摘要与最近对话合并为新的简洁摘要，"
                    "必须保留：已完成的产物文件名、当前图层状态、关键数值结论、用户偏好。"
                    "不超过 300 字，直接输出摘要。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"旧摘要:\n{old_summary or '（无）'}\n\n"
                    f"最近对话:\n{json.dumps(recent, ensure_ascii=False, default=str)[:6000]}"
                ),
            },
        ]
        resp = self.llm.chat(prompt, agent_type="summary", model_id=self.model_id)
        return (resp.get("content") or "").strip()

    def execute_subtask(self, task: str, context: dict | None = None) -> dict:
        """T9：子任务执行器接口预留。

        当任务复杂、需要隔离/并行/权限边界时，注入实现（如独立 checker agent、
        大数据量分析 worker）。当前默认返回 unsupported，不影响主循环。
        """
        if self.sub_agent is not None:
            return self.sub_agent(task=task, context=context or {})
        return {
            "status": "unsupported",
            "error": "子任务执行器未配置（sub_agent 为 None）",
        }

    @staticmethod
    def _emit(on_event, event: dict) -> None:
        """触发事件回调（为空时静默跳过）"""
        if on_event:
            on_event(event)

    # ── 内部 ──
    def _execute(self, name: str, args: dict) -> dict:
        """把工具调用分发给引擎实现"""
        impl = getattr(self.engine, name, None)
        if impl is None:
            raise GisEngineError(f"未知工具: {name}")
        return impl(**args)

    def _execute_with_check(self, name: str, args: dict) -> dict:
        """执行工具 + 产物校验回环。

        产生产物的工具（choropleth/scatter/render/summarize/export）执行后自动校验：
        - 校验失败 → 返回 status=error（附校验原因），让 LLM 修正参数重试；
        - 同一工具累计失败 ≥ max_check_retries 次 → 强制终止该工具，防止死循环。
        """
        result = self._execute(name, args)
        if result.get("status") != "ok" or name not in PRODUCT_TOOLS:
            return result
        errors = check_outputs(result)
        if not errors:
            self._check_failures.pop(name, None)
            return result

        self._check_failures[name] = self._check_failures.get(name, 0) + 1
        if self._check_failures[name] >= self.max_check_retries:
            self._check_failures.pop(name, None)
            return {
                "status": "error",
                "error": (
                    f"产物校验连续失败 {self.max_check_retries} 次，请停止该工具，"
                    f"检查参数或改用其他方法。校验错误: {'；'.join(errors)}"
                ),
                "check_failed": errors,
            }
        return {
            "status": "error",
            "error": f"产物校验失败，请修正参数后重试: {'；'.join(errors)}",
            "check_failed": errors,
        }

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
