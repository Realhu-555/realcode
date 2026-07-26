"""ApprovalGate 人工介入机制"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.orchestrator.state import OutputArtifact

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 300  # 5 分钟


class UserAction(str, Enum):
    """用户对产出的操作类型"""

    APPROVE = "approve"  # 确认通过
    REVISE = "revise"  # 提出修改意见
    REDO = "redo"  # 要求重做


@dataclass
class ApprovalResult:
    """审批结果"""

    action: UserAction
    feedback: str | None = None  # 修改意见（仅 REVISE 时有值）
    approved: bool = False  # 是否通过（兼容旧逻辑）


@dataclass
class PendingRequest:
    """待处理的审批请求"""

    request_id: str
    client_id: str
    stage: str
    artifact: OutputArtifact
    event: asyncio.Event = field(default_factory=asyncio.Event)
    result: ApprovalResult | None = None
    status: str = "waiting"


class ApprovalGate:
    """人工确认门

    在每个需要人工确认的阶段暂停流水线，等待用户操作。

    使用方式：
        gate = ApprovalGate()

        # 方式1：直接等待（阻塞直到用户操作或超时）
        result = await gate.wait_for_approval(client_id, "requirement", artifact)
        if result.action == UserAction.APPROVE:
            # 继续下一阶段
        elif result.action == UserAction.REVISE:
            # 根据 feedback 重新生成
        elif result.action == UserAction.REDO:
            # 完全重做

        # 方式2：通过回调推送（用于 WebSocket）
        gate.set_notify_callback(ws_manager.send)
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        """初始化 ApprovalGate

        Args:
            timeout: 等待用户操作的超时时间（秒），默认 300 秒
        """
        self._timeout = timeout
        self._pending_requests: dict[str, PendingRequest] = {}
        self._notify_callback: Callable[[str, dict], Awaitable[None]] | None = None

    def set_notify_callback(
        self, callback: Callable[[str, dict], Awaitable[None]]
    ) -> None:
        """设置通知回调（用于 WebSocket 推送）

        Args:
            callback: 异步回调函数，参数为 (client_id, data)
        """
        self._notify_callback = callback

    async def wait_for_approval(
        self,
        client_id: str,
        stage: str,
        artifact: OutputArtifact,
        timeout: float | None = None,
    ) -> ApprovalResult:
        """暂停流水线，等待用户操作

        Args:
            client_id: 客户端 ID（用于区分不同用户会话）
            stage: 当前阶段名称
            artifact: 当前阶段的产出物
            timeout: 超时时间（秒），None 则使用默认值

        Returns:
            ApprovalResult: 用户的操作结果

        Raises:
            asyncio.TimeoutError: 等待超时
        """
        timeout = timeout if timeout is not None else self._timeout
        request_id = f"{client_id}:{stage}:{artifact['version']}"

        # 创建待处理请求
        pending = PendingRequest(
            request_id=request_id,
            client_id=client_id,
            stage=stage,
            artifact=artifact,
        )
        self._pending_requests[request_id] = pending

        # 通知用户（如果设置了回调）
        if self._notify_callback:
            await self._notify_callback(
                client_id,
                {
                    "type": "approval_required",
                    "request_id": request_id,
                    "stage": stage,
                    "artifact": {
                        "full_content": artifact.get("full_content", ""),
                        "summary": artifact.get("summary", ""),
                        "version": artifact.get("version", 1),
                    },
                },
            )

        # 等待用户操作或超时
        try:
            await asyncio.wait_for(pending.event.wait(), timeout=timeout)
        except TimeoutError:
            pending.status = "timeout"
            self._pending_requests.pop(request_id, None)
            # 超时默认为通过
            return ApprovalResult(
                action=UserAction.APPROVE,
                approved=True,
            )

        # 获取用户操作结果
        result = pending.result or ApprovalResult(
            action=UserAction.APPROVE,
            approved=True,
        )

        # 清理
        self._pending_requests.pop(request_id, None)

        return result

    def handle_user_action(
        self,
        request_id: str,
        action: UserAction,
        feedback: str | None = None,
    ) -> ApprovalResult:
        """处理用户操作

        Args:
            request_id: 请求 ID
            action: 用户操作类型
            feedback: 修改意见（仅 REVISE 时需要）

        Returns:
            ApprovalResult: 处理结果
        """
        result = ApprovalResult(
            action=action,
            feedback=feedback,
            approved=(action == UserAction.APPROVE),
        )

        pending = self._pending_requests.get(request_id)
        if pending and pending.status == "waiting":
            pending.result = result
            pending.status = "completed"
            # 触发 Event，唤醒等待的协程
            pending.event.set()

        return result

    def get_pending_request(self, request_id: str) -> dict[str, Any] | None:
        """获取待处理请求

        Args:
            request_id: 请求 ID

        Returns:
            请求信息，如果不存在或已完成则返回 None
        """
        pending = self._pending_requests.get(request_id)
        if pending and pending.status == "waiting":
            return {
                "request_id": pending.request_id,
                "client_id": pending.client_id,
                "stage": pending.stage,
                "artifact": pending.artifact,
                "status": pending.status,
            }
        return None

    def clear_pending_request(self, request_id: str) -> bool:
        """清除待处理请求

        Args:
            request_id: 请求 ID

        Returns:
            是否成功清除
        """
        pending = self._pending_requests.get(request_id)
        if pending:
            # 如果请求还在等待中，设置超时结果
            if pending.status == "waiting":
                pending.result = ApprovalResult(
                    action=UserAction.APPROVE,
                    approved=True,
                )
                pending.event.set()
            del self._pending_requests[request_id]
            return True
        return False

    def get_pending_requests_by_client(self, client_id: str) -> list[dict[str, Any]]:
        """获取指定客户端的所有待处理请求

        Args:
            client_id: 客户端 ID

        Returns:
            待处理请求列表
        """
        return [
            {
                "request_id": pending.request_id,
                "stage": pending.stage,
                "artifact": pending.artifact,
            }
            for pending in self._pending_requests.values()
            if pending.client_id == client_id and pending.status == "waiting"
        ]

    def cancel_all_requests(self, client_id: str) -> int:
        """取消指定客户端的所有待处理请求

        Args:
            client_id: 客户端 ID

        Returns:
            取消的请求数量
        """
        count = 0
        to_remove = []
        for request_id, pending in self._pending_requests.items():
            if pending.client_id == client_id and pending.status == "waiting":
                pending.result = ApprovalResult(
                    action=UserAction.APPROVE,
                    approved=True,
                )
                pending.event.set()
                to_remove.append(request_id)
                count += 1

        for request_id in to_remove:
            del self._pending_requests[request_id]

        return count
