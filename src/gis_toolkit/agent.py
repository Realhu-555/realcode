"""GisToolAgent — 工具调用循环（设计文档 6 节）

LLM 通过 function calling 操作 GisEngine，每个工具调用的 (工具名, 参数, 返回) 落轨迹。
终止条件：finish 工具 / 无工具调用 / 步数上限。
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.gis_toolkit import context as ctx
from src.gis_toolkit.approval import ApprovalGate
from src.gis_toolkit.auditor import AuditReport, ResultAuditor
from src.gis_toolkit.checker import check_outputs
from src.gis_toolkit.engine import GisEngine, GisEngineError, _jsonable
from src.gis_toolkit.schemas import TOOL_SCHEMAS
from src.gis_toolkit.validate import validate_final_numbers
from src.llm.provider import LLMProvider
from src.utils.logger import agent_logger

PRODUCT_TOOLS = {"choropleth", "scatter_plot", "render_map", "summarize", "export_geojson"}
HISTORY_WINDOW_MESSAGES = 40  # 未压缩时发给 LLM 的最近消息条数（≈ 最近 5~10 轮）
DEFAULT_FALLBACK_CONTEXT_WINDOW = 128000  # 模型未声明 context_window 时的兜底窗口

SYSTEM_PROMPT = """你是 GIS 智能助手，通过工具调用操作 GIS 引擎，完成用户的 GIS 分析任务。

工作方式：
1. 先用 load_data 加载用户数据，再用 inspect_data 查看字段、CRS、范围后再决策；
2. 每个工具执行后都会返回当前图层摘要（行数/字段/CRS/几何类型），据此决定下一步；
3. 出图用 choropleth（分级设色）/ scatter_plot（散点）；统计用 summarize；空间操作用 buffer / overlay；
4. 产物一律写相对文件名（如 choropleth.png / summary.csv），引擎会保存到输出目录；
5. 工具返回 status=error 时，根据 error 信息修正参数后重试，不要重复同样的错误；
6. 当前图层在会话中持续保留，不要重复 load_data 相同数据；确需其他数据时才重新加载；
7. 任务全部完成后，最后一步必须调用 finish(outputs=[...], summary="...") 收尾并汇报，禁止不调 finish 直接结束；
8. finish 的 summary 就是给用户的最终汇报，必须包含：
   - 做了什么（关键步骤）；
   - 具体结论和数字（分组统计值、Top 名单、趋势、异常点）——数字必须来自工具返回，禁止编造；
   - 产物清单（文件名）；
   - 若图表/统计工具返回提示存在缺失数据（如"无数据省份"），必须如实说明缺失情况，不得声称全部覆盖；
   - 只引用工具返回（含 stats/输出信息）里明确给出的数值；不要凭样例行或常识推测写"约 xx / 最高到 xx / 几倍"，
     确需极值/最值/汇总时先调用 field_statistics / summarize 拿到返回值再写；
   不要只说"数据已导出/详见 CSV"，把核心数字直接写进汇报。

约束：
- 只能使用工具返回的信息，禁止编造数据或字段；
- 不要臆造数据文件路径，只能使用用户提供或已存在的文件；
- 步数有限（12 步），先规划顺序：加载 → 查看 → 分析/出图 → 汇总 → finish，避免无意义的重复调用。"""


class GisToolAgent:
    """GIS 工具调用 Agent：思考 → 调工具 → 观察，直到 finish 或达到步数上限"""

    def __init__(
        self,
        engine: GisEngine | None = None,
        max_steps: int = 12,
        max_check_retries: int = 3,
        approval_gate: ApprovalGate | None = None,
        agent_type: str = "gis_assistant",
        model_id: str | None = None,
        # ── auto-compact（C1-C3）──
        context_window: int | None = None,  # 会话模型窗口；None 时从模型注册表自动取
        compact_trigger_pct: float = ctx.DEFAULT_TRIGGER_PCT,
        compact_target_pct: float = ctx.DEFAULT_TARGET_PCT,
        compact_min_rounds: int = ctx.DEFAULT_MIN_ROUNDS,
        compact_max_reduction_ratio: float = ctx.DEFAULT_MAX_REDUCTION_RATIO,
        compact_model: str | None = None,  # 独立压缩模型 id；None = 随主模型压缩
        compact_source_cap_chars: int = ctx.DEFAULT_SOURCE_CAP_CHARS,
        compact_window_after: int = ctx.DEFAULT_WINDOW_AFTER,
        # ── auto-compact（C4：Loop 内压缩，tail-keep）──
        compact_loop_tail: int = ctx.DEFAULT_LOOP_KEEP_TAIL,
        compact_loop_max: int = ctx.DEFAULT_LOOP_MAX_COMPACTS,
        compact_loop_min_messages: int = ctx.DEFAULT_LOOP_MIN_MESSAGES,
        # ── auto-compact（C5：压缩摘要同步长期记忆，跨会话召回）──
        on_compact_summary: Callable[[str], None] | None = None,
    ) -> None:
        self.engine = engine or GisEngine()
        self.llm = LLMProvider()
        self.max_steps = max_steps
        self.max_check_retries = max_check_retries
        self._check_failures: dict[str, int] = {}
        self.sub_agent = None  # T9：子任务执行器预留（默认 None，实现后注入）
        self.approval_gate = approval_gate  # HITL：危险操作审批门
        self.on_event_callback = None  # run_stream 设置，供审批事件推送
        self.agent_type = agent_type
        self.model_id = model_id
        self.logger = agent_logger
        self.context_window = context_window
        self.compact_trigger_pct = compact_trigger_pct
        self.compact_target_pct = compact_target_pct
        self.compact_min_rounds = compact_min_rounds
        self.compact_max_reduction_ratio = compact_max_reduction_ratio
        self.compact_model = compact_model
        self.compact_source_cap_chars = compact_source_cap_chars
        self.compact_window_after = compact_window_after
        self.compact_loop_tail = compact_loop_tail
        self.compact_loop_max = compact_loop_max
        self.compact_loop_min_messages = compact_loop_min_messages
        self.on_compact_summary = on_compact_summary

    @staticmethod
    def _demo_file_hint() -> str:
        """无显式数据文件时，提示引擎工作目录内可用的演示数据"""
        demo_dir = Path("data/gis_demo")
        if not demo_dir.is_dir():
            return ""
        allowed = {".csv", ".geojson", ".json", ".zip"}
        files = sorted(p for p in demo_dir.iterdir() if p.is_file() and p.suffix.lower() in allowed)
        if not files:
            return ""
        lines = "\n".join(f"- {p.as_posix()}（演示数据集）" for p in files)
        return "引擎工作目录中可用的数据文件（用户未显式提供时可直接 load_data 使用）：\n" + lines

    @staticmethod
    def _ending_fallback(outputs: list[str], trajectory: list[dict]) -> str:
        """任务未正常收尾（超时 / 未调用 finish）时的兜底汇报，避免空回复"""
        ok_steps = [t for t in trajectory if (t.get("result") or {}).get("status") == "ok"]
        parts: list[str] = []
        if ok_steps:
            names = ", ".join(dict.fromkeys(str(t["tool"]) for t in ok_steps))
            parts.append(f"本次共执行 {len(ok_steps)} 步工具调用（{names}）。")
        if outputs:
            parts.append("已生成产物：" + ", ".join(outputs))
        if not parts:
            parts.append("任务未完成（未生成可下载产物），请补充说明后重试。")
        return " ".join(parts)

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
        loop_compacts = 0  # C4：本 run 内已执行的 Loop 压缩次数（上限 compact_loop_max）

        for step in range(1, self.max_steps + 1):
            steps_used = step
            # C4：单 run 内累积步骤逼近窗口阈值时，压缩更早步骤（tail-keep + 恢复块）
            if loop_compacts < self.compact_loop_max:
                ret = self._maybe_compact_loop(messages, user_request, step - 1, loop_compacts)
                if ret is not None:
                    messages, loop_compacts = ret
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
                self.logger.info(
                    "tool_call",
                    extra={
                        "step": step,
                        "tool": name,
                        "status": result.get("status"),
                        "rows": (result.get("layer") or {}).get("rows"),
                    },
                )
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

        if not final.strip():
            final = self._ending_fallback(outputs, trajectory)

        final, outputs, audit_report = self._audit_correction(
            user_request, final, outputs, trajectory, messages
        )
        if session is not None:
            session.append_round(
                messages[1:],
                user_request,
                final,
                {
                    "steps": steps_used,
                    "outputs": outputs,
                    "trajectory": trajectory,
                    "timed_out": timed_out,
                },
            )
            self._maybe_compact(session)
        self._save_trace(user_request, final, outputs, trajectory, audit_report=audit_report)

        return self._wrap(
            trajectory,
            steps_used,
            final=final,
            outputs=outputs,
            last=last_result,
            timed_out=timed_out,
            audit_report=audit_report,
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
            {"type": "approval_request", ...}               危险操作审批请求（HITL）
            {"type": "done", "final": "...", "outputs": [...], "steps": N, "timed_out": bool}
            {"type": "error", "error": "..."}               执行异常
        """
        self.on_event_callback = on_event
        messages = self._prepare_messages(user_request, data_file, session, ltm_hint)

        trajectory: list[dict] = []
        last_result: dict = {}
        final = ""
        outputs: list[str] = []
        timed_out = False
        steps_used = self.max_steps
        error: str | None = None
        audit_report: dict | None = None
        loop_compacts = 0  # C4：本 run 内已执行的 Loop 压缩次数（上限 compact_loop_max）

        for step in range(1, self.max_steps + 1):
            steps_used = step
            # C4：单 run 内累积步骤逼近窗口阈值时，压缩更早步骤（tail-keep + 恢复块）
            if loop_compacts < self.compact_loop_max:
                ret = self._maybe_compact_loop(messages, user_request, step - 1, loop_compacts)
                if ret is not None:
                    messages, loop_compacts = ret
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

        if not final.strip():
            final = self._ending_fallback(outputs, trajectory)

        if error is not None:
            self._emit(on_event, {"type": "error", "error": error})
        else:
            if not final.strip():
                final = self._ending_fallback(outputs, trajectory)
            final, outputs, audit_report = self._audit_correction(
                user_request, final, outputs, trajectory, messages
            )
            if session is not None:
                session.append_round(
                    messages[1:],
                    user_request,
                    final,
                    {
                        "steps": steps_used,
                        "outputs": outputs,
                        "trajectory": trajectory,
                        "timed_out": timed_out,
                    },
                )
                self._maybe_compact(session)
            self._save_trace(user_request, final, outputs, trajectory, audit_report=audit_report)
            self._emit(
                on_event,
                {
                    "type": "done",
                    "final": final,
                    "outputs": outputs,
                    "steps": steps_used,
                    "timed_out": timed_out,
                    "audit_report": audit_report,
                },
            )

        return self._wrap(
            trajectory,
            steps_used,
            final=final,
            outputs=outputs,
            last=last_result,
            timed_out=timed_out,
            audit_report=audit_report,
        )

    def _audit_correction(
        self,
        user_request: str,
        final: str,
        outputs: list[str],
        trajectory: list[dict],
        messages: list[dict],
    ) -> tuple[str, list[str], dict | None]:
        """结果审核（L1 规则 + L2 审核器），FAIL 时最多 2 轮修正 final。

        设计依据：docs/GIS-智能助手-结果审核模块设计文档.md 5.3 / 6.3 / 6.4。
        - L1=PASS（数字全部可溯源）→ 不跑 L2，返回 audit_report=None（无打扰）；
        - 无产物 → 跳过 L2，仅按 L1 记录；
        - L1=WARN/FAIL 且有产物 → 跑 L2；L2=FAIL → 带审核意见让主 Agent 只重写
          final（重新调 finish，不重跑工具），最多 2 轮。
        """
        l1 = validate_final_numbers(final, trajectory)
        if l1["verdict"] == "PASS":
            return final, outputs, None

        auditor = ResultAuditor(self.llm, max_rounds=2)
        report: AuditReport | None = (
            auditor.audit(user_request, final, trajectory, None, outputs) if outputs else None
        )
        verdict = report.verdict if report is not None else l1["verdict"]
        rounds = 0
        while verdict == "FAIL" and rounds < 2 and outputs:
            rounds += 1
            if report is not None:
                advice = "\n".join(report.suggestions or report.reasons)
            else:
                advice = "\n".join(i["reason"] for i in l1["issues"])
            correction_msg = {
                "role": "system",
                "content": (
                    "【结果审核未通过】你上一条 final 汇报存在数据错误。"
                    "请对照最近一次工具返回中的真实数据，仅重新调用 finish 工具修正"
                    "explanation 与 outputs（不要重跑其他工具）。审核意见：\n"
                    f"{advice}"
                ),
            }
            try:
                resp = self.llm.chat_with_tools(
                    [*messages, correction_msg],
                    TOOL_SCHEMAS,
                    agent_type=self.agent_type,
                    model_id=self.model_id,
                )
            except Exception:
                break  # 修正调用失败，保留当前结果
            content = resp.get("content")
            new_final, new_outputs = final, outputs
            for tc in resp.get("tool_calls") or []:
                fn = tc.get("function") or {}
                if fn.get("name") != "finish":
                    continue
                try:
                    a = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    a = {}
                if a.get("explanation"):
                    new_final = str(a["explanation"])
                if a.get("outputs"):
                    new_outputs = [str(o) for o in a["outputs"]]
            if not new_final.strip() or new_final == final:
                if content and content.strip():
                    new_final = content.strip()
                else:
                    break  # LLM 未重写，终止回环
            final, outputs = new_final, new_outputs
            l1 = validate_final_numbers(final, trajectory)
            if l1["verdict"] == "PASS":
                report = AuditReport("PASS", ["修正后数字可溯源"], [], rounds)
                verdict = "PASS"
                break
            if outputs:
                report = auditor.audit(user_request, final, trajectory, None, outputs)
                verdict = report.verdict
            else:
                verdict = l1["verdict"]

        if report is None:
            audit_report = {
                "verdict": l1["verdict"],
                "reasons": [i["reason"] for i in l1["issues"]],
                "rounds_used": 0,
            }
        else:
            audit_report = report.to_dict()
            audit_report["rounds_used"] = rounds
        return final, outputs, audit_report

    def _save_trace(
        self,
        user_request: str,
        final: str,
        outputs: list[str],
        trajectory: list[dict],
        audit_report: dict | None = None,
    ) -> None:
        """T11：轨迹落盘到 data/gis_traces/（.gitignore 已忽略），失败不阻断"""
        try:
            trace_dir = Path("data/gis_traces")
            trace_dir.mkdir(parents=True, exist_ok=True)
            path = trace_dir / (
                f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}.json"
            )
            payload: dict = {
                "user_request": user_request,
                "final": final,
                "outputs": outputs,
                "trajectory": trajectory,
            }
            if audit_report is not None:
                payload["audit_report"] = audit_report
            path.write_text(
                json.dumps(payload, ensure_ascii=False, default=_jsonable),
                encoding="utf-8",
            )
        except Exception:
            pass

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
            user_content = f"数据文件已就绪: {data_file}。请先用 load_data 加载该文件，再用 inspect_data 查看。\n\n用户请求: {user_request}"

        messages: list[dict] = [{"role": "system", "content": system_content}]
        if session is not None and getattr(session, "messages", None):
            # 已压缩会话（compacted=True）收窄窗口：更早轮次已折叠进摘要
            messages.extend(
                self._history_window(session.messages, self._history_window_limit(session))
            )
        messages.append({"role": "user", "content": user_content})
        return messages

    # ── auto-compact：C1 触发 / C2 FullReplace / C3 质量护栏 ──────
    def _history_window_limit(self, session) -> int:
        """当前会话的发送窗口条数：已压缩会话收窄，避免发送包贴近窗口上限"""
        if getattr(session, "compacted", False):
            return self.compact_window_after
        return HISTORY_WINDOW_MESSAGES

    def _effective_context_window(self) -> int:
        """会话模型上下文窗口：显式参数 > 模型注册表声明 > 兜底值"""
        if self.context_window:
            return int(self.context_window)
        try:
            registry = getattr(self.llm, "registry", None)
            if registry is not None:
                model_id = self.model_id or registry.default_for(self.agent_type)
                cfg = registry.get(model_id) if model_id else None
                if cfg is not None and getattr(cfg, "context_window", None):
                    return int(cfg.context_window)
        except Exception:
            pass
        return DEFAULT_FALLBACK_CONTEXT_WINDOW

    def _estimate_send_pack(self, session) -> int:
        """估算一次发送包（system + 摘要 + 历史窗口）的 token 占用，作为 C1 触发依据"""
        limit = self._history_window_limit(session)
        window = ctx.window_messages(session.messages, limit)
        est = ctx.estimate_tokens(window)
        est += ctx.estimate_tokens_text(session.summary or "")
        est += ctx.estimate_tokens_text(SYSTEM_PROMPT)
        return est

    # ── auto-compact：C4 Loop 内压缩（tail-keep + 恢复块）──────
    def _maybe_compact_loop(
        self,
        messages: list[dict],
        user_request: str,
        steps_done: int,
        compacts_used: int,
    ) -> tuple[list[dict], int] | None:
        """C4：单次 run 内部、已累积步骤逼近窗口阈值时压缩更早步骤。

        对标 Grok intra_compaction 的 tail-keep：保留最近 compact_loop_tail 条原文
        （tool-pair-safe 切分），更早步骤整段压成摘要注入 system，并追加恢复块
        （当前图层 / 进行中任务），让长任务不再依赖放大 max_steps。

        护栏复用 C3：摘要退化拒绝 + 缩水率校验，任一不过放弃本次（返回 None），
        不阻断 loop；调用方以 compacts_used 控制单 run 压缩次数上限。
        """
        try:
            if messages is None or len(messages) < self.compact_loop_min_messages:
                return None
            if compacts_used >= self.compact_loop_max:
                return None
            trigger = ctx.trigger_threshold(
                self._effective_context_window(), self.compact_trigger_pct
            )
            if ctx.estimate_tokens(messages) < trigger:
                return None
            s = ctx.loop_compact_split(messages, self.compact_loop_tail)
            if s <= 1:
                return None  # 无可压缩的对话前缀（保留区已覆盖全部）
            old_system = messages[0].get("content") or ""
            material = ctx.messages_to_text(
                ctx.material_for_compact(messages[1:s], cap_chars=self.compact_source_cap_chars)
            ).strip()
            if not material:
                return None
            src_tokens = ctx.estimate_tokens_text(material)
            for _ in range(2):
                summary = self._summarize(material)
                if not summary or ctx.is_degenerate_summary(summary):
                    continue  # C3-1：空/敷衍摘要 → 重试一次
                if not ctx.reduction_ok(
                    src_tokens,
                    ctx.estimate_tokens_text(summary),
                    self.compact_max_reduction_ratio,
                ):
                    continue  # C3-2：缩水率不达标 → 重试一次
                recovery = self._recovery_block(user_request, steps_done)
                new_system = old_system
                new_system += f"\n\n## 前期执行摘要（已完成 {steps_done} 步）\n{summary}"
                if recovery:
                    new_system += f"\n\n## 恢复状态\n{recovery}"
                tail = messages[s:]
                return [{"role": "system", "content": new_system}] + tail, compacts_used + 1
            return None
        except Exception:
            return None  # Loop 压缩失败不阻断主循环

    def _recovery_block(self, user_request: str, steps_done: int) -> str:
        """C4 恢复块：把引擎状态与进行中任务结构化带回 system，防止压缩丢状态"""
        parts: list[str] = []
        layer_name = getattr(self.engine, "_layer_name", None)
        if layer_name:
            parts.append(
                f"当前图层：{layer_name}（仍加载在引擎中，可直接继续操作，无需重新 load_data）"
            )
        elif getattr(self.engine, "_layer", None) is not None:
            parts.append("当前图层仍加载在引擎中，可直接继续操作")
        if user_request:
            parts.append(
                f"进行中任务：{user_request}（已完成 {steps_done} 步，继续执行直至调用 finish 收尾）"
            )
        return "\n".join(parts)

    def _maybe_compact(self, session) -> bool:
        """C1：轮末检查发送包是否越过 context×trigger_pct，是则执行 FullReplace 压缩。

        触发条件（全部满足才压缩，避免频繁调 LLM）：
        - 会话已运行 ≥ compact_min_rounds 轮（跳过一次性小会话）；
        - 发送包估算 token ≥ trigger（context_window × compact_trigger_pct）；
        - 压缩后目标（target）小于当前估算（防止无意义压缩）。
        """
        if session is None or not getattr(session, "messages", None):
            return False
        if len(getattr(session, "history", []) or []) < self.compact_min_rounds:
            return False
        est = self._estimate_send_pack(session)
        trigger = ctx.trigger_threshold(self._effective_context_window(), self.compact_trigger_pct)
        if est < trigger:
            return False
        target = ctx.target_threshold(self._effective_context_window(), self.compact_target_pct)
        if ctx.estimate_tokens_text(session.summary or "") >= target:
            return False  # 已有摘要到达目标水平，压缩无收益
        return self._full_replace(session, est)

    def _full_replace(self, session, est_send_pack: int | None = None) -> bool:
        """C2+C3：整段历史重写为一份新摘要（FullReplace），通过质量护栏才落库。

        材料 = 旧摘要 + 窗口外历史（tool-pair 完整切块，超长按 cap 截断保底保留旧摘要）；
        摘要结果须同时满足：非空 / 未退化（拒绝敷衍） / 缩水率达标（压缩收益真实），
        任一护栏不过则放弃本次（保留旧摘要与 compacted=False），不阻断会话。
        """
        if session is None:
            return False
        try:
            old_summary = session.summary or ""
            keep = self._history_window_limit(session)
            if len(session.messages) > keep:
                split = ctx.tool_pair_safe_start(
                    session.messages, len(session.messages) - keep
                )
                old_part = session.messages[:split] if split > 0 else []
            else:
                # 整个会话都在发送窗口内仍超阈值（单条消息过大/历史过肥）：
                # 无窗口外可压，退化为以全部历史为材料（cap 内截断保底）
                old_part = list(session.messages)
            # 材料文本 = 旧摘要 + 窗口外历史（tool-pair 完整切块，超长按 cap 截断）
            material = ctx.messages_to_text(
                ctx.material_for_compact(old_part, cap_chars=self.compact_source_cap_chars)
            )
            material = ((old_summary + "\n") if old_summary else "") + material
            material = material.strip()
            if not material:
                return False
            src_tokens = ctx.estimate_tokens_text(material)
            if est_send_pack is not None:
                # 发送包是否已达标由调用方判断，这里补充最小可压缩量护栏
                pass
            for _ in range(2):
                new_summary = self._summarize(material)
                if not new_summary or ctx.is_degenerate_summary(new_summary, old_summary):
                    continue  # C3-1：空/敷衍摘要 → 重试一次
                if not ctx.reduction_ok(
                    src_tokens,
                    ctx.estimate_tokens_text(new_summary),
                    self.compact_max_reduction_ratio,
                ):
                    continue  # C3-2：缩水率不达标 → 重试一次
                # C2 落库：原文留档不动，仅替换摘要并收窄后续发送窗口
                session.summary = new_summary
                session.compacted = True
                # C5：压缩摘要（含产物/图层/关键数值引用）同步进长期记忆，跨会话可召回
                if self.on_compact_summary is not None:
                    with contextlib.suppress(Exception):
                        # 记忆同步失败不影响会话压缩
                        self.on_compact_summary(new_summary)
                return True
            return False
        except Exception:
            return False  # 压缩失败不阻断会话，保留原状

    def _summarize(self, material: str) -> str:
        """调用压缩模型对材料做整段重写摘要；兼容 dict / str 两类 LLM 返回"""
        prompt = [
            {
                "role": "system",
                "content": (
                    "你是 GIS 助手的会话摘要器。把提供的完整对话历史重写为一份结构化摘要，"
                    "必须保留：已完成的产物文件名与路径、当前图层/任务状态、关键数值结论、"
                    "审批决策、用户偏好。按时间顺序组织，忽略寒暄与重复试错。"
                    "直接输出摘要正文，不要任何前后缀。"
                ),
            },
            {"role": "user", "content": material[: self.compact_source_cap_chars]},
        ]
        resp = self.llm.chat(
            prompt,
            agent_type="summary",
            model_id=self.compact_model or self.model_id,
        )
        if isinstance(resp, dict):
            return (resp.get("content") or "").strip()
        return (resp or "").strip()

    def _history_window(self, messages: list[dict], limit: int | None = None) -> list[dict]:
        """取最近 N 条历史消息，起点对齐到非 tool 消息。

        tool 消息必须紧跟带 tool_calls 的 assistant 消息；若窗口从中间切断
        落在 tool 消息上，会造成 role=tool 无前导的 400 错误，这里向前扩展对齐。
        """
        if not messages:
            return []
        limit = HISTORY_WINDOW_MESSAGES if limit is None else limit
        start = max(0, len(messages) - limit)
        while start > 0 and messages[start].get("role") == "tool":
            start -= 1
        return messages[start:]

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
        """HITL 审批 → 执行工具 → 产物校验回环。

        产生产物的工具（choropleth/scatter/render/summarize/export）执行后自动校验：
        - 校验失败 → 返回 status=error（附校验原因），让 LLM 修正参数重试；
        - 同一工具累计失败 ≥ max_check_retries 次 → 强制终止该工具，防止死循环。
        危险操作（编辑/删除等）执行前走审批门：pending 时阻塞等待人工审批。
        """
        gate = self.approval_gate
        if gate is not None:
            check = gate.check(name, args)
            if check is not None:
                if check.get("status") == "pending_approval":
                    self._emit_event({"type": "approval_request", **check})
                    verdict = gate.wait_for_approval(check["approval_id"])
                    if verdict != "approved":
                        return {
                            "status": "error",
                            "error": f"危险操作未获人工审批（{verdict}）",
                            "approval_id": check["approval_id"],
                        }
                else:  # rejected
                    return {
                        "status": "error",
                        "error": check.get("error", "操作被权限模式拒绝"),
                        "approval_id": check.get("approval_id"),
                    }
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

    def _emit_event(self, event: dict) -> None:
        """推送事件（run_stream 的 on_event）；无回调时静默"""
        if self.on_event_callback is not None:
            self.on_event_callback(event)

    @staticmethod
    def _wrap(
        trajectory: list[dict],
        steps: int,
        final: str,
        outputs: list[str],
        last: dict,
        timed_out: bool = False,
        audit_report: dict | None = None,
    ) -> dict:
        result: dict = {
            "final": final,
            "outputs": outputs,
            "trajectory": trajectory,
            "steps": steps,
            "timed_out": timed_out,
            "last_result": last,
        }
        if audit_report is not None:
            result["audit_report"] = audit_report
        return result
