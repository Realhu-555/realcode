"""API 集成测试 — 营销内容平台路由"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.web.server import app

    return TestClient(app)


# ========================================================================
# POST /api/v1/content-projects
# ========================================================================

class TestCreateContentProject:
    @patch("src.web.server.CelveAgent")
    def test_create_project_form_mode(self, mock_agent_cls: MagicMock, client):
        """表单模式创建项目"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {
            "input_mode": "form",
            "product_name": "Test Product",
            "strategy": "## 策略内容\n\n分析...",
            "current_stage": "confirming",
            "ask_user": None,
            "messages": [{"from": "celve", "type": "output", "content": "策略"}],
        }

        resp = client.post(
            "/api/v1/content-projects",
            json={
                "mode": "form",
                "product_name": "Test Product",
                "product_description": "A product",
                "target_users": "Developers",
                "key_selling_points": ["fast", "cheap"],
                "brand_tone": "专业",
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "project_id" in data
        assert data["stage"] == "confirming"
        assert data["strategy"] is not None

    @patch("src.web.server.CelveAgent")
    @patch("src.web.server.GongzhonghaoAgent")
    @patch("src.web.server.ZhihuAgent")
    @patch("src.web.server.XiaohongshuAgent")
    @patch("src.web.server.ShenjiaoAgent")
    def test_create_project_free_mode(
        self,
        mock_sj: MagicMock,
        mock_xhs: MagicMock,
        mock_zh: MagicMock,
        mock_gzh: MagicMock,
        mock_celve: MagicMock,
        client,
    ):
        """自由模式创建项目"""
        mock_celve.return_value.run.return_value = {
            "input_mode": "free",
            "user_idea": "推广一个 AI 产品",
            "strategy": "## 策略\n\n自由模式策略",
            "current_stage": "confirming",
            "ask_user": None,
            "messages": [],
        }

        resp = client.post(
            "/api/v1/content-projects",
            json={
                "mode": "free",
                "user_idea": "推广一个 AI 产品，面向技术管理者",
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "confirming"

    @patch("src.web.server.CelveAgent")
    def test_create_project_with_images(self, mock_agent_cls: MagicMock, client):
        """带图片上传"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {
            "input_mode": "form",
            "product_name": "Test",
            "strategy": "## 策略\n\n结合图片分析...",
            "current_stage": "confirming",
            "ask_user": None,
            "image_urls": ["data:image/png;base64,fake"],
            "messages": [],
        }

        resp = client.post(
            "/api/v1/content-projects",
            json={
                "mode": "form",
                "product_name": "Test",
                "product_description": "Desc",
                "target_users": "Users",
                "image_urls": ["data:image/png;base64,fakeimage"],
            },
        )

        assert resp.status_code == 200

    @patch("src.web.server.CelveAgent")
    def test_create_project_ask_user(self, mock_agent_cls: MagicMock, client):
        """策略 Agent 追问"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {
            "input_mode": "form",
            "product_name": "",
            "strategy": None,
            "current_stage": "strategy",
            "ask_user": "请问您的目标用户群体是什么？",
            "messages": [],
        }

        resp = client.post(
            "/api/v1/content-projects",
            json={"mode": "form", "product_name": ""},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ask_user"] is not None
        assert data["stage"] == "strategy"

    @patch("src.web.server.CelveAgent")
    def test_create_project_agent_error(self, mock_agent_cls: MagicMock, client):
        """Agent 异常时返回错误"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.side_effect = RuntimeError("LLM 调用失败")

        resp = client.post(
            "/api/v1/content-projects",
            json={"mode": "form", "product_name": "Test"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "error"
        assert "LLM" in data["error"]


# ========================================================================
# GET /api/v1/content-projects/{id}
# ========================================================================

class TestGetContentProject:
    @patch("src.web.server.CelveAgent")
    def test_get_existing_project(self, mock_agent_cls: MagicMock, client):
        """查询已创建的项目"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {
            "product_name": "Test",
            "strategy": "## 策略",
            "current_stage": "confirming",
            "ask_user": None,
            "messages": [],
        }

        # 先创建
        create_resp = client.post("/api/v1/content-projects", json={"mode": "form", "product_name": "Test"})
        pid = create_resp.json()["project_id"]

        # 再查询
        resp = client.get(f"/api/v1/content-projects/{pid}")
        assert resp.status_code == 200
        assert resp.json()["project_id"] == pid

    def test_get_nonexistent_project(self, client):
        """查询不存在的项目"""
        resp = client.get("/api/v1/content-projects/nonexistent")
        assert resp.status_code == 200
        assert resp.json()["stage"] == "not_found"


# ========================================================================
# POST /api/v1/content-projects/{id}/confirm-strategy
# ========================================================================

class TestConfirmStrategy:
    @patch("src.web.server.CelveAgent")
    @patch("src.web.server.GongzhonghaoAgent")
    @patch("src.web.server.ZhihuAgent")
    @patch("src.web.server.XiaohongshuAgent")
    @patch("src.web.server.ShenjiaoAgent")
    def test_confirm_triggers_generation(
        self,
        mock_sj: MagicMock,
        mock_xhs: MagicMock,
        mock_zh: MagicMock,
        mock_gzh: MagicMock,
        mock_celve: MagicMock,
        client,
    ):
        """确认策略后进入生成阶段"""
        # 创建项目 — 用 side_effect 保留 state
        def celve_run(state):
            return {
                **state,
                "product_name": "Test",
                "strategy": "## 策略",
                "current_stage": "confirming",
                "ask_user": None,
            }
        mock_celve.return_value.run.side_effect = celve_run

        create_resp = client.post("/api/v1/content-projects", json={"product_name": "Test"})
        pid = create_resp.json()["project_id"]

        # mock 生成和审校 — side_effect 保留原始 state
        mock_gzh.return_value.run.side_effect = lambda s: {**s, "gzh_content": "# 公众号"}
        mock_zh.return_value.run.side_effect = lambda s: {**s, "zhihu_content": "## 知乎"}
        mock_xhs.return_value.run.side_effect = lambda s: {**s, "xhs_content": "# 小红书"}
        mock_sj.return_value.run.side_effect = lambda s: {**s, "review_report": "## 审校\n\n通过", "current_stage": "done"}

        resp = client.post(
            f"/api/v1/content-projects/{pid}/confirm-strategy",
            json={"confirmed": True},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "done"
        assert data["contents"]["gongzhonghao"] is not None
        assert data["contents"]["zhihu"] is not None
        assert data["contents"]["xiaohongshu"] is not None
        assert data["review_report"] is not None

    def test_confirm_nonexistent(self, client):
        """确认不存在的项目"""
        resp = client.post(
            "/api/v1/content-projects/nonexistent/confirm-strategy",
            json={"confirmed": True},
        )
        assert resp.json()["stage"] == "not_found"

    @patch("src.web.server.CelveAgent")
    def test_confirm_with_feedback(self, mock_agent_cls: MagicMock, client):
        """带修改意见确认"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        # 第一次：创建
        mock_agent.run.return_value = {
            "product_name": "Test",
            "strategy": "initial strategy",
            "current_stage": "confirming",
            "ask_user": None,
            "messages": [],
        }
        create_resp = client.post("/api/v1/content-projects", json={"product_name": "Test"})
        pid = create_resp.json()["project_id"]

        # 带反馈确认——不 mock 后续生成，只验证 feedback 路径被触发
        mock_agent.run.return_value = {
            "product_name": "Test",
            "strategy": "revised strategy after feedback",
            "current_stage": "confirming",
            "ask_user": None,
            "messages": [{"from": "user", "to": "celve", "type": "answer", "content": "更强调安全卖点"}],
        }

        resp = client.post(
            f"/api/v1/content-projects/{pid}/confirm-strategy",
            json={"confirmed": True, "feedback": "更强调安全卖点"},
        )

        assert resp.status_code == 200


# ========================================================================
# GET /api/v1/content-projects/{id}/content/{channel}
# ========================================================================

class TestGetChannelContent:
    @patch("src.web.server.CelveAgent")
    def test_get_channel_content(self, mock_agent_cls: MagicMock, client):
        """获取渠道内容"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {
            "product_name": "Test",
            "gzh_content": "# 公众号文章内容",
            "current_stage": "generating",
            "ask_user": None,
            "messages": [],
        }

        create_resp = client.post("/api/v1/content-projects", json={"product_name": "Test"})
        pid = create_resp.json()["project_id"]

        # 手动注入 gzh_content（绕过 agent）
        from src.web.server import _content_pipelines
        _content_pipelines[pid]["state"]["gzh_content"] = "# 公众号文章内容"

        resp = client.get(f"/api/v1/content-projects/{pid}/content/gongzhonghao")
        assert resp.status_code == 200
        assert resp.json()["full_content"] == "# 公众号文章内容"

    def test_get_invalid_channel(self, client):
        """无效渠道"""
        resp = client.get("/api/v1/content-projects/test/content/invalid")
        assert resp.status_code == 200
        assert "error" in resp.json()


# ========================================================================
# GET /api/v1/content-projects/{id}/review
# ========================================================================

class TestGetReviewReport:
    @patch("src.web.server.CelveAgent")
    def test_get_review(self, mock_agent_cls: MagicMock, client):
        """获取审校报告"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {
            "product_name": "Test",
            "review_report": "## 审校\n\n全部通过",
            "current_stage": "done",
            "ask_user": None,
            "messages": [],
        }

        create_resp = client.post("/api/v1/content-projects", json={"product_name": "Test"})
        pid = create_resp.json()["project_id"]

        from src.web.server import _content_pipelines
        _content_pipelines[pid]["state"]["review_report"] = "## 审校\n\n全部通过"

        resp = client.get(f"/api/v1/content-projects/{pid}/review")
        assert resp.status_code == 200
        assert "全部通过" in resp.json()["full_content"]


# ========================================================================
# GET /api/v1/content-projects/{id}/export
# ========================================================================

class TestExportContent:
    @patch("src.web.server.CelveAgent")
    def test_export(self, mock_agent_cls: MagicMock, client):
        """导出 Markdown"""
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {
            "product_name": "Test Product",
            "strategy": "strategy text",
            "gzh_content": "gzh text",
            "zhihu_content": "zh text",
            "xhs_content": "xhs text",
            "review_report": "review text",
            "current_stage": "done",
            "ask_user": None,
            "messages": [],
        }

        create_resp = client.post("/api/v1/content-projects", json={"product_name": "Test Product"})
        pid = create_resp.json()["project_id"]

        from src.web.server import _content_pipelines
        _content_pipelines[pid]["state"]["gzh_content"] = "gzh text"
        _content_pipelines[pid]["state"]["zhihu_content"] = "zh text"
        _content_pipelines[pid]["state"]["xhs_content"] = "xhs text"
        _content_pipelines[pid]["state"]["review_report"] = "review text"

        resp = client.get(f"/api/v1/content-projects/{pid}/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "markdown"
        assert "Test Product" in data["content"]
        assert "素宣" in data["content"]


# ========================================================================
# 状态序列化
# ========================================================================

class TestContentStateResponse:
    def test_serialize_strategy_stage(self):
        from src.web.server import _content_state_response
        from src.orchestrator.state import ContentStage

        state = {
            "product_name": "Test",
            "strategy": "## 策略",
            "current_stage": ContentStage.CONFIRMING,
            "ask_user": None,
        }

        resp = _content_state_response("test-id", state)
        assert resp["project_id"] == "test-id"
        assert resp["stage"] == "confirming"
        assert resp["strategy"]["full_content"] == "## 策略"

    def test_serialize_done_stage(self):
        from src.web.server import _content_state_response
        from src.orchestrator.state import ContentStage

        state = {
            "current_stage": ContentStage.DONE,
            "strategy": "s",
            "gzh_content": "g",
            "zhihu_content": "z",
            "xhs_content": "x",
            "review_report": "r",
            "ask_user": None,
        }

        resp = _content_state_response("test-id", state)
        assert resp["stage"] == "done"
        assert resp["contents"]["gongzhonghao"]["full_content"] == "g"
        assert resp["contents"]["zhihu"]["full_content"] == "z"
        assert resp["contents"]["xiaohongshu"]["full_content"] == "x"
        assert resp["review_report"]["full_content"] == "r"

    def test_serialize_null_contents(self):
        from src.web.server import _content_state_response
        from src.orchestrator.state import ContentStage

        state = {
            "current_stage": ContentStage.STRATEGY,
            "strategy": None,
            "ask_user": None,
        }

        resp = _content_state_response("test-id", state)
        assert resp["contents"]["gongzhonghao"] is None
        assert resp["contents"]["zhihu"] is None
        assert resp["contents"]["xiaohongshu"] is None
        assert resp["review_report"] is None
