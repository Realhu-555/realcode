"""素宣 Suxuan — 营销内容多 Agent 平台 Web 服务

数据持久化 + 多租户 + 真实并行 + WebSocket 推送 + 轨迹录制
"""

import asyncio
import copy
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

_thread_pool = ThreadPoolExecutor(max_workers=4)
from pydantic import BaseModel

from src.agents.celve import CelveAgent
from src.agents.gongzhonghao import GongzhonghaoAgent
from src.agents.zhihu import ZhihuAgent
from src.agents.xiaohongshu import XiaohongshuAgent
from src.agents.shenjiao import ShenjiaoAgent
from src.agents.export import ExportAgent
from src.orchestrator.gate import ApprovalGate, UserAction
from src.orchestrator.state import ContentProjectState, ContentStage
from src.storage.project_store import store
from src.web.auth import get_user_id
from src.utils.trace import TraceTracker

app = FastAPI(title="素宣 Suxuan", version="1.0.0")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")))


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
