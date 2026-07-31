"""工具自动调用辅助 + 调用轨迹收集

每个 Agent 在关键节点自动执行其注册的工具，同时记录轨迹。
不依赖 ReAct 循环——这是"agent 内置行为"，不是 LLM 驱动的工具调用。
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from src.tools.registry import tool_registry
from src.tools.protocol import ToolContext


@dataclass
class ToolInvocation:
    tool_id: str
    agent: str
    params: dict[str, Any]
    success: bool
    result: Any = None
    error: str | None = None
    timestamp: float = field(default_factory=time.time)


class ToolTracker:
    """跨 Agent 的工具调用轨迹收集器"""

    def __init__(self):
        self.invocations: list[ToolInvocation] = []

    def record(self, tool_id: str, agent: str, params: dict, result: Any, error: str | None = None):
        self.invocations.append(ToolInvocation(
            tool_id=tool_id,
            agent=agent,
            params=params,
            success=(error is None),
            result=result,
            error=error,
        ))

    def summary(self) -> dict:
        return {
            "total_calls": len(self.invocations),
            "by_tool": {
                tid: len([i for i in self.invocations if i.tool_id == tid])
                for tid in set(i.tool_id for i in self.invocations)
            },
            "calls": [
                {
                    "tool": i.tool_id,
                    "agent": i.agent,
                    "params": i.params,
                    "success": i.success,
                    "result_summary": str(i.result)[:200] if i.error is None else None,
                    "error": i.error,
                }
                for i in self.invocations
            ],
        }


_global_tracker: ToolTracker | None = None


def get_tool_tracker() -> ToolTracker:
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ToolTracker()
    return _global_tracker


def reset_tool_tracker():
    global _global_tracker
    _global_tracker = ToolTracker()
    return _global_tracker


async def call_tool(tool_id: str, agent: str, state: dict, **kwargs) -> Any:
    """执行一个工具并自动记录轨迹"""
    tracker = get_tool_tracker()
    tool = tool_registry.get(tool_id)
    if tool is None:
        tracker.record(tool_id, agent, kwargs, None, f"工具不存在: {tool_id}")
        return None

    ctx = ToolContext(
        session_id=state.get("project_id", agent),
        working_dir=".",
        project_state=state,
        brand_profile=None,
    )

    try:
        result = await tool.execute(ctx, **kwargs)
        tracker.record(tool_id, agent, kwargs, result.data if result.success else None, result.error)
        return result
    except Exception as e:
        tracker.record(tool_id, agent, kwargs, None, str(e))
        return None


def call_tool_sync(tool_id: str, agent: str, state: dict, **kwargs) -> Any:
    """同步/异步通用——自动检测事件循环状态"""
    try:
        loop = asyncio.get_running_loop()
        # 已在事件循环中 → 不能 asyncio.run()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lambda: asyncio.run(call_tool(tool_id, agent, state, **kwargs)))
            return future.result(timeout=30)
    except RuntimeError:
        # 无运行中的事件循环 → 安全使用 asyncio.run()
        return asyncio.run(call_tool(tool_id, agent, state, **kwargs))
