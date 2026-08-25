"""L2 结果审核器单测。

设计依据：docs/GIS-智能助手-结果审核模块设计文档.md 第 9.1 节。
覆盖：ResultAuditor 三分支 / JSON 解析容错 / 修正回环（FAIL→重写→PASS、连续 FAIL 终止、无产物跳过）。
"""

import json

from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.auditor import AuditReport, ResultAuditor
from src.gis_toolkit.engine import GisEngine


# ── 工具 ──────────────────────────────────────────────────────
def _traj_with_stats() -> list[dict]:
    """模拟 summarize 返回 stats（31 省 GDP，total≈126.3 万亿）"""
    return [
        {
            "tool": "summarize",
            "result": {
                "status": "ok",
                "stats": {
                    "total": 126.3,
                    "rows": 31,
                    "group_count": 31,
                    "top3": [
                        {"k": "广东", "v": 13.6},
                        {"k": "江苏", "v": 12.3},
                        {"k": "山东", "v": 9.2},
                    ],
                },
            },
        }
    ]


def _mk_audit(verdict: str, reasons=None, suggestions=None) -> str:
    payload = {
        "verdict": verdict,
        "reasons": reasons or [],
        "suggestions": suggestions or [],
    }
    return f"---AUDIT_START---\n{json.dumps(payload, ensure_ascii=False)}"


class _FakeLLM:
    """同时扮演 LLMProvider：chat 供审核器，chat_with_tools 供修正回环"""

    def __init__(self, chat_result: str = "", tools_result: dict | None = None):
        self.chat_result = chat_result
        self.tools_result = tools_result or {}
        self.chat_calls = 0
        self.tool_calls = 0

    def chat(self, messages, agent_type="gis_auditor", model_id=None) -> str:
        self.chat_calls += 1
        return self.chat_result

    def chat_with_tools(self, messages, tools, agent_type="gis_assistant", model_id=None) -> dict:
        self.tool_calls += 1
        return self.tools_result


def _finish_tool(final: str, outputs=None) -> dict:
    return {
        "content": None,
        "tool_calls": [
            {
                "function": {
                    "name": "finish",
                    "arguments": json.dumps({"explanation": final, "outputs": outputs or []}),
                }
            }
        ],
    }


# ── ResultAuditor：三分支 + 解析容错 ────────────────────────────
class TestResultAuditor:
    def test_audit_pass(self):
        fake = _FakeLLM(chat_result=_mk_audit("PASS", ["数字可溯源"]))
        auditor = ResultAuditor(fake)
        report = auditor.audit("用户请求", "final", _traj_with_stats(), None, ["a.csv"])
        assert report.verdict == "PASS"
        assert report.reasons == ["数字可溯源"]

    def test_audit_warn(self):
        fake = _FakeLLM(chat_result=_mk_audit("WARN", ["疑似未引用"], []))
        auditor = ResultAuditor(fake)
        report = auditor.audit("u", "f", [], None, [])
        assert report.verdict == "WARN"

    def test_audit_fail(self):
        fake = _FakeLLM(
            chat_result=_mk_audit("FAIL", ["12.6 与 stats.total=126.3 量级不一致"], ["修正为 126.3"])
        )
        auditor = ResultAuditor(fake)
        report = auditor.audit("u", "f", _traj_with_stats(), None, ["a.csv"])
        assert report.verdict == "FAIL"
        assert report.suggestions

    def test_parse_markdown_wrapped(self):
        content = (
            "审核结果如下：\n```json\n"
            + json.dumps({"verdict": "WARN", "reasons": ["x"], "suggestions": []})
            + "\n```"
        )
        fake = _FakeLLM(chat_result=content)
        auditor = ResultAuditor(fake)
        report = auditor.audit("u", "f", [], None, [])
        assert report.verdict == "WARN"
        assert report.reasons == ["x"]

    def test_parse_invalid_falls_back_warn(self):
        fake = _FakeLLM(chat_result="抱歉，我无法判断。")
        auditor = ResultAuditor(fake)
        report = auditor.audit("u", "f", [], None, [])
        assert report.verdict == "WARN"

    def test_chat_raises_falls_back_warn(self):
        class _RaisingLLM:
            def chat(self, messages, agent_type="gis_auditor", model_id=None):
                raise RuntimeError("boom")

        auditor = ResultAuditor(_RaisingLLM())
        report = auditor.audit("u", "f", [], None, [])
        assert report.verdict == "WARN"
        assert "调用失败" in report.reasons[0]

    def test_invalid_verdict_value_falls_back_warn(self):
        fake = _FakeLLM(chat_result=_mk_audit("MAYBE"))
        auditor = ResultAuditor(fake)
        report = auditor.audit("u", "f", [], None, [])
        assert report.verdict == "WARN"


# ── 修正回环 ──────────────────────────────────────────────────
def _mk_agent(fake_llm) -> GisToolAgent:
    agent = GisToolAgent(engine=GisEngine(), max_steps=5)
    agent.llm = fake_llm
    return agent


WRONG_FINAL = "全国 GDP 合计约 12.6 万亿元"
RIGHT_FINAL = "全国 GDP 合计约 126.3 万亿元"


class TestCorrectionLoop:
    def test_fail_to_pass_one_round(self):
        """验收锚点：12.6 vs 126 判 FAIL → L2 FAIL → 修正为 126.3 → 终态 PASS（1 轮）"""
        fake = _FakeLLM(
            chat_result=_mk_audit("FAIL", ["量级不一致"], ["改为 126.3"]),
            tools_result=_finish_tool(RIGHT_FINAL, ["out.csv"]),
        )
        agent = _mk_agent(fake)
        final, outputs, report = agent._audit_correction(
            "汇总各省 GDP", WRONG_FINAL, ["out.csv"], _traj_with_stats(), []
        )
        assert final == RIGHT_FINAL
        assert report is not None
        assert report["verdict"] == "PASS"
        assert report["rounds_used"] == 1

    def test_fail_terminates_when_llm_does_not_rewrite(self):
        """LLM 不重写（无 finish 调用、无文本）→ 回环终止，保留 FAIL"""
        fake = _FakeLLM(
            chat_result=_mk_audit("FAIL", ["量级不一致"], ["请修正"]),
            tools_result={"content": None, "tool_calls": []},
        )
        agent = _mk_agent(fake)
        final, outputs, report = agent._audit_correction(
            "汇总各省 GDP", WRONG_FINAL, ["out.csv"], _traj_with_stats(), []
        )
        assert final == WRONG_FINAL
        assert report["verdict"] == "FAIL"
        assert report["rounds_used"] == 1  # 尝试 1 轮后因无重写而终止

    def test_max_rounds_capped(self):
        """连续 FAIL 达 max_rounds 后终止，rounds_used=2"""
        class _FlakyLLM:
            def __init__(self):
                self.chat_result = _mk_audit("FAIL", ["仍不一致"], ["再改"])

            def chat(self, messages, agent_type="gis_auditor", model_id=None):
                return self.chat_result

            def chat_with_tools(self, messages, tools, agent_type="gis_assistant", model_id=None):
                # 每次返回一个不同的错误数字（模拟 LLM 反复写错），触发下一轮审核
                return _finish_tool("全国 GDP 合计约 12.7 万亿元", ["out.csv"])

        agent = _mk_agent(_FlakyLLM())
        final, outputs, report = agent._audit_correction(
            "汇总各省 GDP", WRONG_FINAL, ["out.csv"], _traj_with_stats(), []
        )
        assert report["verdict"] == "FAIL"
        assert report["rounds_used"] == 2  # 达到硬上限

    def test_no_outputs_skips_l2(self):
        """无产物 → 跳过 L2（不调 chat），仅按 L1 记录"""
        fake = _FakeLLM()
        agent = _mk_agent(fake)
        final, outputs, report = agent._audit_correction(
            "汇总各省 GDP", WRONG_FINAL, [], _traj_with_stats(), []
        )
        assert report["verdict"] == "FAIL"  # 量级错误仍按 L1 记录
        assert report["rounds_used"] == 0
        assert fake.chat_calls == 0  # L2 未跑

    def test_all_traceable_passes_no_report(self):
        """数字全部可溯源 → L1=PASS，不跑 L2，audit_report=None（无打扰）"""
        fake = _FakeLLM()
        agent = _mk_agent(fake)
        final, outputs, report = agent._audit_correction(
            "汇总各省 GDP", RIGHT_FINAL, ["out.csv"], _traj_with_stats(), []
        )
        assert report is None
        assert fake.chat_calls == 0

    def test_backward_compat_no_stats(self):
        """旧工具无 stats 的轨迹不报错：无结论性大数 → L1=PASS，不跑 L2"""
        traj = [{"tool": "inspect_data", "result": {"status": "ok", "columns": ["a", "b"]}}]
        fake = _FakeLLM()
        agent = _mk_agent(fake)
        final, outputs, report = agent._audit_correction("查询字段", "共 2 个字段", ["x.csv"], traj, [])
        # 正常返回、不抛异常即为通过；无 stats 时无结论性大数，视为 PASS 无打扰
        assert isinstance(final, str)
        assert report is None
        assert fake.chat_calls == 0


# ── AuditReport ───────────────────────────────────────────────
class TestAuditReport:
    def test_to_dict(self):
        report = AuditReport("WARN", ["a"], ["b"], 1)
        d = report.to_dict()
        assert d == {"verdict": "WARN", "reasons": ["a"], "suggestions": ["b"], "rounds_used": 1}
