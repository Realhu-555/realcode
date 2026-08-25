"""GIS 智能操作助手 Web 服务

数据持久化 + 多租户 + 真实并行 + WebSocket 推送 + 轨迹录制
"""

import asyncio
import json
import queue
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

_thread_pool = ThreadPoolExecutor(max_workers=4)
from pydantic import BaseModel

from src.agents.gis_checker import CheckerAgent
from src.agents.gis_codegen import CodegenAgent
from src.agents.gis_design import DesignAgent
from src.agents.gis_plan import PlanAgent
from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.engine import _jsonable, create_gis_engine
from src.gis_toolkit.session import GisSessionStore
from src.orchestrator.graph import create_gis_graph
from src.orchestrator.long_term_memory import Lesson, LongTermMemory
from src.orchestrator.state import GisProjectState
from src.tools.implementations.data_inspect import inspect_file
from src.web.auth import get_user_id

app = FastAPI(title="GIS 智能操作助手", version="1.1.0")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")))

# P3 阶段1：3D 演示页（frontend/3d-demo → static/3d-demo 同步后挂载）
_3D_DEMO_SRC = Path(__file__).resolve().parents[2] / "frontend" / "3d-demo"
_3D_DEMO_DST = static_dir / "3d-demo"
if _3D_DEMO_SRC.exists():
    _3D_DEMO_DST.mkdir(parents=True, exist_ok=True)
    for _f in _3D_DEMO_SRC.iterdir():
        if _f.is_file():
            shutil.copy2(_f, _3D_DEMO_DST / _f.name)
app.mount("/3d-demo", StaticFiles(directory=str(_3D_DEMO_DST), html=True), name="3d-demo")

# GIS 上传限制（SPEC v1.2 Task 4）
GIS_UPLOAD_DIR = Path("data/gis_uploads")
GIS_EXPORT_DIR = Path("data/gis_exports")
ALLOWED_GIS_EXTENSIONS = {".csv", ".geojson", ".json", ".zip"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
GIS_TOOLKIT_OUT_DIR = Path("data/gis_toolkit_out")
gis_sessions = GisSessionStore()
ltm = LongTermMemory()
_GIS_TOOLKIT_MEDIA = {
    ".png": "image/png",
    ".csv": "text/csv; charset=utf-8",
    ".geojson": "application/geo+json",
    ".json": "application/json",
    ".zip": "application/zip",
}


@app.get("/")
async def index():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return {"service": "GIS 智能操作助手", "version": "1.0.0"}


# ════════════════════════════════════════════════════════════
# WebSocket
# ════════════════════════════════════════════════════════════


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[str]] = {}

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        client_id = uuid.uuid4().hex[:8]
        self.active[client_id] = ws
        return client_id

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)
        for s in self.subscriptions.values():
            s.discard(client_id)

    def subscribe(self, client_id: str, project_id: str):
        self.subscriptions.setdefault(project_id, set()).add(client_id)

    async def broadcast(self, project_id: str, event: dict):
        for cid in self.subscriptions.get(project_id, set()):
            ws = self.active.get(cid)
            if ws:
                try:
                    await ws.send_json(event)
                except Exception:
                    pass


ws_manager = ConnectionManager()


# ── ApprovalGate 全局单例 ──


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    cid = await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            if data.get("action") == "subscribe" and data.get("project_id"):
                ws_manager.subscribe(cid, data["project_id"])
                await ws.send_json({"type": "subscribed", "project_id": data["project_id"]})
            elif data.get("action") == "build_gis":
                project_id = uuid.uuid4().hex[:12]
                asyncio.create_task(
                    _run_gis_ws(
                        client_id=cid,
                        project_id=project_id,
                        user_request=data.get("user_request", ""),
                        data_file=data.get("data_file"),
                        model_preference=data.get("model_preference"),
                    )
                )
                await ws.send_json({"type": "gis_started", "project_id": project_id})
            elif data.get("action") == "build_gis_assistant":
                project_id = uuid.uuid4().hex[:12]
                asyncio.create_task(
                    _run_gis_assistant_ws(
                        client_id=cid,
                        project_id=project_id,
                        user_request=data.get("user_request", ""),
                        data_file=data.get("data_file"),
                        model_preference=data.get("model_preference"),
                    )
                )
                await ws.send_json({"type": "gis_assistant_started", "project_id": project_id})
    except WebSocketDisconnect:
        ws_manager.disconnect(cid)


async def _push_progress(project_id: str, agent: str, status: str, detail: str = ""):
    await ws_manager.broadcast(
        project_id,
        {
            "type": "progress",
            "project_id": project_id,
            "agent": agent,
            "status": status,
            "detail": detail,
            "timestamp": time.time(),
        },
    )


# ════════════════════════════════════════════════════════════
# Pipeline trace
# ════════════════════════════════════════════════════════════


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/models")
async def list_models(user_id: str = Depends(get_user_id)):
    """列出可用模型（前端模型选择下拉）"""
    from src.llm.models import load_registry

    registry = load_registry()
    return {
        "models": registry.list_models(),
        "default": registry.default_model_id(),
    }


# ════════════════════════════════════════════════════════════
# GIS 智能操作平台（SPEC v1.2）
# ════════════════════════════════════════════════════════════


class GisBuildRequest(BaseModel):
    user_request: str
    data_file: str | None = None
    model_preference: str | None = None


class GisAssistantRequest(BaseModel):
    """工具调用版 GIS 助手请求"""

    user_request: str
    data_file: str | None = None
    model_preference: str | None = None
    session_id: str | None = None


@app.post("/api/v1/gis/upload")
async def upload_gis_data(file: UploadFile = File(...), user_id: str = Depends(get_user_id)):
    """上传 GIS 数据文件（CSV / GeoJSON / Shapefile zip）"""
    filename = Path(file.filename or "data").name
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_GIS_EXTENSIONS:
        return {
            "success": False,
            "error": f"不支持的文件类型: {ext}（支持 .csv / .geojson / .zip）",
        }
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        return {"success": False, "error": "文件超过 10MB 限制"}
    user_dir = GIS_UPLOAD_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    target = user_dir / filename
    target.write_bytes(content)
    return {"success": True, "path": str(target), "filename": filename, "size": len(content)}


@app.post("/api/v1/gis/build")
async def build_gis(req: GisBuildRequest, user_id: str = Depends(get_user_id)):
    """启动 GIS 流水线（plan→design→codegen→exec→checker→export），同步返回结果"""
    project_id = uuid.uuid4().hex[:12]
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        _thread_pool,
        _run_gis_sync,
        project_id,
        req.user_request,
        req.data_file,
        req.model_preference,
    )
    return {"project_id": project_id, **result}


@app.post("/api/v1/gis-assistant/run")
async def run_gis_assistant(req: GisAssistantRequest, user_id: str = Depends(get_user_id)):
    """运行工具调用版 GIS 助手；带 session_id 时复用会话（引擎状态 + 对话历史）"""
    project_id = uuid.uuid4().hex[:12]
    session_id, session = gis_sessions.get_or_create(req.session_id, user_id)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        _thread_pool,
        _run_gis_assistant_sync,
        req.user_request,
        req.data_file,
        req.model_preference,
        session,
        user_id,
    )
    gis_sessions.save(user_id, session)
    return {"project_id": project_id, "session_id": session_id, **result}


@app.get("/api/v1/gis-assistant/run/stream")
async def run_gis_assistant_stream(
    user_request: str,
    data_file: str | None = None,
    session_id: str | None = None,
    model_preference: str | None = None,
    user_id: str = Depends(get_user_id),
):
    """SSE 流式运行工具调用版 GIS 助手

    事件按输出顺序推送：
    session_start → text_delta / tool_call / tool_result → done / error。
    前端用 fetch + ReadableStream 解析（EventSource 无法携带 X-API-Key）。
    """
    sid, session = gis_sessions.get_or_create(session_id, user_id)
    events: queue.Queue = queue.Queue()

    def _runner() -> None:
        """后台线程：执行 run_stream 并把事件转发到队列，完成后保存会话"""
        try:
            agent = GisToolAgent(
                engine=session.engine,
                max_steps=12,
                model_id=model_preference,
                approval_gate=session.approval_gate,
            )
            ltm_hint = _build_ltm_hint(user_request, user_id)
            result = agent.run_stream(
                user_request,
                data_file=data_file,
                session=session,
                ltm_hint=ltm_hint,
                on_event=events.put,
            )
            _save_gis_lesson(user_id, session.session_id, user_request, result)
        except Exception as exc:
            events.put({"type": "error", "error": f"GIS 助手执行失败: {exc}"})
        finally:
            gis_sessions.save(user_id, session)
            events.put(None)

    threading.Thread(target=_runner, daemon=True).start()

    def _sse(payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False, default=_jsonable)}\n\n"

    async def _gen():
        yield _sse({"type": "session_start", "session_id": sid})
        while True:
            ev = await asyncio.to_thread(events.get)
            if ev is None:
                break
            yield _sse(ev)

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/gis-assistant/files/{session_id}/{filename}")
async def gis_assistant_file(session_id: str, filename: str, user_id: str = Depends(get_user_id)):
    """访问指定会话的 GIS 助手产物文件（防路径穿越，按扩展名给 MIME）"""
    if len(session_id) != 12 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(status_code=400, detail="非法会话 ID")
    safe = Path(filename).name
    if safe != filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    path = GIS_TOOLKIT_OUT_DIR / session_id / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    media = _GIS_TOOLKIT_MEDIA.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media)


@app.get("/api/v1/gis-assistant/sessions")
async def gis_sessions_list(user_id: str = Depends(get_user_id)):
    """当前用户的会话列表（摘要，按更新时间倒序）"""
    return {"sessions": gis_sessions.list_sessions(user_id)}


@app.get("/api/v1/gis-assistant/sessions/{session_id}")
async def gis_session_detail(session_id: str, user_id: str = Depends(get_user_id)):
    """会话详情（含每轮展示数据，供前端恢复对话）"""
    if len(session_id) != 12 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(status_code=400, detail="非法会话 ID")
    detail = gis_sessions.get_detail(user_id, session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return detail


@app.delete("/api/v1/gis-assistant/sessions/{session_id}")
async def gis_session_delete(session_id: str, user_id: str = Depends(get_user_id)):
    """删除会话（内存 + 持久化 + 产物目录）"""
    if len(session_id) != 12 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(status_code=400, detail="非法会话 ID")
    ok = gis_sessions.delete(user_id, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"success": True}


@app.post("/api/v1/gis-assistant/sessions/{session_id}/approvals/{approval_id}")
async def gis_approval(
    session_id: str,
    approval_id: str,
    action: str,
    user_id: str = Depends(get_user_id),
):
    """HITL 审批：approve / reject 危险操作"""
    if len(session_id) != 12 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(status_code=400, detail="非法会话 ID")
    if len(approval_id) != 12 or not all(c in "0123456789abcdef" for c in approval_id):
        raise HTTPException(status_code=400, detail="非法审批 ID")
    _, session = gis_sessions.get_or_create(session_id, user_id)
    result = session.approval_gate.resolve(approval_id, action)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "审批失败"))
    return result


@app.post("/api/v1/gis-assistant/sessions/{session_id}/permission")
async def gis_permission(
    session_id: str,
    mode: str,
    user_id: str = Depends(get_user_id),
):
    """切换会话权限模式：readonly / auto / ask"""
    if len(session_id) != 12 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(status_code=400, detail="非法会话 ID")
    _, session = gis_sessions.get_or_create(session_id, user_id)
    try:
        session.approval_gate.set_mode(mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "mode": mode}


# ════════════════════════════════════════════════════════════
# GIS helpers
# ════════════════════════════════════════════════════════════


def _build_gis_agents() -> dict:
    return {
        "plan": PlanAgent(),
        "design": DesignAgent(),
        "codegen": CodegenAgent(),
        "checker": CheckerAgent(),
    }


class _GisProgressAgent:
    """包装 GIS Agent，推送阶段进度（跨线程安全，WebSocket 用）"""

    def __init__(
        self,
        name: str,
        agent: Any,
        project_id: str,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.name = name
        self.agent = agent
        self.project_id = project_id
        self.loop = loop

    def run(self, state: dict) -> dict:
        self._push("started")
        try:
            result = self.agent.run(state)
        except Exception:
            self._push("error")
            raise
        self._push("done")
        return result

    def _push(self, status: str) -> None:
        coro = _push_progress(self.project_id, self.name, status)
        asyncio.run_coroutine_threadsafe(coro, self.loop)


def _build_ltm_hint(user_request: str, user_id: str) -> str:
    """检索当前用户的 GIS 历史任务经验，注入 system prompt"""
    try:
        lessons = ltm.get_relevant_lessons(user_request, limit=5)
        mine = [lesson for lesson in lessons if lesson.agent_name == f"gis_assistant:{user_id}"]
    except Exception:
        mine = []
    if not mine:
        return ""
    lines = "\n".join(f"- {lesson.lesson}" for lesson in mine[:3])
    return "你之前的 GIS 任务经验（仅作参考，按当前请求重新执行）：\n" + lines


def _save_gis_lesson(user_id: str, session_id: str, user_request: str, result: dict) -> None:
    """任务产出成功时，把用户请求 + 结论存入长期记忆"""
    outputs = result.get("outputs") or []
    if not outputs:
        return
    try:
        lesson = Lesson(
            id=uuid.uuid4().hex[:16],
            project_id=session_id,
            agent_name=f"gis_assistant:{user_id}",
            category="success",
            lesson=(
                f"GIS 任务完成：{user_request} → {result.get('final', '')}"
                f"（产物: {', '.join(outputs)}）"
            ),
        )
        ltm.save_lesson(lesson)
    except Exception:
        pass  # 记忆写入失败不影响主流程


def _run_gis_assistant_sync(
    user_request: str,
    data_file: str | None,
    model_preference: str | None,
    session=None,
    user_id: str = "anonymous",
) -> dict:
    """工具调用版 GIS 助手（后台线程执行，REST / WebSocket 复用）

    传入 session（GisSession）时复用引擎状态与对话历史，实现多轮连续对话。
    """
    try:
        engine = (
            session.engine if session is not None else create_gis_engine(allowed_roots=["data"])
        )
        agent = GisToolAgent(
            engine=engine,
            max_steps=12,
            model_id=model_preference,
            approval_gate=session.approval_gate if session is not None else None,
        )
        ltm_hint = _build_ltm_hint(user_request, user_id)
        result = agent.run(
            user_request,
            data_file=data_file,
            session=session,
            ltm_hint=ltm_hint,
        )
        if session is not None:
            _save_gis_lesson(user_id, session.session_id, user_request, result)
        return {
            "stage": "done",
            "trajectory": result["trajectory"],
            "outputs": result["outputs"],
            "final": result["final"],
            "steps": result["steps"],
            "timed_out": result["timed_out"],
            "out_dir": str(engine.out_dir),
        }
    except Exception as exc:
        return {"stage": "error", "error_message": f"GIS 助手执行失败: {exc}"}


def _run_gis_sync(
    project_id: str,
    user_request: str,
    data_file: str | None,
    model_preference: str | None,
    loop: asyncio.AbstractEventLoop | None = None,
) -> dict:
    """在后台线程同步执行 GIS 流水线（REST / WebSocket 复用）"""
    data_schema = None
    if data_file and Path(data_file).is_file():
        try:
            schema = inspect_file(data_file, str(Path(data_file).parent))
            schema["filename"] = Path(data_file).name
            data_schema = json.dumps(schema, ensure_ascii=False)
        except ValueError as exc:
            return {"stage": "error", "error_message": f"数据检查失败: {exc}"}

    state: GisProjectState = {
        "user_request": user_request,
        "data_file": data_file,
        "data_schema": data_schema,
        "model_preference": model_preference,
        "current_stage": "plan",
        "messages": [],
    }
    agents = _build_gis_agents()
    if loop is not None:
        agents = {
            name: _GisProgressAgent(name, agent, project_id, loop) for name, agent in agents.items()
        }
    graph = create_gis_graph(
        agents,
        export_dir=str(GIS_EXPORT_DIR),
        project_id=project_id,
    )
    try:
        result = graph.invoke(state)
    except Exception as exc:
        return {"stage": "error", "error_message": f"流水线执行失败: {exc}"}
    return _gis_response(result)


def _gis_response(state: dict) -> dict:
    """GIS 流水线结果序列化（供 REST / WebSocket）"""
    return {
        "stage": str(state.get("current_stage", "plan")),
        "ask_user": state.get("ask_user"),
        "task_plan": state.get("task_plan"),
        "tech_plan": state.get("tech_plan"),
        "script": state.get("script"),
        "exec_log": state.get("exec_log"),
        "artifacts": state.get("artifacts"),
        "check_report": state.get("check_report"),
        "artifact_path": state.get("artifact_path"),
        "error_message": state.get("error_message"),
        "rewrite_round": state.get("rewrite_round"),
    }


async def _run_gis_assistant_ws(
    client_id: str,
    project_id: str,
    user_request: str,
    data_file: str | None,
    model_preference: str | None,
) -> None:
    """WebSocket 后台执行工具调用版 GIS 助手，完成后广播结果"""
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            _thread_pool,
            _run_gis_assistant_sync,
            user_request,
            data_file,
            model_preference,
        )
        await ws_manager.broadcast(
            project_id, {"type": "gis_assistant_result", "project_id": project_id, **result}
        )
    except Exception as exc:
        await ws_manager.broadcast(
            project_id,
            {"type": "gis_assistant_error", "project_id": project_id, "error": str(exc)},
        )


async def _run_gis_ws(
    client_id: str,
    project_id: str,
    user_request: str,
    data_file: str | None,
    model_preference: str | None,
) -> None:
    """WebSocket 后台执行 GIS 流水线，完成后广播结果"""
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            _thread_pool,
            _run_gis_sync,
            project_id,
            user_request,
            data_file,
            model_preference,
            loop,
        )
        await ws_manager.broadcast(
            project_id, {"type": "gis_result", "project_id": project_id, **result}
        )
    except Exception as exc:
        await ws_manager.broadcast(
            project_id,
            {"type": "gis_error", "project_id": project_id, "error": str(exc)},
        )


# ════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """SPA history fallback：非 API 路径统一返回 index.html（/gis 等前端路由）"""
    if full_path.startswith(("api/", "assets/")) or full_path == "health":
        raise HTTPException(status_code=404, detail="Not Found")
    index_path = static_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return {"service": "GIS 智能操作助手", "version": "1.1.0"}


def start():
    import uvicorn

    uvicorn.run("src.web.server:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    start()
