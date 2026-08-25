"""L2 结果审核 Agent（独立 LLM 复核）。

设计依据：docs/GIS-智能助手-结果审核模块设计文档.md 第 6 节。
- 只依据工具返回与产物清单核对 final 汇报，不依赖外部常识；
- 输出结构化 verdict（PASS/WARN/FAIL）+ reasons（带证据）+ suggestions；
- 只判不改：修正由主 Agent 完成（见 agent.py 修正回环）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from src.llm.provider import LLMProvider

_AUDIT_MARK = "---AUDIT_START---"


@dataclass
class AuditReport:
    """一次审核的结果。rounds_used 由主 Agent 在修正回环后回填。"""

    verdict: Literal["PASS", "WARN", "FAIL"]
    reasons: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    rounds_used: int = 0

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "reasons": self.reasons,
            "suggestions": self.suggestions,
            "rounds_used": self.rounds_used,
        }


def _stats_summary(trajectory: list[dict]) -> list[str]:
    """从轨迹提取各工具返回中的 stats，生成可读摘要行（供审核 prompt 使用）。"""
    lines: list[str] = []
    for t in trajectory:
        result = t.get("result") or {}
        stats = result.get("stats")
        if not isinstance(stats, dict) or not stats:
            continue
        lines.append(f"[{t.get('tool')}] " + json.dumps(stats, ensure_ascii=False))
    return lines


def _outputs_summary(outputs: list[str]) -> str:
    if not outputs:
        return "（无产物）"
    return "\n".join(f"- {o}" for o in outputs)


_AUDIT_SYSTEM = (
    "你是独立的 GIS 结果审核员。只依据提供的『工具返回统计』与『产物清单』核对用户请求与最终汇报，"
    "不依赖外部常识，不臆测数据。\n"
    "检查项：\n"
    "1. 用户请求是否真正完成；\n"
    "2. final 中的每个数字能否在工具返回统计中找到对应来源（要求给出引用）；\n"
    "3. 是否存在编造/与工具返回明显冲突的结论；\n"
    "4. 产物清单与 final 声明的产物是否一致。\n"
    "输出格式：先输出一行 " + _AUDIT_MARK + "，随后输出一个 JSON 对象，形如：\n"
    '{"verdict": "PASS|WARN|FAIL", "reasons": ["...", "..."], "suggestions": ["...", "..."]}\n'
    "verdict 取值只能是 PASS/WARN/FAIL。reasons 每条必须给出依据；"
    "suggestions 给主 Agent 的修改建议（仅 verdict=FAIL 时需要）。禁止改写结论，只判不改。"
)


class ResultAuditor:
    """L2 审核器：独立上下文调 LLM，输出 AuditReport。"""

    def __init__(self, llm: LLMProvider | None = None, max_rounds: int = 2) -> None:
        self.llm = llm or LLMProvider()
        self.max_rounds = max_rounds

    def audit(
        self,
        user_request: str,
        final: str,
        trajectory: list[dict],
        stats: dict[str, Any] | None = None,
        outputs: list[str] | None = None,
    ) -> AuditReport:
        """审核一次 final 汇报。stats 为额外的结构化统计（可空，轨迹内已含）。"""
        try:
            content = self.llm.chat(
                self._build_prompt(user_request, final, trajectory, stats, outputs or []),
                agent_type="gis_auditor",
            )
        except Exception as exc:  # 审核器调用失败不阻断会话，降级为 WARN
            return AuditReport("WARN", [f"审核器调用失败: {exc}"], [], 0)
        if not isinstance(content, str):  # 兼容异常返回（如 dict），视为无法解析
            content = ""
        data = self._parse(content)
        if data is None:
            return AuditReport(
                "WARN", ["审核器输出无法解析（未找到合法结构化结果）"], [], 0
            )
        verdict = data.get("verdict")
        if verdict not in ("PASS", "WARN", "FAIL"):
            verdict = "WARN"
        reasons = data.get("reasons") or []
        suggestions = data.get("suggestions") or []
        if not isinstance(reasons, list):
            reasons = []
        if not isinstance(suggestions, list):
            suggestions = []
        return AuditReport(verdict, [str(r) for r in reasons], [str(s) for s in suggestions], 0)

    # ── 内部 ──
    def _build_prompt(
        self,
        user_request: str,
        final: str,
        trajectory: list[dict],
        stats: dict[str, Any] | None,
        outputs: list[str],
    ) -> list[dict]:
        stats_lines = _stats_summary(trajectory)
        if stats:
            stats_lines.append("[额外统计] " + json.dumps(stats, ensure_ascii=False))
        stats_text = "\n".join(stats_lines) if stats_lines else "（工具返回中无结构化统计）"
        user_content = (
            f"用户请求：\n{user_request[:2000]}\n\n"
            f"工具返回统计：\n{stats_text[:6000]}\n\n"
            f"产物清单：\n{_outputs_summary(outputs)[:2000]}\n\n"
            f"Agent 最终汇报：\n{final[:6000]}\n\n"
            "请按审核规则输出审核结论。"
        )
        return [
            {"role": "system", "content": _AUDIT_SYSTEM},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def _parse(content: str) -> dict | None:
        """解析审核器输出：优先取 ---AUDIT_START--- 之后的 JSON，兼容 markdown 包裹。"""
        if not content:
            return None
        text = content
        if _AUDIT_MARK in text:
            text = text.split(_AUDIT_MARK, 1)[1]
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
