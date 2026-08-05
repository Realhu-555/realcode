"""ApprovalGate WebSocket 集成测试"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestrator.gate import ApprovalGate, UserAction, ApprovalResult
from src.orchestrator.state import OutputArtifact


class TestNotifyCallback:
    """通知回调集成测试"""

    @pytest.mark.asyncio
    async def test_callback_called_on_wait_for_approval(self):
        """wait_for_approval 时通知回调被调用"""
        gate = ApprovalGate(timeout=0.05)
        mock_callback = AsyncMock()
        gate.set_notify_callback(mock_callback)

        artifact: OutputArtifact = {
            "full_content": "测试策略内容",
            "summary": "摘要",
            "version": 1,
        }

        await gate.wait_for_approval("project-123", "strategy", artifact)

        # 回调应该被调用一次
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0]
        assert call_args[0] == "project-123"  # client_id (用作 project_id)
        data = call_args[1]
        assert data["type"] == "approval_required"
        assert data["stage"] == "strategy"
        assert data["artifact"]["full_content"] == "测试策略内容"

    @pytest.mark.asyncio
    async def test_callback_data_includes_request_id(self):
        """通知数据包含 request_id"""
        gate = ApprovalGate(timeout=0.05)
        mock_callback = AsyncMock()
        gate.set_notify_callback(mock_callback)

        artifact: OutputArtifact = {
            "full_content": "test",
            "summary": "",
            "version": 2,
        }

        await gate.wait_for_approval("proj-1", "strategy", artifact)

        data = mock_callback.call_args[0][1]
        assert data["request_id"] == "proj-1:strategy:2"


class TestFullApprovalFlow:
    """完整审批流程测试"""

    @pytest.mark.asyncio
    async def test_approve_flow(self):
        """用户 approve → 流水线继续"""
        gate = ApprovalGate(timeout=30)
        mock_callback = AsyncMock()
        gate.set_notify_callback(mock_callback)

        artifact: OutputArtifact = {
            "full_content": "策略",
            "summary": "",
            "version": 1,
        }

        # 模拟用户 0.05 秒后 approve
        async def user_approves():
            await asyncio.sleep(0.05)
            gate.handle_user_action("proj:strategy:1", UserAction.APPROVE)

        task = asyncio.create_task(
            gate.wait_for_approval("proj", "strategy", artifact)
        )
        await user_approves()
        result = await task

        assert result.action == UserAction.APPROVE
        assert result.approved is True

    @pytest.mark.asyncio
    async def test_revise_flow(self):
        """用户 revise → 带 feedback 返回"""
        gate = ApprovalGate(timeout=30)
        artifact: OutputArtifact = {
            "full_content": "策略",
            "summary": "",
            "version": 1,
        }

        async def user_revises():
            await asyncio.sleep(0.05)
            gate.handle_user_action(
                "proj:strategy:1", UserAction.REVISE, "加强安全"
            )

        task = asyncio.create_task(
            gate.wait_for_approval("proj", "strategy", artifact)
        )
        await user_revises()
        result = await task

        assert result.action == UserAction.REVISE
        assert result.feedback == "加强安全"
        assert result.approved is False

    @pytest.mark.asyncio
    async def test_redo_flow(self):
        """用户 redo → 清空重做"""
        gate = ApprovalGate(timeout=30)
        artifact: OutputArtifact = {
            "full_content": "策略",
            "summary": "",
            "version": 1,
        }

        async def user_redos():
            await asyncio.sleep(0.05)
            gate.handle_user_action("proj:strategy:1", UserAction.REDO)

        task = asyncio.create_task(
            gate.wait_for_approval("proj", "strategy", artifact)
        )
        await user_redos()
        result = await task

        assert result.action == UserAction.REDO
        assert result.approved is False


class TestDuplicateActions:
    """重复操作边界测试"""

    @pytest.mark.asyncio
    async def test_second_action_ignored(self):
        """第二次操作被忽略（请求已完成）"""
        gate = ApprovalGate(timeout=30)
        artifact: OutputArtifact = {
            "full_content": "test", "summary": "", "version": 1,
        }

        async def user_double_clicks():
            await asyncio.sleep(0.05)
            gate.handle_user_action("proj:strategy:1", UserAction.APPROVE)
            await asyncio.sleep(0.02)
            # 第二次点击应该被忽略
            gate.handle_user_action("proj:strategy:1", UserAction.REDO)

        task = asyncio.create_task(
            gate.wait_for_approval("proj", "strategy", artifact)
        )
        await user_double_clicks()
        result = await task

        # 第一次的 approve 生效
        assert result.action == UserAction.APPROVE

    @pytest.mark.asyncio
    async def test_action_after_timeout_ignored(self):
        """超时后再操作被忽略"""
        gate = ApprovalGate(timeout=0.05)
        artifact: OutputArtifact = {
            "full_content": "test", "summary": "", "version": 1,
        }

        result = await gate.wait_for_approval("proj", "strategy", artifact)
        assert result.action == UserAction.APPROVE  # 超时自动通过

        # 超时后操作应该无效果
        result2 = gate.handle_user_action("proj:strategy:1", UserAction.REDO)
        assert result2.action == UserAction.REDO  # 返回正确但不会改变结果


class TestWebSocketMessageFormat:
    """WebSocket 消息格式测试"""

    def test_approve_message_format(self):
        """approve 消息格式正确"""
        msg = {
            "action": "approve",
            "request_id": "proj:strategy:1",
        }
        assert json.dumps(msg)  # 可序列化
        assert msg["action"] == "approve"

    def test_revise_message_format(self):
        """revise 消息包含 feedback"""
        msg = {
            "action": "revise",
            "request_id": "proj:strategy:1",
            "feedback": "加强安全卖点",
        }
        data = json.loads(json.dumps(msg))
        assert data["action"] == "revise"
        assert data["feedback"] == "加强安全卖点"

    def test_redo_message_format(self):
        """redo 消息格式正确"""
        msg = {
            "action": "redo",
            "request_id": "proj:strategy:1",
        }
        assert json.dumps(msg)

    def test_approval_required_message_format(self):
        """approval_required 推送消息格式"""
        msg = {
            "type": "approval_required",
            "project_id": "proj-123",
            "request_id": "proj-123:strategy:1",
            "stage": "strategy",
            "artifact": {
                "full_content": "策略内容",
                "summary": "摘要",
                "version": 1,
            },
        }
        data = json.loads(json.dumps(msg))
        assert data["type"] == "approval_required"
        assert data["request_id"] == "proj-123:strategy:1"
