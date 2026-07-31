"""素宣 Suxuan — 营销内容多 Agent 平台 Web 服务

真实并行 + WebSocket 实时推送 + 全流程轨迹录制
"""

import asyncio
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.agents.celve import CelveAgent
from src.agents.gongzhonghao import GongzhonghaoAgent
from src.agents.zhihu import ZhihuAgent
from src.agents.xiaohongshu import XiaohongshuAgent
from src.agents.shenjiao import ShenjiaoAgent
from src.agents.export import ExportAgent
from src.orchestrator.state import ContentProjectState, ContentStage
from src.utils.trace import TraceTracker

app = FastAPI(title="素宣 Suxuan")

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    html_path = static_dir / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return {"service": "素宣 Suxuan", "version": "0.1.0"}


# ════════════════════════════════════════════════════════════
# WebSocket 连接管理
# ════════════════════════════════════════════════════════════

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}  # client_id → ws
        self.subscriptions: dict[str, set[str]] = {}  # project_id → {client_ids}

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        client_id = uuid.uuid4().hex[:8]
        self.active[client_id] = ws
        return client_id

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)
        for clients in self.subscriptions.values():
            clients.discard(client_id)

    def subscribe(self, client_id: str, project_id: str):
        if project_id not in self.subscriptions:
            self.subscriptions[project_id] = set()
        self.subscriptions[project_id].add(client_id)

    async def broadcast(self, project_id: str, event: dict):
        """向订阅了该项目的所有客户端推送事件"""
        clients = self.subscriptions.get(project_id, set())
        dead = []
        for cid in clients:
            ws = self.active.get(cid)
            if ws:
                try:
                    await ws.send_json(event)
                except Exception:
                    dead.append(cid)
            else:
                dead.append(cid)
        for cid in dead:
            clients.discard(cid)


ws_manager = ConnectionManager()
_thread_pool = ThreadPoolExecutor(max_workers=4)


# ════════════════════════════════════════════════════════════
# 全流程轨迹
# ════════════════════════════════════════════════════════════

@dataclass
class PipelineStage:
    stage: str                          # strategy | gongzhonghao | zhihu | xiaohongshu | shenjiao | export
    status: str                         # started | done | error
    start_ts: float = field(default_factory=time.time)
    end_ts: float = 0.0
    input_summary: dict | None = None   # state 关键字段摘要
    output_summary: dict | None = None  # 产出摘要（长度/前100字）
    error: str | None = None
    tool_calls: list[dict] = field(default_factory=list)  # 工具调用轨迹


@dataclass
class PipelineTrace:
    project_id: str
    pipeline: list[PipelineStage] = field(default_factory=list)
    created_ts: float = field(default_factory=time.time)

    def add_stage(self, stage: str, status: str = "started", **kwargs):
        entry = PipelineStage(stage=stage, status=status, **kwargs)
        existing = [s for s in self.pipeline if s.stage == stage and s.status == status]
        if existing:
            self.pipeline.remove(existing[0])
        self.pipeline.append(entry)
        return entry

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "total_elapsed": round(
                (self.pipeline[-1].end_ts - self.pipeline[0].start_ts)
                if self.pipeline and self.pipeline[0].start_ts and self.pipeline[-1].end_ts
                else 0, 1
            ),
            "pipeline": [
                {
                    "stage": s.stage,
                    "status": s.status,
                    "elapsed": round(s.end_ts - s.start_ts, 1) if s.end_ts else None,
                    "input_summary": s.input_summary,
                    "output_summary": s.output_summary,
                    "error": s.error,
                    "tool_calls": s.tool_calls,
                }
                for s in self.pipeline
            ],
        }

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ════════════════════════════════════════════════════════════
# 存储
# ════════════════════════════════════════════════════════════

_content_pipelines: dict[str, dict] = {}  # project_id → {state, agents, trace}


def _build_agents(celve_trace=None):
    return {
        "celve": CelveAgent(trace=celve_trace),
        "gongzhonghao": GongzhonghaoAgent(),
        "zhihu": ZhihuAgent(),
        "xiaohongshu": XiaohongshuAgent(),
        "shenjiao": ShenjiaoAgent(),
        "export": ExportAgent(),
    }


def _state_summary(state: ContentProjectState) -> dict:
    """提取 state 关键字段用于轨迹"""
    def summarize(val, max_len=100):
        if val is None:
            return None
        s = str(val)
        return {"len": len(s), "preview": s[:max_len]}

    return {
        "product_name": state.get("product_name"),
        "product_description": state.get("product_description"),
        "brand_tone": state.get("brand_tone"),
        "strategy": summarize(state.get("strategy")),
        "gzh_content": summarize(state.get("gzh_content")),
        "zhihu_content": summarize(state.get("zhihu_content")),
        "xhs_content": summarize(state.get("xhs_content")),
        "review_report": summarize(state.get("review_report")),
    }


# ════════════════════════════════════════════════════════════
# WebSocket 端点
# ════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    client_id = await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action", "")
            project_id = data.get("project_id", "")
            if action == "subscribe" and project_id:
                ws_manager.subscribe(client_id, project_id)
                await ws.send_json({
                    "type": "subscribed",
                    "project_id": project_id,
                    "message": f"已订阅项目 {project_id} 的进度更新",
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)


async def _push_progress(project_id: str, agent: str, status: str, detail: str = ""):
    await ws_manager.broadcast(project_id, {
        "type": "progress",
        "project_id": project_id,
        "agent": agent,
        "status": status,
        "detail": detail,
        "timestamp": time.time(),
    })


# ════════════════════════════════════════════════════════════
# API 路由
# ════════════════════════════════════════════════════════════

class CreateContentProjectRequest(BaseModel):
    mode: str = "form"
    product_name: str | None = None
    product_description: str | None = None
    target_users: str | None = None
    key_selling_points: list[str] | None = None
    brand_tone: str | None = None
    competitors: list[str] | None = None
    user_idea: str | None = None
    image_urls: list[str] | None = None


class ConfirmStrategyRequest(BaseModel):
    confirmed: bool = True
    feedback: str | None = None


@app.post("/api/v1/content-projects")
async def create_content_project(req: CreateContentProjectRequest):
    """创建项目 → 策略 Agent"""
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
        "strategy": None, "gzh_content": None, "zhihu_content": None,
        "xhs_content": None, "review_report": None,
        "current_stage": ContentStage.STRATEGY,
        "error_message": None, "ask_user": None, "messages": [],
        "brand_profile_id": None,
    }

    await _push_progress(project_id, "celve", "running", "策略分析中…")

    stage = pipeline.add_stage("strategy", status="started", input_summary=_state_summary(state))
    try:
        state = agents["celve"].run(state)
        stage.end_ts = time.time()
        stage.status = "done"
        stage.output_summary = _state_summary(state)
        # 提取 celve 的工具调用轨迹
        stage.tool_calls = [
            {"tool": s.tool_id, "params": s.tool_params, "result": s.tool_result}
            for s in celve_trace.steps if s.step_type == "tool_call"
        ]
    except Exception as e:
        stage.end_ts = time.time()
        stage.status = "error"
        stage.error = str(e)

    await _push_progress(project_id, "celve", "done", "策略分析完成")

    _content_pipelines[project_id] = {"state": state, "agents": agents, "trace": pipeline}
    return _content_state_response(project_id, state)


@app.get("/api/v1/content-projects/{project_id}")
async def get_content_project(project_id: str):
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "stage": "not_found", "error": "项目不存在"}

    response = _content_state_response(project_id, saved["state"])

    # 附带轨迹摘要
    trace = saved.get("trace")
    if trace:
        response["trace"] = trace.to_dict()
    return response


@app.post("/api/v1/content-projects/{project_id}/confirm-strategy")
async def confirm_content_strategy(project_id: str, req: ConfirmStrategyRequest):
    """确认策略 → 三路并行生成 → 审校 → 完成"""
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "stage": "not_found", "error": "项目不存在"}

    state = saved["state"]
    agents = saved["agents"]
    pipeline = saved.get("trace") or PipelineTrace(project_id=project_id)

    # 修改意见 → 重新策略
    if req.feedback:
        state["messages"] = state.get("messages", []) + [
            {"from": "user", "to": "celve", "type": "answer", "content": req.feedback}
        ]
        state["ask_user"] = None
        state = agents["celve"].run(state)
        if state.get("ask_user"):
            _content_pipelines[project_id] = {"state": state, "agents": agents, "trace": pipeline}
            return _content_state_response(project_id, state)

    state["current_stage"] = ContentStage.GENERATING

    # ===== 三路真正并行 =====
    # 每个渠道 Agent 只读：product + strategy，互不冲突
    # 用 ThreadPoolExecutor 绕过 GIL 串行，真正并发

    channels = [
        ("gongzhonghao", agents["gongzhonghao"]),
        ("zhihu", agents["zhihu"]),
        ("xiaohongshu", agents["xiaohongshu"]),
    ]

    async def _run_channel(ch_name, ch_agent, ch_state):
        loop = asyncio.get_running_loop()
        await _push_progress(project_id, ch_name, "running", f"{ch_name} 开始生成…")
        stage = pipeline.add_stage(ch_name, status="started")

        try:
            result = await loop.run_in_executor(_thread_pool, ch_agent.run, ch_state)
            stage.end_ts = time.time()
            stage.status = "done"
            stage.output_summary = {
                "len": len(str(result.get(
                    {"gongzhonghao": "gzh_content", "zhihu": "zhihu_content", "xiaohongshu": "xhs_content"}[ch_name],
                    ""
                )))
            }
            await _push_progress(project_id, ch_name, "done", f"{ch_name} 生成完成")
            return result
        except Exception as e:
            stage.end_ts = time.time()
            stage.status = "error"
            stage.error = str(e)
            return ch_state

    import copy
    results = await asyncio.gather(*[
        _run_channel(name, agent, copy.deepcopy(state))
        for name, agent in channels
    ])

    # 合并三个渠道产出
    for name, _ in channels:
        for r in results:
            key_map = {
                "gongzhonghao": "gzh_content",
                "zhihu": "zhihu_content",
                "xiaohongshu": "xhs_content",
            }
            if r.get(key_map.get(name)):
                state[key_map[name]] = r[key_map[name]]

    # 审校
    state["current_stage"] = ContentStage.REVIEW
    await _push_progress(project_id, "shenjiao", "running", "审校中…")
    stage = pipeline.add_stage("shenjiao", status="started")
    try:
        loop = asyncio.get_running_loop()
        state = await loop.run_in_executor(_thread_pool, agents["shenjiao"].run, state)
        stage.end_ts = time.time()
        stage.status = "done"
    except Exception as e:
        stage.end_ts = time.time()
        stage.status = "error"
        stage.error = str(e)
    await _push_progress(project_id, "shenjiao", "done", "审校完成")

    state["current_stage"] = ContentStage.DONE
    await _push_progress(project_id, "done", "done", "全部完成！")

    _content_pipelines[project_id] = {"state": state, "agents": agents, "trace": pipeline}
    return _content_state_response(project_id, state)


@app.get("/api/v1/content-projects/{project_id}/content/{channel}")
async def get_channel_content(project_id: str, channel: str):
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "error": "项目不存在"}
    channel_keys = {
        "gongzhonghao": "gzh_content",
        "zhihu": "zhihu_content",
        "xiaohongshu": "xhs_content",
    }
    key = channel_keys.get(channel)
    if not key:
        return {"project_id": project_id, "error": f"无效渠道: {channel}"}
    return {
        "project_id": project_id,
        "channel": channel,
        "full_content": saved["state"].get(key),
    }


@app.get("/api/v1/content-projects/{project_id}/review")
async def get_review_report(project_id: str):
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "error": "项目不存在"}
    return {
        "project_id": project_id,
        "full_content": saved["state"].get("review_report"),
    }


@app.get("/api/v1/content-projects/{project_id}/export")
async def export_content(project_id: str):
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "error": "项目不存在"}
    state = saved["state"]
    agents = saved["agents"]
    state = agents["export"].run(state)
    export_text = ""
    for msg in state.get("messages", []):
        if msg.get("from") == "export" and msg.get("type") == "output":
            export_text = msg["content"]
            break
    return {
        "project_id": project_id,
        "format": "markdown",
        "content": export_text,
    }


# ════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════

def _content_state_response(project_id: str, state: ContentProjectState) -> dict:
    stage = state.get("current_stage", ContentStage.STRATEGY)

    strategy = None
    if state.get("strategy"):
        strategy = {"full_content": state["strategy"]}

    contents: dict[str, dict | None] = {
        "gongzhonghao": (
            {"full_content": state["gzh_content"]}
            if state.get("gzh_content") else None
        ),
        "zhihu": (
            {"full_content": state["zhihu_content"]}
            if state.get("zhihu_content") else None
        ),
        "xiaohongshu": (
            {"full_content": state["xhs_content"]}
            if state.get("xhs_content") else None
        ),
    }

    review_report = None
    if state.get("review_report"):
        review_report = {"full_content": state["review_report"]}

    return {
        "project_id": project_id,
        "stage": stage.value if hasattr(stage, "value") else str(stage),
        "ask_user": state.get("ask_user"),
        "strategy": strategy,
        "contents": contents,
        "review_report": review_report,
        "created_at": "",
        "updated_at": "",
    }


# ════════════════════════════════════════════════════════════
# 启动入口
# ════════════════════════════════════════════════════════════

def start():
    import uvicorn
    uvicorn.run("src.web.server:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    start()
