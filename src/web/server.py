"""Web 服务 — FastAPI + WebSocket 实时推送"""

import json
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

from src.orchestrator.state import ProjectState, Stage
from src.orchestrator.graph import create_graph
from src.agents.requirement import RequirementAgent
from src.agents.architect import ArchitectAgent
from src.agents.backend import BackendAgent
from src.agents.frontend import FrontendAgent
from src.agents.tester import TesterAgent
from src.agents.deployer import DeployerAgent


app = FastAPI(title="AI Dev Platform")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    html_path = static_dir / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = static_dir / "downloads" / filename
    if not file_path.exists():
        return HTMLResponse("文件不存在或已被清理", status_code=404)
    return FileResponse(file_path, filename=filename, media_type="application/zip")


# ─── WebSocket 管理 ──────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        client_id = uuid.uuid4().hex
        self.active[client_id] = ws
        return client_id

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)

    async def send(self, client_id: str, data: dict):
        ws = self.active.get(client_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()

# 持久化流水线状态，支持中断后恢复
_pipelines: dict[str, dict] = {}

# ─── Agent 初始化 ──────────────────────────────────────

def _build_agents():
    return {
        "requirement": RequirementAgent(),
        "architect": ArchitectAgent(),
        "backend": BackendAgent(),
        "frontend": FrontendAgent(),
        "tester": TesterAgent(),
        "deployer": DeployerAgent(),
    }


# ─── 进度映射 ──────────────────────────────────────────

STAGE_LABELS = {
    "requirement": "需求分析中…",
    "architecture": "架构设计中…",
    "backend": "正在生成后端代码…",
    "frontend": "正在生成前端代码…",
    "testing": "测试验证中…",
    "deployment": "打包中…",
    "done": "完成！",
}

STAGE_ORDER = ["requirement", "architecture", "backend", "frontend", "testing", "deployment"]


# ─── WebSocket 端点 ────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    client_id = await manager.connect(ws)

    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action")

            if action == "build":
                user_idea = data.get("idea", "")
                await run_pipeline(client_id, user_idea)

            elif action == "answer":
                answer_text = data.get("answer", "")
                await resume_pipeline(client_id, answer_text)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        _pipelines.pop(client_id, None)


async def run_pipeline(client_id: str, user_idea: str):
    """启动/重新开始流水线"""
    agents = _build_agents()

    state: ProjectState = {
        "user_idea": user_idea,
        "prd": None,
        "tech_plan": None,
        "frontend_code": None,
        "backend_code": None,
        "test_report": None,
        "zip_path": None,
        "current_stage": Stage.REQUIREMENT,
        "error_message": None,
        "messages": [],
        "ask_user": None,
    }

    await _execute_stages(client_id, agents, state, stage_index=0)


async def resume_pipeline(client_id: str, answer_text: str):
    """用户回答追问后恢复流水线"""
    saved = _pipelines.get(client_id)
    if not saved:
        await manager.send(client_id, {
            "type": "error",
            "message": "没有正在进行的构建任务，请重新开始。"
        })
        return

    agents = _build_agents()
    state = saved["state"]
    next_index = saved["next_index"]

    # 注入用户答案
    state["messages"] = state.get("messages", []) + [{
        "from": "user",
        "to": "requirement",
        "type": "answer",
        "content": answer_text,
    }]
    state["ask_user"] = None

    await _execute_stages(client_id, agents, state, stage_index=next_index)


async def _execute_stages(
    client_id: str,
    agents: dict,
    state: dict,
    stage_index: int,
):
    """从指定阶段开始执行流水线，每阶段检查是否需要追问"""
    stage_specs = [
        ("requirement", ["requirement"]),
        ("architecture", ["architect"]),
        ("backend", ["backend"]),
        ("frontend", ["frontend"]),
        ("testing", ["tester"]),
        ("deployment", ["deployer"]),
    ]

    for i in range(stage_index, len(stage_specs)):
        stage_name, agent_names = stage_specs[i]

        await manager.send(client_id, {
            "type": "progress",
            "stage": stage_name,
            "label": STAGE_LABELS.get(stage_name, stage_name),
        })

        for name in agent_names:
            try:
                agent = agents[name]
                state = agent.run(state)
            except Exception as e:
                await manager.send(client_id, {
                    "type": "error",
                    "message": f"{name} 执行失败: {str(e)}"
                })
                _pipelines.pop(client_id, None)
                return

        # 每阶段执行后检查是否有追问
        if state.get("ask_user"):
            _pipelines[client_id] = {
                "state": state,
                "next_index": i,  # 从当前阶段重试
            }
            await manager.send(client_id, {
                "type": "clarify",
                "question": state["ask_user"],
                "state": _serialize_state(state, stage_name),
            })
            return

        # 推送本阶段产出
        await manager.send(client_id, {
            "type": "update",
            "stage": stage_name,
            "state": _serialize_state(state, stage_name),
        })

    # 全部完成
    _pipelines.pop(client_id, None)
    await manager.send(client_id, {
        "type": "done",
        "state": _serialize_state(state, "done"),
    })


def _serialize_state(state: dict, stage: str) -> dict:
    """提取当前阶段可展示的内容"""
    result = {"stage": stage}
    if state.get("ask_user"):
        result["ask_user"] = state["ask_user"]
    if state.get("prd"):
        result["prd"] = state["prd"][:2000]
    if state.get("tech_plan"):
        result["tech_plan"] = state["tech_plan"][:2000]
    if state.get("backend_code"):
        result["backend_code"] = state["backend_code"][:2000]
    if state.get("frontend_code"):
        result["frontend_code"] = state["frontend_code"][:2000]
    if state.get("test_report"):
        result["test_report"] = state["test_report"][:1000]
    if state.get("zip_path"):
        result["zip_path"] = state["zip_path"]
    return result


# ─── 启动入口 ──────────────────────────────────────────

def start():
    import uvicorn
    uvicorn.run("src.web.server:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    start()
