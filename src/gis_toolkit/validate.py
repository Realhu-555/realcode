"""结果审核 L1：final 汇报数字与工具返回 stats 的规则校验（确定性、零 LLM 成本）。

设计依据：docs/GIS-智能助手-结果审核模块设计文档.md 第 5 节。
典型场景：LLM 在 finish 汇报里把「126 万亿」写成「12.6 万亿」，本模块用规则抓出量级错误。
"""

from __future__ import annotations

import math
import re
from typing import Any

# 中文数字单位 → 倍数（统一折算到「元」量纲，仅用于量级换算匹配）
_UNIT_MULT: dict[str, float] = {"万亿": 1e12, "亿": 1e8, "万": 1e4}

# 精确匹配相对容差（±0.5%）
_EXACT_TOL = 0.005
# 量级匹配容差：log10(比值) 距整数的最大偏差（允许 10 倍内 ±5% 浮动）
_MAGNITUDE_TOL = 0.05

# 结论性大数关键词：数字出现在这些词附近才判「结论性大数」
_CONCLUSIVE_WORDS = ("合计", "总共", "共计", "总量", "共计约", "总")

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# 匹配时尝试的 known 值单位（无单位 + 三种中文单位）
_UNIT_SCALES: list[float] = [1.0, 1e12, 1e8, 1e4]


def _collect_known(trajectory: list[dict]) -> list[float]:
    """从轨迹各工具返回的 stats 收集可核对数字（去重保序）"""
    seen: set[float] = set()
    out: list[float] = []
    for t in trajectory:
        res = t.get("result") or {}
        st = res.get("stats")
        if not isinstance(st, dict):
            continue
        for v in st.values():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            f = float(v)
            if f in seen:
                continue
            seen.add(f)
            out.append(f)
    return out


def _extract_candidates(final: str) -> list[dict[str, Any]]:
    """从 final 提取候选数字（含跟随的中文单位；过滤年份等噪声）"""
    out: list[dict[str, Any]] = []
    for m in _NUM_RE.finditer(final):
        raw = m.group(0)
        val = float(raw)
        tail = re.sub(r"\s+", "", final[m.end() : m.end() + 6])
        unit: str | None = None
        for u in _UNIT_MULT:
            if tail.startswith(u):
                unit = u
                break
        # 年份噪声：4 位整数、无单位、在 1900-2100 区间
        if raw.isdigit() and not unit and 1900 <= val <= 2100:
            continue
        out.append({"raw": raw, "value": val, "unit": unit, "pos": m.start()})
    return out


def _close(a: float, b: float) -> bool:
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) / abs(b) <= _EXACT_TOL


def _match_known(value: float, unit: str | None, known: list[float]) -> str | None:
    """判断候选数字与任一 known 统计值的关系。

    Returns:
        "exact"：精确匹配（含单位换算，如 13.56 万亿 = 135673.2 亿）
        "magnitude"：量级匹配（差 10 的幂次倍，如 12.6 vs 126）→ FAIL
        None：未命中
    """
    v = value * _UNIT_MULT.get(unit or "", 1)
    # 第一遍：找精确匹配（含单位换算，如 13.56 万亿 = 135673.2 亿）
    for k in known:
        for mult in _UNIT_SCALES:
            if _close(v, k * mult):
                return "exact"
    # 第二遍：找量级匹配（差 10 的幂次倍，如 12.6 vs 126）→ FAIL
    for k in known:
        for mult in _UNIT_SCALES:
            kv = k * mult
            if kv == 0:
                continue
            ratio = v / kv
            if ratio <= 0:
                continue
            lg = math.log10(ratio)
            rounded = round(lg)
            if abs(rounded) >= 1 and abs(lg - rounded) <= _MAGNITUDE_TOL:
                return "magnitude"
    return None


def _is_conclusive(pos: int, final: str) -> bool:
    """候选数字是否为「结论性大数」：前后 30 字符窗口内出现合计/总共等词"""
    window = final[max(0, pos - 30) : min(len(final), pos + 30)]
    return any(w in window for w in _CONCLUSIVE_WORDS)


def validate_final_numbers(final: str, trajectory: list[dict]) -> dict:
    """L1 规则校验：核对 final 中的数字与工具返回 stats 是否一致。

    Args:
        final: 主 Agent 的最终汇报文本（finish.summary / 兜底汇报）。
        trajectory: 会话轨迹，每项含 {"tool", "result": {"stats": {...}}}。

    Returns:
        {"verdict": "PASS|WARN|FAIL", "issues": [{"number", "expected", "kind", "reason"}]}
    """
    known = _collect_known(trajectory)
    candidates = _extract_candidates(final)

    if not candidates:
        if known:
            return {
                "verdict": "WARN",
                "issues": [
                    {
                        "number": None,
                        "expected": None,
                        "kind": "missing",
                        "reason": "工具返回含关键统计，但 final 未引用任何数字",
                    }
                ],
            }
        return {"verdict": "PASS", "issues": []}

    issues: list[dict] = []
    for c in candidates:
        match = _match_known(c["value"], c["unit"], known)
        if match == "exact":
            continue
        if match == "magnitude":
            issues.append(
                {
                    "number": c["raw"],
                    "expected": None,
                    "kind": "magnitude",
                    "reason": (
                        f"数字 {c['raw']} 与工具返回统计量级不一致"
                        "（差 10 的幂次倍，疑似小数/量级错误）"
                    ),
                }
            )
            continue
        if c["value"] > 100 and _is_conclusive(c["pos"], final):
            issues.append(
                {
                    "number": c["raw"],
                    "expected": None,
                    "kind": "unverified",
                    "reason": f"结论性数字 {c['raw']} 未在工具返回统计中找到对应值",
                }
            )

    kinds = [i.get("kind") for i in issues]
    if "magnitude" in kinds:
        verdict = "FAIL"
    elif issues:
        verdict = "WARN"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "issues": issues}
