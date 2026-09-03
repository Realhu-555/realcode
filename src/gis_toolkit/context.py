"""会话上下文管理与 auto-compact 工具函数（C1-C3）

对标 Grok Build / Claude Code 的自动压缩（auto-compact）机制：
- C1：按模型 context 百分比触发（不再用固定 token 阈值）
- C2：FullReplace 整体压缩 + 摘要注入发送窗口
- C3：质量护栏（退化拒绝 / 缩减率校验）

本模块只放纯函数与配置常量，便于独立单测；决策逻辑在 agent.py。
"""

from __future__ import annotations

DEFAULT_CHARS_PER_TOKEN = 3.0  # 无 tokenizer 环境的实用估算（中文为主场景取 3 字符/token）

# auto-compact 护栏默认值（可经 CompactConfig 注入覆盖）
DEFAULT_TRIGGER_PCT = 85.0  # 上下文占用达到窗口百分比触发压缩
DEFAULT_TARGET_PCT = 50.0  # 压缩目标：回到窗口百分比（发送窗口会明显缩小）
DEFAULT_MIN_ROUNDS = 3  # 至少 N 轮才允许压缩，避免过早开销
DEFAULT_MIN_COMPACTABLE_TOKENS = 5000  # 可压缩量低于该值不压（压缩开销 > 收益）
DEFAULT_MAX_REDUCTION_RATIO = 0.8  # 摘要 token 必须 ≤ 材料 token×该比例，否则视为未压缩成功
DEFAULT_MIN_SUMMARY_CHARS = 20  # 摘要低于该长度视为退化
DEFAULT_SOURCE_CAP_CHARS = 60000  # FullReplace 输入材料字符上限（防止单次压缩调用过大）
DEFAULT_WINDOW_AFTER = 12  # 压缩后发送窗口条数（旧历史已进摘要，无需再发 40 条原文）


def estimate_tokens_text(
    text: str | None, chars_per_token: float = DEFAULT_CHARS_PER_TOKEN
) -> int:
    """文本 token 快速估算：字符数 ÷ 每 token 字符数，最少 1"""
    if not text:
        return 0
    return max(1, int(len(text) / chars_per_token))


def estimate_tokens(
    messages: list[dict], chars_per_token: float = DEFAULT_CHARS_PER_TOKEN
) -> int:
    """消息列表 token 估算：content + tool_calls 参数均计入（system 之外由调用方并入）"""
    total = 0
    for m in messages:
        content = m.get("content")
        if isinstance(content, str):
            total += len(content)
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or {}
            total += len(fn.get("name") or "") + len(fn.get("arguments") or "")
    return max(1, int(total / chars_per_token))


def trigger_threshold(context_window: int, pct: float = DEFAULT_TRIGGER_PCT) -> int:
    """按 context 窗口与百分比算触发阈值（85% → int(window×0.85)）"""
    return max(1, int(context_window * pct / 100.0))


def target_threshold(context_window: int, pct: float = DEFAULT_TARGET_PCT) -> int:
    """按 context 窗口与百分比算压缩目标（50% → int(window×0.50)）"""
    return max(1, int(context_window * pct / 100.0))


def is_degenerate_summary(
    text: str,
    old_summary: str = "",
    min_chars: int = DEFAULT_MIN_SUMMARY_CHARS,
    repeated_line_ratio: float = 0.9,
) -> bool:
    """退化摘要检测：空 / 过短 / 与旧摘要完全相同 / 几乎整段复读同一行 → True"""
    if not text or not text.strip():
        return True
    stripped = text.strip()
    if len(stripped) < min_chars:
        return True
    if old_summary and stripped == old_summary.strip():
        return True
    lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    if not lines:
        return True
    if len(lines) >= 2:
        most_common = max(set(lines), key=lines.count)
        if lines.count(most_common) >= len(lines) * repeated_line_ratio:
            return True
    return False


def reduction_ok(
    original_tokens: int,
    summary_tokens: int,
    max_ratio: float = DEFAULT_MAX_REDUCTION_RATIO,
) -> bool:
    """缩减率校验：摘要必须把 token 降到材料 ×max_ratio 以下才算压缩有效"""
    if summary_tokens <= 0:
        return False
    budget = max(1, int(original_tokens * max_ratio))
    return summary_tokens <= budget


def tool_pair_safe_start(messages: list[dict], limit: int) -> int:
    """取最近 limit 条消息的窗口起点，向前对齐保证起点不是 role=tool。

    tool 消息必须紧跟带 tool_calls 的 assistant 消息；窗口从中间切断落在
    tool 消息上会造成 role=tool 无前导的 400 错误。
    """
    if not messages:
        return 0
    start = max(0, len(messages) - limit)
    while start > 0 and messages[start].get("role") == "tool":
        start -= 1
    return start


def window_messages(messages: list[dict], limit: int) -> list[dict]:
    """取最近 limit 条消息（tool-pair-safe 起点）"""
    start = tool_pair_safe_start(messages, limit)
    return messages[start:]


def material_for_compact(messages: list[dict], cap_chars: int = DEFAULT_SOURCE_CAP_CHARS) -> list[dict]:
    """FullReplace 压缩材料：最近消息窗口（tool-pair-safe），字符总量 ≤ cap_chars"""
    if not messages:
        return []
    limit = len(messages)
    while limit > 1:
        start = tool_pair_safe_start(messages, limit)
        chars = sum(
            len(m.get("content") or "") if isinstance(m.get("content"), str) else 0 for m in messages[start:]
        )
        if chars <= cap_chars:
            return messages[start:]
        limit = max(1, limit - 4)
    return messages[-1:]


def messages_to_text(messages: list[dict]) -> str:
    """把消息列表序列化为压缩模型可读的纯文本（含 tool_calls 参数）"""
    if not messages:
        return ""
    lines: list[str] = []
    for m in messages:
        role = m.get("role", "?")
        content = m.get("content")
        if content is None:
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function") or {}
                lines.append(f"[{role}] {fn.get('name')}({fn.get('arguments')})")
            continue
        if not isinstance(content, str):
            content = str(content)
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)
