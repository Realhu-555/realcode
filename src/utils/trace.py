"""Agent 轨迹追踪

记录每一步：LLM 调用、工具执行、中间结果。
输出为 trace.json，可在外部工具中可视化。

用法:
    from src.utils.trace import TraceTracker

    trace = TraceTracker()
    trace.llm_call(messages=[...], response="...")
    trace.tool_call(tool_id="web_search", params={"query": "..."}, result=...)
    trace.save("output/trace.json")
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class TraceStep:
    step_index: int
    step_type: str        # "llm_call" | "tool_results" | "final"
    timestamp: float = field(default_factory=time.time)

    # LLM call — 原生 function calling 格式
    messages: list[dict] | None = None       # 发给 LLM 的消息
    tools: list[dict] | None = None          # 可用的 tools schema
    content: str | None = None               # LLM 返回的文本内容
    tool_calls: list[dict] | None = None     # LLM 决定调用的工具
    model: str | None = None

    # Tool results（本轮所有工具执行结果）
    tool_results: list[dict] | None = None   # [{"id":..., "name":..., "result":..., "error":...}]

    # Final output
    final_output: str | None = None


class TraceTracker:
    """轨迹录制器 — DeepSeek 原生 function calling 格式"""

    def __init__(self):
        self.steps: list[TraceStep] = []
        self._step_index = 0

    def llm_call(
        self,
        messages: list[dict],
        tools: list[dict],
        content: str = "",
        tool_calls: list[dict] | None = None,
        model: str = "",
    ):
        self.steps.append(TraceStep(
            step_index=self._step_index,
            step_type="llm_call",
            messages=messages,
            tools=tools,
            content=content,
            tool_calls=tool_calls,
            model=model,
        ))
        self._step_index += 1

    def tool_results(self, results: list[dict]):
        """记录一批工具的执行结果"""
        self.steps.append(TraceStep(
            step_index=self._step_index,
            step_type="tool_results",
            tool_results=results,
        ))
        self._step_index += 1

    def final(self, output: str):
        self.steps.append(TraceStep(
            step_index=self._step_index,
            step_type="final",
            final_output=output,
        ))
        self._step_index += 1

    def to_dict(self) -> dict:
        return {
            "total_steps": len(self.steps),
            "steps": [asdict(s) for s in self.steps],
        }

    def save(self, filepath: str | Path):
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def summary(self) -> str:
        llm_count = sum(1 for s in self.steps if s.step_type == "llm_call")
        tool_count = sum(1 for s in self.steps if s.step_type == "tool_results")
        return f"{len(self.steps)} steps ({llm_count} LLM calls, {tool_count} tool results)"

