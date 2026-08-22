"""Token 成本统计

在 LLM Provider 层挂点：每次调用记录模型、Token 用量、耗时。
支持按 Agent / 阶段聚合，估算金额。

用法:
    from src.observability.cost_tracker import cost_tracker

    # provider 层每次 LLM 调用后:
    cost_tracker.record(model=..., agent_type=..., prompt_tokens=...,
                        completion_tokens=..., duration_ms=...)

    # 运行结束:
    summary = cost_tracker.summary()
    cost_tracker.save_run(run_id, scenario, success, latency_ms, trace_path)
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# 模型单价（美元 / 百万 tokens）—— 估算值，可在 config 中覆盖
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "deepseek:deepseek-v4-pro": {"input": 0.27, "output": 1.10},
    "default": {"input": 0.27, "output": 1.10},
}

_DB_PATH = Path(__file__).parent.parent.parent / "data" / "run_metrics.db"


@dataclass
class CostRecord:
    """单次 LLM 调用成本记录"""

    agent_type: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error_type: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class CostTracker:
    """成本追踪器（全局单例）"""

    def __init__(self, pricing: dict[str, dict[str, float]] | None = None) -> None:
        self.records: list[CostRecord] = []
        self.pricing = pricing or DEFAULT_PRICING

    # ── 记录 ──
    def record(
        self,
        agent_type: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        success: bool = True,
        error_type: str | None = None,
    ) -> None:
        self.records.append(CostRecord(
            agent_type=agent_type,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=duration_ms,
            success=success,
            error_type=error_type,
        ))

    # ── 聚合 ──
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.records)

    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self.records)

    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self.records)

    def estimate_cost(self, model: str | None = None) -> float:
        """估算金额（美元）。按模型单价，未知模型用 default 兜底。"""
        total = 0.0
        default_price = self.pricing.get("default", {"input": 0.27, "output": 1.10})
        for r in self.records:
            price = self.pricing.get(r.model, default_price)
            total += (r.prompt_tokens / 1_000_000) * price["input"]
            total += (r.completion_tokens / 1_000_000) * price["output"]
        return round(total, 6)

    def by_agent(self) -> dict[str, dict[str, Any]]:
        """按 Agent 维度聚合"""
        agents: dict[str, list[CostRecord]] = {}
        for r in self.records:
            agents.setdefault(r.agent_type, []).append(r)
        result = {}
        for agent, rs in agents.items():
            result[agent] = {
                "calls": len(rs),
                "prompt_tokens": sum(r.prompt_tokens for r in rs),
                "completion_tokens": sum(r.completion_tokens for r in rs),
                "total_tokens": sum(r.total_tokens for r in rs),
                "duration_ms_avg": round(sum(r.duration_ms for r in rs) / len(rs), 1),
                "failures": sum(0 for r in rs if not r.success),
            }
        return result

    def failures(self) -> list[dict[str, Any]]:
        """失败的 LLM 调用列表"""
        return [
            asdict(r) for r in self.records if not r.success
        ]

    def summary(self) -> dict[str, Any]:
        return {
            "total_calls": len(self.records),
            "total_tokens": self.total_tokens(),
            "prompt_tokens": self.total_prompt_tokens(),
            "completion_tokens": self.total_completion_tokens(),
            "estimated_cost_usd": self.estimate_cost(),
            "by_agent": self.by_agent(),
            "failures": self.failures(),
        }

    def reset(self) -> None:
        self.records = []

    # ── 持久化：run_metrics 表 ──
    def save_run(
        self,
        run_id: str,
        scenario: str,
        success: bool,
        latency_ms: float,
        trace_path: str = "",
        error_info: dict | None = None,
    ) -> None:
        """保存一次运行的结果汇总到 SQLite（供 Web 展示/历史查询）"""
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(_DB_PATH)
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS run_metrics (
                    run_id TEXT PRIMARY KEY,
                    scenario TEXT,
                    success INTEGER,
                    latency_ms REAL,
                    total_tokens INTEGER,
                    estimated_cost_usd REAL,
                    error_info TEXT,
                    trace_path TEXT,
                    created_at REAL
                )"""
            )
            conn.execute(
                """INSERT OR REPLACE INTO run_metrics
                   (run_id, scenario, success, latency_ms, total_tokens,
                    estimated_cost_usd, error_info, trace_path, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id, scenario, int(success), latency_ms,
                    self.total_tokens(), self.estimate_cost(),
                    str(error_info or ""), trace_path, time.time(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def list_runs(limit: int = 20) -> list[dict[str, Any]]:
        """查询最近运行记录"""
        if not _DB_PATH.exists():
            return []
        conn = sqlite3.connect(_DB_PATH)
        try:
            rows = conn.execute(
                "SELECT * FROM run_metrics ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            cols = [d[0] for d in conn.execute("SELECT * FROM run_metrics LIMIT 0").description]
            return [dict(zip(cols, r, strict=False)) for r in rows]
        finally:
            conn.close()


# 全局单例
cost_tracker = CostTracker()
