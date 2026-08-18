"""LangGraph 状态图 — GIS 智能操作 Agent 编排

编排流程：
  START → plan → design → codegen → exec → checker → (rewrite|export) → END
"""

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from langgraph.graph import END, StateGraph

from src.agents.gis_common import parse_pass_fail
from src.orchestrator.state import GisProjectState


def create_gis_graph(
    agents: dict[str, Any],
    export_dir: str = "data/gis_exports",
    project_id: str = "gis",
) -> Any:
    """创建 GIS 智能操作编排图

    节点：plan → design → codegen → exec → checker → export
    条件边：
    - plan 追问 → 停（ask_user，等待用户补充）；
    - checker FAIL 且重写轮次 < 2 → 回 codegen 重写（bump 递增轮次）；
    - checker PASS 或重写耗尽 → export。
    exec / export 为纯代码节点（无 LLM）。
    """
    graph = StateGraph(GisProjectState)

    graph.add_node("plan", agents["plan"].run)
    graph.add_node("design", agents["design"].run)
    graph.add_node("codegen", agents["codegen"].run)
    graph.add_node("exec", _exec_node)
    graph.add_node("checker", agents["checker"].run)
    graph.add_node("bump", _bump_rewrite_round)
    graph.add_node("export", _make_export_node(export_dir, project_id))

    graph.set_entry_point("plan")
    graph.add_conditional_edges(
        "plan",
        _route_after_plan,
        {"ask_user": END, "continue": "design"},
    )
    graph.add_edge("design", "codegen")
    graph.add_edge("codegen", "exec")
    graph.add_edge("exec", "checker")
    graph.add_conditional_edges(
        "checker",
        _route_after_check,
        {"rewrite": "bump", "export": "export"},
    )
    graph.add_edge("bump", "codegen")
    graph.add_edge("export", END)

    return graph.compile()


def _route_after_plan(state: GisProjectState) -> str:
    if state.get("ask_user"):
        return "ask_user"
    return "continue"


def _route_after_check(state: GisProjectState) -> str:
    report = state.get("check_report") or ""
    if not parse_pass_fail(report) and (state.get("rewrite_round") or 0) < 2:
        return "rewrite"
    return "export"


def _bump_rewrite_round(state: GisProjectState) -> GisProjectState:
    return {**state, "rewrite_round": (state.get("rewrite_round") or 0) + 1}


def _exec_node(state: GisProjectState) -> GisProjectState:
    """执行 codegen 产出的脚本：快照源数据 → AST 扫描 → 运行 → 收集产物"""
    from src.sandbox.executor import SandboxExecutor

    sandbox = SandboxExecutor()
    sandbox.create("gis_task")

    data_file = state.get("data_file")
    if data_file and Path(data_file).is_file():
        shutil.copy2(data_file, sandbox.work_dir / Path(data_file).name)

    output, code = sandbox.run_script("main.py", state.get("script") or "")
    result: GisProjectState = {
        **state,
        "exec_log": output,
        "artifacts": sandbox.list_files(),
        "workdir": str(sandbox.work_dir),
        "current_stage": "exec",
    }
    if code != 0:
        result["error_message"] = f"沙箱执行退出码: {code}"
    return result


def _make_export_node(export_dir: str, project_id: str) -> Callable[[GisProjectState], GisProjectState]:
    """导出节点工厂：打包成果 zip + 操作说明，打包后清理沙箱"""

    def _export(state: GisProjectState) -> GisProjectState:
        workdir = state.get("workdir")
        if not workdir or not Path(workdir).is_dir():
            return {
                **state,
                "current_stage": "error",
                "error_message": "沙箱目录不存在，无法导出",
            }
        Path(workdir, "操作说明.md").write_text(_build_readme(state), encoding="utf-8")
        Path(workdir, "校验报告.md").write_text(state.get("check_report") or "", encoding="utf-8")
        out_dir = Path(export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_base = str(out_dir / f"gis_result_{project_id}")
        zip_path = shutil.make_archive(zip_base, "zip", workdir)
        shutil.rmtree(workdir, ignore_errors=True)
        return {
            **state,
            "artifact_path": zip_path,
            "current_stage": "done",
        }

    return _export


def _build_readme(state: GisProjectState) -> str:
    """生成操作说明 Markdown"""
    artifacts = state.get("artifacts") or ["（无）"]
    return (
        "# GIS 成果操作说明\n\n"
        f"## 用户需求\n{state.get('user_request', '')}\n\n"
        f"## 任务方案\n{state.get('task_plan') or '（无）'}\n\n"
        f"## 技术方案\n{state.get('tech_plan') or '（无）'}\n\n"
        f"## 产出文件\n- " + "\n- ".join(artifacts) + "\n\n"
        f"## 校验报告\n{state.get('check_report') or '（无）'}\n"
    )
