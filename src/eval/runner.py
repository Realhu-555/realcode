"""评测运行器

批量跑真实流水线（celve → 三渠道并行 → 审校），产出指标数据。

用法:
    python -m src.eval.runner --scenarios all --repeat 1
    python -m src.eval.runner --scenarios devgate_form,mianmian_form --repeat 2

设计要点:
- 评测复用生产 Agent（不 mock），只是注入"自动回答"配置，测的是真实能力
- 所有 Agent 的同步 run() 放入线程池执行（内部 asyncio.run 不能在 running loop 里跑）
- 每轮评测前重置 cost_tracker / tool_tracker，保证指标是单次运行的
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agents.celve import CelveAgent
from src.agents.export import ExportAgent
from src.agents.gongzhonghao import GongzhonghaoAgent
from src.agents.shenjiao import ShenjiaoAgent
from src.agents.xiaohongshu import XiaohongshuAgent
from src.agents.zhihu import ZhihuAgent
from src.observability.cost_tracker import cost_tracker
from src.observability.failure import extract_failure
from src.orchestrator.state import ContentStage
from src.tools.tool_tracker import reset_tool_tracker, get_tool_tracker
from src.utils.trace import TraceTracker

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
OUTPUT_ROOT = Path(__file__).parent.parent.parent / "tests" / "eval_output"

_CHANNEL_KEY = {
    "gongzhonghao": "gzh_content",
    "zhihu": "zhihu_content",
    "xiaohongshu": "xhs_content",
}


@dataclass
class EvalConfig:
    """评测配置"""

    auto_answer: str = "信息够了，直接按现有信息生成完整策略，不用追问"
    max_celve_rounds: int = 2      # 自动回答追问的最大轮数（防死循环）
    timeout_per_stage: float = 300  # 单阶段超时（秒）


@dataclass
class RunResult:
    """单次运行结果"""

    scenario: str
    run_id: str
    success: bool
    latency_ms: float
    stages: dict[str, Any] = field(default_factory=dict)
    tool_stats: dict[str, Any] = field(default_factory=dict)
    cost_summary: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    state_summary: dict[str, Any] = field(default_factory=dict)


def _build_agents() -> dict[str, Any]:
    return {
        "celve": CelveAgent(),
        "gongzhonghao": GongzhonghaoAgent(),
        "zhihu": ZhihuAgent(),
        "xiaohongshu": XiaohongshuAgent(),
        "shenjiao": ShenjiaoAgent(),
        "export": ExportAgent(),
    }


def build_state(scenario: dict[str, Any]) -> dict[str, Any]:
    """从场景构造初始共享状态"""
    return {
        "input_mode": scenario.get("input_mode", "form"),
        "product_name": scenario.get("product_name", ""),
        "product_description": scenario.get("product_description", ""),
        "target_users": scenario.get("target_users", ""),
        "key_selling_points": scenario.get("key_selling_points", []),
        "brand_tone": scenario.get("brand_tone", "专业"),
        "competitors": scenario.get("competitors", []),
        "user_idea": scenario.get("user_idea", ""),
        "image_urls": [],
        "strategy": None,
        "gzh_content": None,
        "zhihu_content": None,
        "xhs_content": None,
        "review_report": None,
        "current_stage": ContentStage.STRATEGY,
        "error_message": None,
        "ask_user": None,
        "messages": [],
        "brand_profile_id": None,
    }


def load_scenarios(names: list[str] | None = None) -> list[dict[str, Any]]:
    """加载场景集。names=None 或 ["all"] 时加载全部。"""
    files = sorted(SCENARIOS_DIR.glob("*.json"))
    scenarios = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if names and names != ["all"] and data["name"] not in names:
            continue
        scenarios.append(data)
    return scenarios


async def run_pipeline_once(
    scenario: dict[str, Any],
    config: EvalConfig | None = None,
) -> RunResult:
    """跑一次完整流水线，返回运行结果"""
    config = config or EvalConfig()
    run_id = uuid.uuid4().hex[:10]
    start_wall = time.time()
    stages: dict[str, Any] = {}
    error: dict[str, Any] | None = None
    last_error_stage = ""

    # 每轮独立统计
    cost_tracker.reset()
    reset_tool_tracker()
    trace = TraceTracker()

    agents = _build_agents()
    state = build_state(scenario)
    loop = asyncio.get_running_loop()

    async def _run_node(name: str, st: dict[str, Any]) -> tuple[dict[str, Any], float, Exception | None]:
        t0 = time.time()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, agents[name].run, st),
                timeout=config.timeout_per_stage,
            )
            return result, (time.time() - t0) * 1000, None
        except Exception as e:
            return st, (time.time() - t0) * 1000, e

    # ── 阶段 1：策略（含自动追问处理）──
    for round_idx in range(config.max_celve_rounds):
        if state.get("ask_user"):
            # 模拟用户补充信息，清除追问标记
            state["messages"] = state.get("messages", []) + [
                {"from": "user", "to": "celve", "type": "answer",
                 "content": scenario.get("auto_answer") or config.auto_answer}
            ]
            state["ask_user"] = None
        st, dur, err = await _run_node("celve", state)
        state = st
        stages[f"strategy_round{round_idx + 1}"] = {
            "status": "error" if err else "done",
            "duration_ms": round(dur, 1),
        }
        if err:
            error = extract_failure(state, "celve", err, "strategy").to_dict()
            last_error_stage = "strategy"
            break
        if not state.get("ask_user"):
            break  # 策略完成，无追问

    if error:
        return RunResult(
            scenario=scenario["name"], run_id=run_id, success=False,
            latency_ms=(time.time() - start_wall) * 1000,
            stages=stages, error=error,
            tool_stats=get_tool_tracker().summary(),
            cost_summary=cost_tracker.summary(),
            state_summary=_state_summary(state),
        )

    # ── 阶段 2：三渠道并行 ──
    state["current_stage"] = ContentStage.GENERATING
    channels = ["gongzhonghao", "zhihu", "xiaohongshu"]
    tasks = [_run_node(name, copy.deepcopy(state)) for name in channels]
    results = await asyncio.gather(*tasks)

    for name, (r, dur, err) in zip(channels, results):
        stages[f"generate_{name}"] = {
            "status": "error" if err else "done",
            "duration_ms": round(dur, 1),
        }
        if err:
            error = extract_failure(state, name, err, "generating").to_dict()
            last_error_stage = f"generate_{name}"
            continue
        key = _CHANNEL_KEY[name]
        if r.get(key):
            state[key] = r[key]

    # ── 阶段 3：审校 ──
    if not error:
        state["current_stage"] = ContentStage.REVIEW
        st, dur, err = await _run_node("shenjiao", state)
        state = st
        stages["review"] = {
            "status": "error" if err else "done",
            "duration_ms": round(dur, 1),
        }
        if err:
            error = extract_failure(state, "shenjiao", err, "review").to_dict()
            last_error_stage = "review"

    if not error:
        state["current_stage"] = ContentStage.DONE
        stages["done"] = {"status": "done", "duration_ms": 0.0}

    # ── 成功判定：策略 + 至少一个渠道内容 + 审校报告 ──
    produced_channels = sum(
        1 for key in _CHANNEL_KEY.values() if state.get(key)
    )
    success = bool(
        error is None
        and state.get("strategy")
        and produced_channels >= 1
        and state.get("review_report")
    )
    if not success and error is None:
        error = {
            "stage": last_error_stage or "final",
            "node": "pipeline",
            "error_type": "incomplete_output",
            "message": f"产出不完整: 策略={bool(state.get('strategy'))}, "
                       f"渠道产出数={produced_channels}/3, 审校={bool(state.get('review_report'))}",
        }

    # 保存轨迹
    trace_path = ""
    try:
        trace_dir = OUTPUT_ROOT / "traces" / run_id
        trace_dir.mkdir(parents=True, exist_ok=True)
        trace_path = str(trace_dir / "trace.json")
        trace.final(str(state.get("strategy", ""))[:200] or "no strategy")
        trace.save(trace_path)
    except Exception:
        trace_path = ""

    result = RunResult(
        scenario=scenario["name"],
        run_id=run_id,
        success=success,
        latency_ms=(time.time() - start_wall) * 1000,
        stages=stages,
        tool_stats=get_tool_tracker().summary(),
        cost_summary=cost_tracker.summary(),
        error=error,
        state_summary=_state_summary(state),
    )

    # 持久化 run_metrics
    try:
        cost_tracker.save_run(
            run_id=run_id,
            scenario=scenario["name"],
            success=success,
            latency_ms=result.latency_ms,
            trace_path=trace_path,
            error_info=error,
        )
    except Exception:
        pass  # 统计失败不影响评测结果

    return result


def _state_summary(state: dict[str, Any]) -> dict[str, Any]:
    """产出摘要（便于报告查看）"""
    return {
        "strategy_len": len(state.get("strategy") or ""),
        "gzh_len": len(state.get("gzh_content") or ""),
        "zhihu_len": len(state.get("zhihu_content") or ""),
        "xhs_len": len(state.get("xhs_content") or ""),
        "review_len": len(state.get("review_report") or ""),
        "ask_user": bool(state.get("ask_user")),
    }


async def _run_batch(scenarios: list[dict[str, Any]], repeat: int, config: EvalConfig) -> list[RunResult]:
    all_results: list[RunResult] = []
    for sc in scenarios:
        for i in range(repeat):
            print(f"[eval] 运行场景 {sc['name']} ({i + 1}/{repeat}) ...", flush=True)
            result = await run_pipeline_once(sc, config)
            status = "[OK]" if result.success else "[FAIL]"
            print(
                f"  {status} {result.scenario} {result.run_id} "
                f"latency={result.latency_ms:.0f}ms "
                f"tokens={result.cost_summary.get('total_tokens', 0)}",
                flush=True,
            )
            if result.error:
                print(f"    失败: [{result.error.get('node')}] {result.error.get('message', '')[:120]}", flush=True)
            all_results.append(result)
    return all_results


def main() -> None:
    parser = argparse.ArgumentParser(description="素宣 Agent 评测")
    parser.add_argument("--scenarios", default="all", help="场景名，逗号分隔或 all")
    parser.add_argument("--repeat", type=int, default=1, help="每个场景重复次数")
    parser.add_argument("--auto-answer", default="", help="自定义自动回答内容")
    args = parser.parse_args()

    names = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    scenarios = load_scenarios(names)
    if not scenarios:
        print(f"[eval] 没有匹配的场景: {names}")
        return

    config = EvalConfig(auto_answer=args.auto_answer or EvalConfig.auto_answer)
    print(f"[eval] 场景数: {len(scenarios)}, repeat: {args.repeat}")

    results = asyncio.run(_run_batch(scenarios, args.repeat, config))

    # 输出报告
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    from src.eval.report import write_report
    write_report(out_dir, results, meta={
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scenarios": [s["name"] for s in scenarios],
        "repeat": args.repeat,
    })

    # 控制台摘要
    total = len(results)
    ok = sum(1 for r in results if r.success)
    tool_calls = sum(len((r.tool_stats or {}).get("calls", [])) for r in results)
    tool_ok = sum(
        sum(1 for c in (r.tool_stats or {}).get("calls", []) if c.get("success"))
        for r in results
    )
    print("\n" + "=" * 50)
    print(f"评测完成: {ok}/{total} 成功 ({ok / total * 100:.1f}%)")
    if tool_calls:
        print(f"工具调用: {tool_ok}/{tool_calls} 成功 ({tool_ok / tool_calls * 100:.1f}%)")
    print(f"报告目录: {out_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()
