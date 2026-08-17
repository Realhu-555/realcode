"""GIS Agent 公共解析工具 — 结构化标记提取与结论判断"""

import re

# LLM 输出中的结构化标记（与 prompt 模板约定一致）
ASK_USER_PATTERN = re.compile(r"\[ASK_USER\]\s*(.*?)\s*\[/ASK_USER\]", re.DOTALL)
TECH_PLAN_PATTERN = re.compile(r"---TECH_PLAN_START---\s*(.*?)\s*---TECH_PLAN_END---", re.DOTALL)
SCRIPT_PATTERN = re.compile(r"---SCRIPT_START---\s*(.*?)\s*---SCRIPT_END---", re.DOTALL)
CHECK_REPORT_PATTERN = re.compile(
    r"---CHECK_REPORT_START---\s*(.*?)\s*---CHECK_REPORT_END---", re.DOTALL
)
_PASS_FAIL_PATTERN = re.compile(r"整体结论\s*[:：]\s*(PASS|FAIL)", re.IGNORECASE)
_FALLBACK_PASS_FAIL = re.compile(r"\b(PASS|FAIL)\b")
# 容错：LLM 常只输出 START 不输出 END，统一从 START 取到结尾
_GENERIC_BLOCK = re.compile(r"---[A-Z_]+_START---\s*(.*?)(?:---[A-Z_]+_END---|$)", re.DOTALL)


def extract_block(content: str, pattern: re.Pattern[str]) -> str:
    """提取标记块内容；带/不带 END 标记都容错，无标记时返回全文"""
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    fallback = _GENERIC_BLOCK.search(content)
    if fallback:
        return fallback.group(1).strip()
    return content.strip()


def parse_ask_user(response: str) -> str | None:
    """解析 [ASK_USER] 追问；无追问返回 None"""
    match = ASK_USER_PATTERN.search(response)
    if not match:
        return None
    question = match.group(1).strip()
    return question or None


def parse_pass_fail(report: str) -> bool:
    """判断校验结论：True=PASS，False=FAIL；找不到关键字时宽容按 PASS"""
    match = _PASS_FAIL_PATTERN.search(report)
    if match:
        return match.group(1).upper() == "PASS"
    fallback = _FALLBACK_PASS_FAIL.search(report)
    return not (fallback and fallback.group(1).upper() == "FAIL")
