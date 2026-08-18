"""素宣 Suxuan — 营销内容多 Agent 平台 Web 服务

数据持久化 + 多租户 + 真实并行 + WebSocket 推送 + 轨迹录制
"""

import asyncio
import copy
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

_thread_pool = ThreadPoolExecutor(max_workers=4)
from pydantic import BaseModel

from src.agents.celve import CelveAgent
from src.agents.export import ExportAgent
from src.agents.gis_checker import CheckerAgent
from src.agents.gis_codegen import CodegenAgent
from src.agents.gis_design import DesignAgent
from src.agents.gis_plan import PlanAgent
from src.agents.gongzhonghao import GongzhonghaoAgent
from src.agents.shenjiao import ShenjiaoAgent
from src.agents.xiaohongshu import XiaohongshuAgent
from src.agents.zhihu import ZhihuAgent
from src.orchestrator.gate import ApprovalGate, UserAction
from src.orchestrator.graph import create_gis_graph
from src.orchestrator.state import ContentProjectState, ContentStage, GisProjectState
from src.storage.project_store import store
from src.tools.implementations.data_inspect import inspect_file
from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.engine import GisEngine
from src.gis_toolkit.session import GisSessionStore
from src.orchestrator.long_term_memory import LongTermMemory, Lesson
from src.utils.trace import TraceTracker
from src.web.auth import get_user_id

app = FastAPI(title="素宣 Suxuan", version="1.0.0")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")))

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
    return {"service": "素宣 Suxuan", "version": "1.0.0"}


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
approval_gate = ApprovalGate(timeout=300)


async def _notify_approval(client_id: str, data: dict) -> None:
    """将 ApprovalGate 通知转发到 WebSocket broadcast"""
    data["project_id"] = client_id
    await ws_manager.broadcast(client_id, data)


approval_gate.set_notify_callback(_notify_approval)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    cid = await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            if data.get("action") == "subscribe" and data.get("project_id"):
                ws_manager.subscribe(cid, data["project_id"])
                await ws.send_json({"type": "subscribed", "project_id": data["project_id"]})
            elif data.get("action") in ("approve", "revise", "redo"):
                request_id = data.get("request_id")
                feedback = data.get("feedback") if data["action"] == "revise" else None
                approval_gate.handle_user_action(
                    request_id=request_id,
                    action=UserAction(data["action"]),
                    feedback=feedback,
                )
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
    await ws_manager.broadcast(project_id, {
        "type": "progress", "project_id": project_id,
        "agent": agent, "status": status, "detail": detail, "timestamp": time.time(),
    })


# ════════════════════════════════════════════════════════════
# Pipeline trace
# ════════════════════════════════════════════════════════════

@dataclass
class PipelineStage:
    stage: str
    status: str = "started"
    start_ts: float = field(default_factory=time.time)
    end_ts: float = 0.0
    output_summary: dict | None = None
    error: str | None = None
    tool_calls: list[dict] = field(default_factory=list)


@dataclass
class PipelineTrace:
    project_id: str
    pipeline: list[PipelineStage] = field(default_factory=list)

    def add(self, stage: str, **kw):
        s = PipelineStage(stage=stage, **kw)
        self.pipeline.append(s)
        return s


# ════════════════════════════════════════════════════════════
# Agent 工厂
# ════════════════════════════════════════════════════════════

def _build_agents(celve_trace=None):
    return {
        "celve": CelveAgent(trace=celve_trace),
        "gongzhonghao": GongzhonghaoAgent(),
        "zhihu": ZhihuAgent(),
        "xiaohongshu": XiaohongshuAgent(),
        "shenjiao": ShenjiaoAgent(),
        "export": ExportAgent(),
    }


_CHANNEL_KEY = {
    "gongzhonghao": "gzh_content",
    "zhihu": "zhihu_content",
    "xiaohongshu": "xhs_content",
}


# ════════════════════════════════════════════════════════════
# API
# ════════════════════════════════════════════════════════════

class CreateProjectRequest(BaseModel):
    mode: str = "form"
    product_name: str | None = None
    product_description: str | None = None
    target_users: str | None = None
    key_selling_points: list[str] | None = None
    brand_tone: str | None = None
    competitors: list[str] | None = None
    user_idea: str | None = None
    image_urls: list[str] | None = None
    model_preference: str | None = None



@app.post("/api/v1/content-projects")
async def create_project(req: CreateProjectRequest, user_id: str = Depends(get_user_id)):
    project_id = uuid.uuid4().hex[:12]
    pipeline = PipelineTrace(project_id=project_id)
    celve_trace = TraceTracker()
    agents = _build_agents(celve_trace=celve_trace)

    state: ContentProjectState = {
        "input_mode": req.mode,
        "product_name": req.product_name or "",
        "product_description": req.product_description or "",
        "target_users": req.target_users or "",
        "key_selling_points": req.key_selling_points or [],
        "brand_tone": req.brand_tone or "专业",
        "competitors": req.competitors or [],
        "user_idea": req.user_idea or "",
        "image_urls": req.image_urls or [],
        "model_preference": req.model_preference or None,
        "strategy": None, "gzh_content": None, "zhihu_content": None,
        "xhs_content": None, "review_report": None,
        "current_stage": ContentStage.STRATEGY,
        "error_message": None, "ask_user": None, "messages": [],
        "brand_profile_id": None,
    }

    # ── 策略生成 ──
    await _push_progress(project_id, "celve", "running", "策略分析中…")
    st = pipeline.add("strategy", status="started")
    try:
        loop = asyncio.get_running_loop()
        state = await loop.run_in_executor(_thread_pool, agents["celve"].run, state)
        st.end_ts = time.time(); st.status = "done"
        st.tool_calls = [
            {"name": tr["name"], "arguments": tr["arguments"],
             "result": str(tr.get("result", ""))[:200] if tr.get("result") else None}
            for s in celve_trace.steps if s.step_type == "tool_results"
            for tr in (s.tool_results or [])
        ]
    except Exception as e:
        st.end_ts = time.time(); st.status = "error"; st.error = str(e)
        await _push_progress(project_id, "celve", "error", str(e))

    await _push_progress(project_id, "celve", "done", "策略分析完成")

    # 持久化
    store.save(project_id, {**state, "current_stage": str(state.get("current_stage", ""))}, user_id)

    return _response(project_id, state)


@app.post("/api/v1/content-projects/{project_id}/confirm-strategy")
async def confirm_strategy(project_id: str, user_id: str = Depends(get_user_id)):
    """策略确认 → 人工审批（approve/revise/redo）→ 三渠道生成 → 审校"""
    proj = store.get(project_id, user_id)
    if not proj:
        return {"project_id": project_id, "stage": "not_found", "error": "项目不存在"}

    state = proj.get("_full", proj)
    celve_trace = TraceTracker()
    agents = _build_agents(celve_trace=celve_trace)

    # ── 审批循环：approve → 继续 / revise → 带反馈重生成 / redo → 清空重生成 ──
    strategy_version = 1
    while True:
        # 策略已生成或已更新，推送审批要求
        artifact = {
            "full_content": state.get("strategy") or "",
            "summary": (state.get("strategy") or "")[:200],
            "version": strategy_version,
        }
        await _push_progress(project_id, "celve", "done", "策略分析完成，等待确认…")
        result = await approval_gate.wait_for_approval(project_id, "strategy", artifact)

        if result.action == UserAction.APPROVE:
            break
        elif result.action == UserAction.REVISE:
            state["messages"] = state.get("messages", []) + [
                {"from": "user", "to": "celve", "type": "answer",
                 "content": result.feedback or ""}
            ]
            state["ask_user"] = None
            strategy_version += 1
            await _push_progress(project_id, "celve", "running", "根据反馈修改策略…")
            loop = asyncio.get_running_loop()
            state = await loop.run_in_executor(_thread_pool, agents["celve"].run, state)
            await _push_progress(project_id, "celve", "done", "策略已更新")
            continue
        elif result.action == UserAction.REDO:
            state["strategy"] = None
            state["ask_user"] = None
            strategy_version += 1
            await _push_progress(project_id, "celve", "running", "重新生成策略…")
            loop = asyncio.get_running_loop()
            state = await loop.run_in_executor(_thread_pool, agents["celve"].run, state)
            await _push_progress(project_id, "celve", "done", "策略重新生成完成")
            continue

    # ── 策略已确认：三渠道并行生成 ──
    state["current_stage"] = ContentStage.GENERATING

    channels = [
        ("gongzhonghao", agents["gongzhonghao"]),
        ("zhihu", agents["zhihu"]),
        ("xiaohongshu", agents["xiaohongshu"]),
    ]

    async def _run_channel(ch_name, ch_agent, ch_state):
        loop = asyncio.get_running_loop()
        await _push_progress(project_id, ch_name, "running", f"{ch_name} 生成中…")
        try:
            result = await loop.run_in_executor(_thread_pool, ch_agent.run, ch_state)
            await _push_progress(project_id, ch_name, "done", f"{ch_name} 完成")
            return result
        except Exception as e:
            await _push_progress(project_id, ch_name, "error", str(e))
            return ch_state

    results = await asyncio.gather(*[
        _run_channel(name, agent, copy.deepcopy(state))
        for name, agent in channels
    ])

    key_map = {"gongzhonghao": "gzh_content", "zhihu": "zhihu_content", "xiaohongshu": "xhs_content"}
    for (name, _), r in zip(channels, results):
        if r.get(key_map[name]):
            state[key_map[name]] = r[key_map[name]]

    # 审校
    state["current_stage"] = ContentStage.REVIEW
    await _push_progress(project_id, "shenjiao", "running", "审校中…")
    loop = asyncio.get_running_loop()
    state = await loop.run_in_executor(_thread_pool, agents["shenjiao"].run, state)
    await _push_progress(project_id, "shenjiao", "done", "审校完成")

    state["current_stage"] = ContentStage.DONE
    await _push_progress(project_id, "done", "done", "全部完成！")

    store.save(project_id, {**state, "current_stage": str(state.get("current_stage", ""))}, user_id)
    return _response(project_id, state)


@app.get("/api/v1/content-projects/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(get_user_id)):
    proj = store.get(project_id, user_id)
    if not proj:
        return {"project_id": project_id, "stage": "not_found", "error": "项目不存在"}
    return proj


@app.get("/api/v1/content-projects/{project_id}/content/{channel}")
async def get_content(project_id: str, channel: str, user_id: str = Depends(get_user_id)):
    proj = store.get(project_id, user_id)
    if not proj:
        return {"project_id": project_id, "error": "项目不存在"}
    state = proj.get("_full", proj)
    key = _CHANNEL_KEY.get(channel)
    return {"project_id": project_id, "channel": channel, "full_content": state.get(key) if key else None}


@app.get("/api/v1/content-projects/{project_id}/review")
async def get_review(project_id: str, user_id: str = Depends(get_user_id)):
    proj = store.get(project_id, user_id)
    if not proj:
        return {"project_id": project_id, "error": "项目不存在"}
    return {"project_id": project_id, "full_content": proj.get("_full", {}).get("review_report")}


@app.get("/api/v1/content-projects/{project_id}/export")
async def export_project(project_id: str, user_id: str = Depends(get_user_id)):
    proj = store.get(project_id, user_id)
    if not proj:
        return {"project_id": project_id, "error": "项目不存在"}
    state = proj.get("_full", proj)
    agents = _build_agents()
    state = agents["export"].run(state)
    export_text = ""
    for msg in state.get("messages", []):
        if msg.get("from") == "export":
            export_text = msg["content"]
            break
    return {"project_id": project_id, "format": "markdown", "content": export_text}


@app.get("/api/v1/content-projects")
async def list_projects(user_id: str = Depends(get_user_id)):
    """列出用户的最近项目"""
    projects = store.list_by_user(user_id, limit=50)
    return {
        "user_id": user_id,
        "total": len(projects),
        "projects": [{k: v for k, v in p.items() if k != "_full"} for p in projects],
    }


# ════════════════════════════════════════════════════════════
# 健康检查
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
    session_id, session = gis_sessions.get_or_create(req.session_id)
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
    return {"project_id": project_id, "session_id": session_id, **result}


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
        mine = [l for l in lessons if l.agent_name == f"gis_assistant:{user_id}"]
    except Exception:
        mine = []
    if not mine:
        return ""
    lines = "\n".join(f"- {l.lesson}" for l in mine[:3])
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
        engine = session.engine if session is not None else GisEngine(allowed_roots=["data"])
        agent = GisToolAgent(engine=engine, max_steps=12, model_id=model_preference)
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
            name: _GisProgressAgent(name, agent, project_id, loop)
            for name, agent in agents.items()
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
        await ws_manager.broadcast(project_id, {"type": "gis_result", "project_id": project_id, **result})
    except Exception as exc:
        await ws_manager.broadcast(
            project_id,
            {"type": "gis_error", "project_id": project_id, "error": str(exc)},
        )


# ════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════

def _response(project_id: str, state: dict) -> dict:
    stage = state.get("current_stage", ContentStage.STRATEGY)
    stage_str = stage.value if hasattr(stage, "value") else str(stage)

    strategy = {"full_content": state["strategy"]} if state.get("strategy") else None
    contents = {
        "gongzhonghao": {"full_content": state["gzh_content"]} if state.get("gzh_content") else None,
        "zhihu": {"full_content": state["zhihu_content"]} if state.get("zhihu_content") else None,
        "xiaohongshu": {"full_content": state["xhs_content"]} if state.get("xhs_content") else None,
    }
    review = {"full_content": state["review_report"]} if state.get("review_report") else None

    return {
        "project_id": project_id,
        "stage": stage_str,
        "ask_user": state.get("ask_user"),
        "strategy": strategy,
        "contents": contents,
        "review_report": review,
        "created_at": "",
        "updated_at": "",
    }


# ════════════════════════════════════════════════════════════
# 启动
# ════════════════════════════════════════════════════════════

def start():
    import uvicorn
    uvicorn.run("src.web.server:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    start()
