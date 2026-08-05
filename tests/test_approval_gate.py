"""ApprovalGate 单元测试"""
import asyncio
import pytest
from src.orchestrator.gate import ApprovalGate, UserAction, ApprovalResult


class TestApprovalGate:
    """ApprovalGate 核心逻辑测试"""

    def test_approve_action_returns_correct_result(self):
        """approve 操作返回正确的 ApprovalResult"""
        gate = ApprovalGate()
        result = gate.handle_user_action("test:strategy:1", UserAction.APPROVE)
        assert result.action == UserAction.APPROVE
        assert result.approved is True
        assert result.feedback is None

    def test_revise_action_returns_feedback(self):
        """revise 操作携带 feedback"""
        gate = ApprovalGate()
        result = gate.handle_user_action(
            "test:strategy:1", UserAction.REVISE, "加强安全卖点"
        )
        assert result.action == UserAction.REVISE
        assert result.feedback == "加强安全卖点"
        assert result.approved is False

    def test_redo_action_returns_not_approved(self):
        """redo 操作返回未通过"""
        gate = ApprovalGate()
        result = gate.handle_user_action("test:strategy:1", UserAction.REDO)
        assert result.action == UserAction.REDO
        assert result.approved is False

    @pytest.mark.asyncio
    async def test_timeout_auto_approve(self):
        """超时后自动放行（approve）"""
        gate = ApprovalGate(timeout=0.05)
        artifact = {"full_content": "测试策略", "summary": "摘要", "version": 1}
        result = await gate.wait_for_approval("test_client", "strategy", artifact)
        assert result.action == UserAction.APPROVE
        assert result.approved is True

    @pytest.mark.asyncio
    async def test_user_action_wakes_wait(self):
        """用户操作能唤醒正在等待的协程"""
        gate = ApprovalGate(timeout=30)
        artifact = {"full_content": "测试策略", "summary": "摘要", "version": 1}

        async def user_acts():
            await asyncio.sleep(0.05)
            gate.handle_user_action("test:strategy:1", UserAction.APPROVE)

        task = asyncio.create_task(
            gate.wait_for_approval("test", "strategy", artifact)
        )
        await user_acts()
        result = await task

        assert result.action == UserAction.APPROVE


class TestApprovalGatePendingRequests:
    """待处理请求管理测试"""

    def test_get_pending_request_when_exists(self):
        """请求存在时返回信息"""
        gate = ApprovalGate()
        # 需要一个等待中的请求才能查询
        gate._pending_requests["test:strategy:1"] = type(
            "PendingRequest", (),
            {
                "request_id": "test:strategy:1",
                "client_id": "test",
                "stage": "strategy",
                "artifact": {"full_content": "x", "summary": "", "version": 1},
                "status": "waiting",
            },
        )()
        info = gate.get_pending_request("test:strategy:1")
        assert info is not None
        assert info["request_id"] == "test:strategy:1"
        assert info["stage"] == "strategy"
        assert info["status"] == "waiting"

    def test_get_pending_request_returns_none_when_completed(self):
        """请求已完成时返回 None"""
        gate = ApprovalGate()
        completed = type(
            "PendingRequest", (),
            {
                "request_id": "test:strategy:1",
                "client_id": "test",
                "stage": "strategy",
                "artifact": {"full_content": "x", "summary": "", "version": 1},
                "status": "completed",
            },
        )()
        gate._pending_requests["test:strategy:1"] = completed
        assert gate.get_pending_request("test:strategy:1") is None

    def test_get_pending_requests_by_client(self):
        """按客户端查询待处理请求"""
        gate = ApprovalGate()
        pending = type(
            "PendingRequest", (),
            {
                "request_id": "test:strategy:1",
                "client_id": "test",
                "stage": "strategy",
                "artifact": {"full_content": "x", "summary": "", "version": 1},
                "status": "waiting",
            },
        )()
        gate._pending_requests["test:strategy:1"] = pending
        results = gate.get_pending_requests_by_client("test")
        assert len(results) >= 1
        assert results[0]["stage"] == "strategy"

    def test_cancel_all_requests(self):
        """取消所有请求——设置为 approve 并清理"""
        gate = ApprovalGate()
        import asyncio
        pending = type(
            "PendingRequest", (),
            {
                "request_id": "test:strategy:1",
                "client_id": "test",
                "stage": "strategy",
                "artifact": {"full_content": "x", "summary": "", "version": 1},
                "event": asyncio.Event(),
                "result": None,
                "status": "waiting",
            },
        )()
        gate._pending_requests["test:strategy:1"] = pending
        count = gate.cancel_all_requests("test")
        assert count >= 1


def test_user_action_enum_values():
    """验证枚举值正确"""
    assert UserAction.APPROVE.value == "approve"
    assert UserAction.REVISE.value == "revise"
    assert UserAction.REDO.value == "redo"


def test_approval_result_dataclass():
    """验证 ApprovalResult 数据类"""
    r = ApprovalResult(action=UserAction.APPROVE, approved=True)
    assert r.action == UserAction.APPROVE
    assert r.approved is True
    assert r.feedback is None

    r2 = ApprovalResult(action=UserAction.REVISE, feedback="改", approved=False)
    assert r2.action == UserAction.REVISE
    assert r2.feedback == "改"
    assert r2.approved is False
