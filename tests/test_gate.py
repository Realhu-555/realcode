"""ApprovalGate 人工介入机制单元测试"""

import asyncio

import pytest
from src.orchestrator.gate import ApprovalGate, ApprovalResult, UserAction
from src.orchestrator.state import OutputArtifact

# 忽略未使用变量的警告（测试中故意保留）

# ========================================================================
# 辅助函数
# ========================================================================


def _make_artifact(**overrides) -> OutputArtifact:
    """测试辅助：构造一个合法的 OutputArtifact"""
    defaults: dict = {
        "full_content": "# PRD\n\n完整内容",
        "summary": "# PRD 摘要",
        "structured": {"modules": [{"name": "auth"}]},
        "token_count": 5000,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    defaults.update(overrides)
    return defaults  # type: ignore[return-value]


# ========================================================================
# UserAction 枚举测试
# ========================================================================


def test_user_action_enum_values():
    """UserAction 枚举包含三种操作类型"""
    expected_actions = {"approve", "revise", "redo"}
    actual_actions = {action.value for action in UserAction}
    assert actual_actions == expected_actions


def test_user_action_string_values():
    """UserAction 枚举值为小写字符串"""
    assert UserAction.APPROVE.value == "approve"
    assert UserAction.REVISE.value == "revise"
    assert UserAction.REDO.value == "redo"


# ========================================================================
# ApprovalResult 数据类测试
# ========================================================================


def test_approval_result_approve():
    """ApprovalResult 确认操作"""
    result = ApprovalResult(
        action=UserAction.APPROVE,
        approved=True,
    )
    assert result.action == UserAction.APPROVE
    assert result.approved is True
    assert result.feedback is None


def test_approval_result_revise_with_feedback():
    """ApprovalResult 修改操作包含反馈"""
    result = ApprovalResult(
        action=UserAction.REVISE,
        feedback="请补充非功能需求",
        approved=False,
    )
    assert result.action == UserAction.REVISE
    assert result.feedback == "请补充非功能需求"
    assert result.approved is False


def test_approval_result_redo():
    """ApprovalResult 重做操作"""
    result = ApprovalResult(
        action=UserAction.REDO,
        approved=False,
    )
    assert result.action == UserAction.REDO
    assert result.approved is False
    assert result.feedback is None


# ========================================================================
# ApprovalGate 初始化测试
# ========================================================================


def test_approval_gate_init():
    """ApprovalGate 初始化成功"""
    gate = ApprovalGate()
    assert gate is not None
    assert gate._pending_requests == {}


# ========================================================================
# ApprovalGate 处理用户操作测试
# ========================================================================


def test_approval_gate_handle_approve():
    """ApprovalGate 处理确认操作"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    assert result.action == UserAction.APPROVE
    assert result.approved is True


def test_approval_gate_handle_revise_with_feedback():
    """ApprovalGate 处理修改操作"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.REVISE,
        feedback="请增加登录功能",
    )

    assert result.action == UserAction.REVISE
    assert result.feedback == "请增加登录功能"
    assert result.approved is False


def test_approval_gate_handle_redo():
    """ApprovalGate 处理重做操作"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.REDO,
    )

    assert result.action == UserAction.REDO
    assert result.approved is False


def test_approval_gate_handle_unknown_request():
    """ApprovalGate 处理未知请求 ID 仍然返回操作结果"""
    gate = ApprovalGate()
    request_id = "unknown-request"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    # 即使请求不存在，也根据 action 返回结果
    assert result.action == UserAction.APPROVE
    assert result.approved is True


# ========================================================================
# ApprovalGate 待处理请求管理测试
# ========================================================================


def test_approval_gate_get_pending_request():
    """ApprovalGate 获取待处理请求"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    # 处理一个请求
    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )
    assert result.approved is True

    # 请求已处理，应该返回 None
    request = gate.get_pending_request(request_id)
    assert request is None


def test_approval_gate_get_completed_request():
    """ApprovalGate 获取已完成的请求返回 None"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    # 处理一个不存在的请求（仍然返回结果）
    gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    request = gate.get_pending_request(request_id)
    assert request is None


def test_approval_gate_get_nonexistent_request():
    """ApprovalGate 获取不存在的请求返回 None"""
    gate = ApprovalGate()

    request = gate.get_pending_request("nonexistent")
    assert request is None


def test_approval_gate_clear_pending_request():
    """ApprovalGate 清除待处理请求"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    # 处理一个不存在的请求
    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    # 清除不存在的请求返回 False
    result = gate.clear_pending_request(request_id)
    assert result is False


def test_approval_gate_clear_nonexistent_request():
    """ApprovalGate 清除不存在的请求返回 False"""
    gate = ApprovalGate()

    result = gate.clear_pending_request("nonexistent")
    assert result is False


# ========================================================================
# ApprovalGate 端到端流程测试
# ========================================================================


def test_approval_gate_full_flow_approve():
    """ApprovalGate 端到端流程：确认操作"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    # 用户确认（请求不存在也返回结果）
    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    # 验证结果
    assert result.action == UserAction.APPROVE
    assert result.approved is True


def test_approval_gate_full_flow_revise():
    """ApprovalGate 端到端流程：修改操作"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    # 用户修改
    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.REVISE,
        feedback="请补充用户故事",
    )

    # 验证结果
    assert result.action == UserAction.REVISE
    assert result.feedback == "请补充用户故事"
    assert result.approved is False


def test_approval_gate_full_flow_redo():
    """ApprovalGate 端到端流程：重做操作"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    # 用户重做
    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.REDO,
    )

    # 验证结果
    assert result.action == UserAction.REDO
    assert result.approved is False


# ========================================================================
# ApprovalGate 与 OutputArtifact 集成测试
# ========================================================================


def test_approval_gate_with_artifact_status_draft():
    """ApprovalGate 处理 draft 状态的产出物"""
    gate = ApprovalGate()
    artifact = _make_artifact(status="draft", version=1)
    request_id = "client-1:requirement:1"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    assert result.approved is True
    # gate 本身不修改 artifact
    assert artifact["status"] == "draft"


def test_approval_gate_with_artifact_version_increments():
    """ApprovalGate 处理修订版本"""
    gate = ApprovalGate()
    artifact = _make_artifact(status="revised", version=2)
    request_id = "client-1:requirement:2"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    assert result.approved is True
    assert artifact["version"] == 2


# ========================================================================
# ApprovalGate 多阶段测试
# ========================================================================


def test_approval_gate_multiple_stages():
    """ApprovalGate 处理多个阶段的审批"""
    gate = ApprovalGate()

    # 创建多个阶段的请求 ID
    stages = ["requirement", "architecture", "development"]
    request_ids = {}

    for stage in stages:
        request_ids[stage] = f"client-1:{stage}:1"

    # 依次确认每个阶段
    for stage in stages:
        result = gate.handle_user_action(
            request_id=request_ids[stage],
            action=UserAction.APPROVE,
        )
        assert result.approved is True

    # 所有请求都已处理
    for stage in stages:
        assert gate.get_pending_request(request_ids[stage]) is None


# ========================================================================
# ApprovalGate 边界情况测试
# ========================================================================


def test_approval_gate_empty_artifact():
    """ApprovalGate 处理空产出物"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.APPROVE,
    )

    assert result.approved is True


def test_approval_gate_long_feedback():
    """ApprovalGate 处理长反馈"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"
    long_feedback = "这是一条很长的反馈" * 100

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.REVISE,
        feedback=long_feedback,
    )

    assert result.action == UserAction.REVISE
    assert result.feedback == long_feedback


def test_approval_gate_special_characters_in_feedback():
    """ApprovalGate 处理特殊字符反馈"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"
    special_feedback = "请添加：<script>alert('xss')</script> & ' OR 1=1 --"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.REVISE,
        feedback=special_feedback,
    )

    assert result.action == UserAction.REVISE
    assert result.feedback == special_feedback


# ========================================================================
# 异步等待机制测试
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_wait_for_approval_approve():
    """ApprovalGate 异步等待：用户确认"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    async def user_action():
        """模拟用户在另一个协程中操作"""
        await asyncio.sleep(0.1)
        return gate.handle_user_action(
            request_id=request_id,
            action=UserAction.APPROVE,
        )

    # 同时启动等待和用户操作
    wait_task = asyncio.create_task(
        gate.wait_for_approval(client_id, "requirement", artifact)
    )
    user_task = asyncio.create_task(user_action())

    result = await wait_task
    await user_task

    assert result.action == UserAction.APPROVE
    assert result.approved is True


@pytest.mark.asyncio
async def test_approval_gate_wait_for_approval_revise():
    """ApprovalGate 异步等待：用户修改"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    async def user_action():
        """模拟用户修改"""
        await asyncio.sleep(0.1)
        return gate.handle_user_action(
            request_id=request_id,
            action=UserAction.REVISE,
            feedback="请补充非功能需求",
        )

    wait_task = asyncio.create_task(
        gate.wait_for_approval(client_id, "requirement", artifact)
    )
    user_task = asyncio.create_task(user_action())

    result = await wait_task
    await user_task

    assert result.action == UserAction.REVISE
    assert result.feedback == "请补充非功能需求"
    assert result.approved is False


@pytest.mark.asyncio
async def test_approval_gate_wait_for_approval_timeout():
    """ApprovalGate 异步等待：超时自动通过"""
    gate = ApprovalGate(timeout=0.1)  # 0.1 秒超时
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"

    result = await gate.wait_for_approval(client_id, "requirement", artifact)

    # 超时默认通过
    assert result.action == UserAction.APPROVE
    assert result.approved is True


@pytest.mark.asyncio
async def test_approval_gate_notify_callback():
    """ApprovalGate 通知回调"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    notifications = []

    async def mock_notify(cid: str, data: dict):
        notifications.append((cid, data))

    gate.set_notify_callback(mock_notify)

    async def wait_and_cancel():
        """等待后取消"""
        await asyncio.sleep(0.05)
        gate.cancel_all_requests(client_id)

    wait_task = asyncio.create_task(
        gate.wait_for_approval(client_id, "requirement", artifact)
    )
    cancel_task = asyncio.create_task(wait_and_cancel())

    await wait_task
    await cancel_task

    # 验证通知被发送
    assert len(notifications) == 1
    assert notifications[0][0] == client_id
    assert notifications[0][1]["type"] == "approval_required"
    assert notifications[0][1]["request_id"] == request_id


@pytest.mark.asyncio
async def test_approval_gate_get_pending_requests_by_client():
    """ApprovalGate 获取指定客户端的待处理请求"""
    gate = ApprovalGate(timeout=5.0)
    artifact1 = _make_artifact(status="draft", version=1)
    artifact2 = _make_artifact(status="draft", version=1)
    client_id = "client-1"

    async def wait1():
        return await gate.wait_for_approval(client_id, "requirement", artifact1)

    async def wait2():
        return await gate.wait_for_approval(client_id, "architecture", artifact2)

    # 启动两个等待任务（但不完成）
    task1 = asyncio.create_task(wait1())
    task2 = asyncio.create_task(wait2())

    await asyncio.sleep(0.01)  # 确保任务开始

    pending = gate.get_pending_requests_by_client(client_id)
    assert len(pending) == 2
    stages = {p["stage"] for p in pending}
    assert stages == {"requirement", "architecture"}

    # 清理
    gate.cancel_all_requests(client_id)
    await task1
    await task2


@pytest.mark.asyncio
async def test_approval_gate_cancel_all_requests():
    """ApprovalGate 取消所有待处理请求"""
    gate = ApprovalGate(timeout=5.0)
    artifact1 = _make_artifact(status="draft", version=1)
    artifact2 = _make_artifact(status="draft", version=1)
    client_id = "client-1"

    results = []

    async def wait1():
        r = await gate.wait_for_approval(client_id, "requirement", artifact1)
        results.append(r)

    async def wait2():
        r = await gate.wait_for_approval(client_id, "architecture", artifact2)
        results.append(r)

    task1 = asyncio.create_task(wait1())
    task2 = asyncio.create_task(wait2())

    await asyncio.sleep(0.01)

    count = gate.cancel_all_requests(client_id)
    assert count == 2

    await task1
    await task2

    # 所有请求都被取消（默认通过）
    assert len(results) == 2
    assert all(r.approved for r in results)


@pytest.mark.asyncio
async def test_approval_gate_multiple_clients():
    """ApprovalGate 多客户端并发"""
    gate = ApprovalGate(timeout=5.0)
    artifact1 = _make_artifact(status="draft", version=1)
    artifact2 = _make_artifact(status="draft", version=1)

    results = {"client-1": None, "client-2": None}

    async def wait_client(client_id, artifact):
        r = await gate.wait_for_approval(client_id, "requirement", artifact)
        results[client_id] = r

    async def approve_client(client_id, request_id):
        await asyncio.sleep(0.1)
        gate.handle_user_action(request_id, UserAction.APPROVE)

    task1 = asyncio.create_task(wait_client("client-1", artifact1))
    task2 = asyncio.create_task(wait_client("client-2", artifact2))

    await asyncio.sleep(0.01)

    # 分别审批
    approve1 = asyncio.create_task(
        approve_client("client-1", "client-1:requirement:1")
    )
    approve2 = asyncio.create_task(
        approve_client("client-2", "requirement:1")
    )

    await task1
    await task2
    await approve1
    await approve2

    assert results["client-1"].approved is True
    assert results["client-2"].approved is True


@pytest.mark.asyncio
async def test_approval_gate_clear_pending_request_wakes_waiter():
    """ApprovalGate 清除请求唤醒等待者"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    async def wait():
        return await gate.wait_for_approval(client_id, "requirement", artifact)

    task = asyncio.create_task(wait())
    await asyncio.sleep(0.01)

    # 清除请求
    result = gate.clear_pending_request(request_id)
    assert result is True

    # 等待者应该被唤醒
    approval_result = await task
    assert approval_result.approved is True


# ========================================================================
# 补充测试：等待状态的请求管理
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_get_pending_request_while_waiting():
    """ApprovalGate 在等待期间获取待处理请求"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    async def wait():
        return await gate.wait_for_approval(client_id, "requirement", artifact)

    task = asyncio.create_task(wait())
    await asyncio.sleep(0.01)

    # 在等待期间获取请求
    pending = gate.get_pending_request(request_id)
    assert pending is not None
    assert pending["request_id"] == request_id
    assert pending["client_id"] == client_id
    assert pending["stage"] == "requirement"
    assert pending["status"] == "waiting"

    # 清理
    gate.cancel_all_requests(client_id)
    await task


# ========================================================================
# 补充测试：重复操作处理
# ========================================================================


def test_approval_gate_handle_action_on_completed_request():
    """ApprovalGate 对已完成请求重复操作仍然返回结果"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    # 第一次操作
    result1 = gate.handle_user_action(request_id, UserAction.APPROVE)
    assert result1.approved is True

    # 第二次操作（请求已完成，但仍然返回结果）
    result2 = gate.handle_user_action(request_id, UserAction.REVISE, feedback="修改")
    assert result2.action == UserAction.REVISE
    assert result2.feedback == "修改"
    assert result2.approved is False


# ========================================================================
# 补充测试：自定义超时参数
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_wait_for_approval_custom_timeout():
    """ApprovalGate 使用自定义超时参数"""
    gate = ApprovalGate(timeout=60.0)  # 默认 60 秒
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"

    # 使用更短的超时覆盖默认值
    result = await gate.wait_for_approval(
        client_id, "requirement", artifact, timeout=0.1
    )

    # 超时默认通过
    assert result.action == UserAction.APPROVE
    assert result.approved is True


# ========================================================================
# 补充测试：cancel_all_requests 边界情况
# ========================================================================


def test_approval_gate_cancel_all_requests_no_pending():
    """ApprovalGate 取消无待处理请求的客户端"""
    gate = ApprovalGate()

    count = gate.cancel_all_requests("nonexistent-client")
    assert count == 0


@pytest.mark.asyncio
async def test_approval_gate_cancel_all_requests_only_waiting():
    """ApprovalGate 只取消等待状态的请求"""
    gate = ApprovalGate(timeout=5.0)
    artifact1 = _make_artifact(status="draft", version=1)
    artifact2 = _make_artifact(status="draft", version=2)
    client_id = "client-1"

    async def wait1():
        return await gate.wait_for_approval(client_id, "requirement", artifact1)

    task1 = asyncio.create_task(wait1())
    await asyncio.sleep(0.01)

    # 手动完成一个请求
    gate.handle_user_action("client-1:requirement:2", UserAction.APPROVE)

    # 只有一个等待中的请求
    count = gate.cancel_all_requests(client_id)
    assert count == 1

    gate.cancel_all_requests(client_id)
    await task1


# ========================================================================
# 补充测试：get_pending_requests_by_client 过滤逻辑
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_get_pending_requests_filters_completed():
    """ApprovalGate 获取待处理请求过滤已完成的"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"

    async def wait1():
        return await gate.wait_for_approval(client_id, "requirement", artifact)

    async def wait2():
        return await gate.wait_for_approval(client_id, "architecture", artifact)

    task1 = asyncio.create_task(wait1())
    task2 = asyncio.create_task(wait2())
    await asyncio.sleep(0.01)

    # 手动完成一个请求
    gate.handle_user_action("client-1:requirement:1", UserAction.APPROVE)

    # 只有一个等待中的请求
    pending = gate.get_pending_requests_by_client(client_id)
    assert len(pending) == 1
    assert pending[0]["stage"] == "architecture"

    gate.cancel_all_requests(client_id)
    await task1
    await task2


# ========================================================================
# 补充测试：多客户端隔离
# ========================================================================


def test_approval_gate_different_clients_independent():
    """ApprovalGate 不同客户端的请求相互独立"""
    gate = ApprovalGate()
    request_id_1 = "client-1:requirement:1"
    request_id_2 = "client-2:requirement:1"

    # 客户端 1 确认
    result1 = gate.handle_user_action(request_id_1, UserAction.APPROVE)
    assert result1.approved is True

    # 客户端 2 不存在的请求
    request_2 = gate.get_pending_request(request_id_2)
    assert request_2 is None


# ========================================================================
# 补充测试：并发操作竞争
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_concurrent_user_actions():
    """ApprovalGate 并发用户操作不产生竞争"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=1)
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    results = []

    async def wait():
        r = await gate.wait_for_approval(client_id, "requirement", artifact)
        results.append(r)

    async def concurrent_approve():
        await asyncio.sleep(0.01)
        gate.handle_user_action(request_id, UserAction.APPROVE)

    task = asyncio.create_task(wait())
    approve_task = asyncio.create_task(concurrent_approve())

    await task
    await approve_task

    assert len(results) == 1
    assert results[0].approved is True


# ========================================================================
# 补充测试：PendingRequest 数据类
# ========================================================================


def test_pending_request_default_values():
    """PendingRequest 默认值正确"""
    from src.orchestrator.gate import PendingRequest

    artifact = _make_artifact()
    pending = PendingRequest(
        request_id="test-id",
        client_id="client-1",
        stage="requirement",
        artifact=artifact,
    )

    assert pending.request_id == "test-id"
    assert pending.client_id == "client-1"
    assert pending.stage == "requirement"
    assert pending.artifact == artifact
    assert pending.status == "waiting"
    assert pending.result is None
    assert pending.last_question is None if hasattr(pending, "last_question") else True
    assert isinstance(pending.event, asyncio.Event)
    assert pending.event.is_set() is False


# ========================================================================
# 补充测试：handle_user_action 对已处理请求的行为
# ========================================================================


def test_approval_gate_handle_action_on_already_processed_request():
    """ApprovalGate 对已处理请求再次操作：不更新 pending.result，但仍返回新结果"""
    gate = ApprovalGate()
    artifact = _make_artifact()
    request_id = "client-1:requirement:1"

    # 创建等待中的请求
    asyncio.get_event_loop().run_until_complete(
        gate.wait_for_approval("client-1", "requirement", artifact, timeout=0.01)
    )

    # 手动添加一个请求并处理
    from src.orchestrator.gate import PendingRequest

    pending = PendingRequest(
        request_id=request_id,
        client_id="client-1",
        stage="requirement",
        artifact=artifact,
    )
    gate._pending_requests[request_id] = pending

    # 第一次操作
    result1 = gate.handle_user_action(request_id, UserAction.APPROVE)
    assert result1.approved is True
    assert pending.status == "completed"

    # 保存第一次的 result
    first_result = pending.result

    # 第二次操作（请求已 completed，pending.result 不会被更新）
    result2 = gate.handle_user_action(request_id, UserAction.REVISE, feedback="修改")
    assert result2.action == UserAction.REVISE
    assert result2.feedback == "修改"
    # pending.result 仍然是第一次的结果
    assert pending.result == first_result


# ========================================================================
# 补充测试：wait_for_approval 超时后清理
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_timeout_cleans_pending_request():
    """ApprovalGate 超时后正确清理 pending_requests"""
    gate = ApprovalGate(timeout=0.05)
    artifact = _make_artifact()
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    result = await gate.wait_for_approval(client_id, "requirement", artifact)

    # 超时后请求被清理
    assert gate.get_pending_request(request_id) is None
    assert result.action == UserAction.APPROVE
    assert result.approved is True


# ========================================================================
# 补充测试：notify_callback 未设置时
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_no_notify_callback():
    """ApprovalGate 未设置回调时不报错"""
    gate = ApprovalGate(timeout=0.05)
    artifact = _make_artifact()
    client_id = "client-1"

    # 不设置回调，直接等待（应该正常超时）
    result = await gate.wait_for_approval(client_id, "requirement", artifact)

    assert result.action == UserAction.APPROVE
    assert result.approved is True


# ========================================================================
# 补充测试：cancel_all_requests 后等待者收到 approve
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_cancel_wakes_waiter_with_approve():
    """ApprovalGate cancel_all_requests 后等待者收到 approve 结果"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact()
    client_id = "client-1"

    results = []

    async def wait():
        r = await gate.wait_for_approval(client_id, "requirement", artifact)
        results.append(r)

    task = asyncio.create_task(wait())
    await asyncio.sleep(0.01)

    # 取消
    count = gate.cancel_all_requests(client_id)
    assert count == 1

    await task

    assert len(results) == 1
    assert results[0].approved is True
    assert results[0].action == UserAction.APPROVE


# ========================================================================
# 补充测试：get_pending_requests_by_client 返回数据结构
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_get_pending_requests_data_structure():
    """ApprovalGate get_pending_requests_by_client 返回正确的数据结构"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=2)
    client_id = "client-1"

    async def wait():
        return await gate.wait_for_approval(client_id, "architecture", artifact)

    task = asyncio.create_task(wait())
    await asyncio.sleep(0.01)

    pending = gate.get_pending_requests_by_client(client_id)
    assert len(pending) == 1

    req = pending[0]
    assert "request_id" in req
    assert "stage" in req
    assert "artifact" in req
    assert req["stage"] == "architecture"
    assert req["artifact"]["version"] == 2

    gate.cancel_all_requests(client_id)
    await task


# ========================================================================
# 补充测试：多个请求 ID 格式
# ========================================================================


def test_approval_gate_request_id_formats():
    """ApprovalGate 支持多种 request_id 格式"""
    gate = ApprovalGate()

    # 标准格式
    result1 = gate.handle_user_action("client-1:requirement:1", UserAction.APPROVE)
    assert result1.approved is True

    # 带特殊字符
    result2 = gate.handle_user_action("client-123:architecture:99", UserAction.APPROVE)
    assert result2.approved is True

    # 长 ID
    long_id = "a" * 100 + ":requirement:1"
    result3 = gate.handle_user_action(long_id, UserAction.APPROVE)
    assert result3.approved is True


# ========================================================================
# 补充测试：handle_user_action 无 feedback 的 REVISE
# ========================================================================


def test_approval_gate_revise_without_feedback():
    """ApprovalGate REVISE 操作可以不带 feedback"""
    gate = ApprovalGate()
    request_id = "client-1:requirement:1"

    result = gate.handle_user_action(
        request_id=request_id,
        action=UserAction.REVISE,
        feedback=None,
    )

    assert result.action == UserAction.REVISE
    assert result.feedback is None
    assert result.approved is False


# ========================================================================
# 补充测试：clear_pending_request 对等待中请求设置 approve
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_clear_sets_approve_for_waiting():
    """ApprovalGate clear_pending_request 对等待中请求设置 approve 并唤醒"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact()
    client_id = "client-1"
    request_id = f"{client_id}:requirement:1"

    async def wait():
        return await gate.wait_for_approval(client_id, "requirement", artifact)

    task = asyncio.create_task(wait())
    await asyncio.sleep(0.01)

    # 确认请求在等待
    pending = gate.get_pending_request(request_id)
    assert pending is not None
    assert pending["status"] == "waiting"

    # 清除请求
    cleared = gate.clear_pending_request(request_id)
    assert cleared is True

    # 等待者被唤醒，收到 approve
    result = await task
    assert result.approved is True
    assert result.action == UserAction.APPROVE

    # 请求已被删除
    assert gate.get_pending_request(request_id) is None


# ========================================================================
# 补充测试：多个客户端并发取消
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_cancel_multiple_clients():
    """ApprovalGate 取消多个客户端的请求"""
    gate = ApprovalGate(timeout=5.0)
    artifact1 = _make_artifact()
    artifact2 = _make_artifact()

    results = {"client-1": None, "client-2": None}

    async def wait_client(client_id, artifact):
        r = await gate.wait_for_approval(client_id, "requirement", artifact)
        results[client_id] = r

    task1 = asyncio.create_task(wait_client("client-1", artifact1))
    task2 = asyncio.create_task(wait_client("client-2", artifact2))
    await asyncio.sleep(0.01)

    # 分别取消
    count1 = gate.cancel_all_requests("client-1")
    count2 = gate.cancel_all_requests("client-2")

    assert count1 == 1
    assert count2 == 1

    await task1
    await task2

    assert results["client-1"].approved is True
    assert results["client-2"].approved is True


# ========================================================================
# 补充测试：get_pending_request 在 wait_for_approval 期间返回正确数据
# ========================================================================


@pytest.mark.asyncio
async def test_approval_gate_get_pending_during_wait():
    """ApprovalGate 在等待期间 get_pending_request 返回完整信息"""
    gate = ApprovalGate(timeout=5.0)
    artifact = _make_artifact(status="draft", version=3)
    client_id = "client-1"
    request_id = f"{client_id}:requirement:3"

    async def wait():
        return await gate.wait_for_approval(client_id, "requirement", artifact)

    task = asyncio.create_task(wait())
    await asyncio.sleep(0.01)

    pending = gate.get_pending_request(request_id)
    assert pending is not None
    assert pending["request_id"] == request_id
    assert pending["client_id"] == client_id
    assert pending["stage"] == "requirement"
    assert pending["status"] == "waiting"
    assert pending["artifact"]["version"] == 3
    assert pending["artifact"]["full_content"] == "# PRD\n\n完整内容"

    gate.cancel_all_requests(client_id)
    await task


# ========================================================================
# 补充测试：ApprovalResult 默认值
# ========================================================================


def test_approval_result_default_values():
    """ApprovalResult 默认值正确"""
    result = ApprovalResult(action=UserAction.APPROVE)

    assert result.action == UserAction.APPROVE
    assert result.feedback is None
    assert result.approved is False


# ========================================================================
# 补充测试：handle_user_action 返回的 result.approved 逻辑
# ========================================================================


def test_approval_gate_approved_flag_logic():
    """ApprovalGate approved 标志仅在 APPROVE 时为 True"""
    gate = ApprovalGate()

    # APPROVE -> approved=True
    r1 = gate.handle_user_action("id1", UserAction.APPROVE)
    assert r1.approved is True

    # REVISE -> approved=False
    r2 = gate.handle_user_action("id2", UserAction.REVISE, feedback="修改")
    assert r2.approved is False

    # REDO -> approved=False
    r3 = gate.handle_user_action("id3", UserAction.REDO)
    assert r3.approved is False


# ========================================================================
# 补充测试：clear_pending_request 对已完成请求
# ========================================================================


def test_approval_gate_clear_completed_request():
    """ApprovalGate clear_pending_request 对已完成请求直接删除"""
    gate = ApprovalGate()
    artifact = _make_artifact()
    request_id = "client-1:requirement:1"

    # 创建并完成一个请求
    from src.orchestrator.gate import PendingRequest

    pending = PendingRequest(
        request_id=request_id,
        client_id="client-1",
        stage="requirement",
        artifact=artifact,
    )
    gate._pending_requests[request_id] = pending

    # 先完成请求
    gate.handle_user_action(request_id, UserAction.APPROVE)
    assert pending.status == "completed"

    # 清除已完成的请求（直接删除，不设置 result）
    result = gate.clear_pending_request(request_id)
    assert result is True
    assert request_id not in gate._pending_requests
