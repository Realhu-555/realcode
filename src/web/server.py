"""素宣 Suxuan — 营销内容多 Agent 平台 Web 服务"""

import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.agents.celve import CelveAgent
from src.agents.gongzhonghao import GongzhonghaoAgent
from src.agents.zhihu import ZhihuAgent
from src.agents.xiaohongshu import XiaohongshuAgent
from src.agents.shenjiao import ShenjiaoAgent
from src.agents.export import ExportAgent
from src.orchestrator.state import ContentProjectState, ContentStage

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


# ════════════════════════════════════════════════════════
# Agent 初始化
# ════════════════════════════════════════════════════════

_content_pipelines: dict[str, dict] = {}


def _build_agents():
    return {
        "celve": CelveAgent(),
        "gongzhonghao": GongzhonghaoAgent(),
        "zhihu": ZhihuAgent(),
        "xiaohongshu": XiaohongshuAgent(),
        "shenjiao": ShenjiaoAgent(),
        "export": ExportAgent(),
    }


# ════════════════════════════════════════════════════════
# API 路由
# ════════════════════════════════════════════════════════


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
    """创建营销内容项目，启动策略 Agent"""
    project_id = uuid.uuid4().hex[:12]
    agents = _build_agents()

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

    try:
        state = agents["celve"].run(state)
    except Exception as e:
        return {"project_id": project_id, "stage": "error", "error": str(e)}

    _content_pipelines[project_id] = {"state": state, "agents": agents}
    return _content_state_response(project_id, state)


@app.get("/api/v1/content-projects/{project_id}")
async def get_content_project(project_id: str):
    """查询项目状态和所有产出"""
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "stage": "not_found", "error": "项目不存在"}
    return _content_state_response(project_id, saved["state"])


@app.post("/api/v1/content-projects/{project_id}/confirm-strategy")
async def confirm_content_strategy(project_id: str, req: ConfirmStrategyRequest):
    """确认策略，继续到内容生成阶段"""
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "stage": "not_found", "error": "项目不存在"}

    state = saved["state"]
    agents = saved["agents"]

    if req.feedback:
        state["messages"] = state.get("messages", []) + [
            {"from": "user", "to": "celve", "type": "answer", "content": req.feedback}
        ]
        state["ask_user"] = None
        state = agents["celve"].run(state)
        if state.get("ask_user"):
            _content_pipelines[project_id] = {"state": state, "agents": agents}
            return _content_state_response(project_id, state)

    # 三路并行生成
    state["current_stage"] = ContentStage.GENERATING
    state = agents["gongzhonghao"].run(state)
    state = agents["zhihu"].run(state)
    state = agents["xiaohongshu"].run(state)

    # 审校 → 完成
    state["current_stage"] = ContentStage.REVIEW
    state = agents["shenjiao"].run(state)
    state["current_stage"] = ContentStage.DONE

    _content_pipelines[project_id] = {"state": state, "agents": agents}
    return _content_state_response(project_id, state)


@app.get("/api/v1/content-projects/{project_id}/content/{channel}")
async def get_channel_content(project_id: str, channel: str):
    """获取指定渠道内容"""
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
    """获取审校报告"""
    saved = _content_pipelines.get(project_id)
    if not saved:
        return {"project_id": project_id, "error": "项目不存在"}
    return {
        "project_id": project_id,
        "full_content": saved["state"].get("review_report"),
    }


@app.get("/api/v1/content-projects/{project_id}/export")
async def export_content(project_id: str):
    """导出所有内容为 Markdown"""
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


# ════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════


def _content_state_response(project_id: str, state: ContentProjectState) -> dict:
    stage = state.get("current_stage", ContentStage.STRATEGY)

    strategy = None
    if state.get("strategy"):
        strategy = {"full_content": state["strategy"]}

    contents: dict[str, dict | None] = {
        "gongzhonghao": {"full_content": state["gzh_content"]} if state.get("gzh_content") else None,
        "zhihu": {"full_content": state["zhihu_content"]} if state.get("zhihu_content") else None,
        "xiaohongshu": {"full_content": state["xhs_content"]} if state.get("xhs_content") else None,
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


# ════════════════════════════════════════════════════════
# 启动入口
# ════════════════════════════════════════════════════════


def start():
    import uvicorn

    uvicorn.run("src.web.server:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    start()
