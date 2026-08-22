"""HITL 审批机制（Human-in-the-Loop）— 危险操作人在回路确认。

- 权限模式：`readonly`（全拒）/ `auto`（自动过）/ `ask`（询问，默认）；
- agent 执行危险工具前检查，`ask` 模式下挂起并生成审批请求，阻塞等待人工审批；
- 审批接口 approve/reject；超时默认拒绝（default_on_timeout=reject）。
"""

from __future__ import annotations

import threading
import time
import uuid

APPROVAL_TTL_SECONDS = 60  # 审批超时（默认拒绝）

# 危险工具注册表（编辑/删除/覆盖等；随 Gate 6 要素编辑工具加入扩展）
DANGEROUS_TOOLS: set[str] = {
    "add_features",
    "update_features",
    "update_geometry",
    "delete_features",
    "commit_edits",
    "overwrite_output",
}

PERMISSION_MODES = ("readonly", "auto", "ask")


class ApprovalRequest:
    """一次挂起的危险操作审批请求"""

    def __init__(self, tool: str, args: dict, impact: str = "") -> None:
        self.id = uuid.uuid4().hex[:12]
        self.tool = tool
        self.args = dict(args)
        self.impact = impact
        self.status = "pending"  # pending / approved / rejected / timed_out
        self.created_at = time.time()


class ApprovalGate:
    """会话级审批门：危险操作挂起 + approve/reject + 超时兜底"""

    def __init__(self, mode: str = "ask", ttl: int = APPROVAL_TTL_SECONDS) -> None:
        if mode not in PERMISSION_MODES:
            raise ValueError(f"权限模式必须是 {PERMISSION_MODES}，收到: {mode}")
        self.mode = mode
        self.ttl = ttl
        self._requests: dict[str, ApprovalRequest] = {}
        self._lock = threading.Lock()

    # ── 危险操作检查 ──
    def check(self, tool: str, args: dict | None = None) -> dict | None:
        """危险操作前置检查：None=放行；dict=拒绝/挂起"""
        if tool not in DANGEROUS_TOOLS:
            return None
        args = args or {}
        if self.mode == "readonly":
            return {
                "status": "rejected",
                "error": "只读模式：该操作需要人工审批，已拒绝",
                "approval_id": None,
            }
        if self.mode == "auto":
            return None  # 自动放行
        # ask：创建审批请求
        req = ApprovalRequest(tool, args)
        with self._lock:
            self._requests[req.id] = req
        return {
            "status": "pending_approval",
            "approval_id": req.id,
            "tool": tool,
            "args": args,
            "message": "该操作需要人工审批，请在前端确认",
        }

    def wait_for_approval(self, approval_id: str) -> str:
        """阻塞等待审批结果；超时默认拒绝。返回 approved/rejected/timed_out"""
        deadline = time.time() + self.ttl
        while time.time() < deadline:
            with self._lock:
                req = self._requests.get(approval_id)
            if req is not None and req.status != "pending":
                with self._lock:
                    self._requests.pop(approval_id, None)
                return req.status
            time.sleep(0.2)
        # 超时：标记拒绝
        with self._lock:
            req = self._requests.get(approval_id)
            if req is not None:
                req.status = "timed_out"
                self._requests.pop(approval_id, None)
        return "timed_out"

    def resolve(self, approval_id: str, action: str) -> dict:
        """人工审批：approve / reject"""
        if action not in ("approve", "reject"):
            return {"ok": False, "error": f"action 必须是 approve/reject，收到: {action}"}
        with self._lock:
            req = self._requests.get(approval_id)
            if req is None:
                return {"ok": False, "error": "审批请求不存在或已处理"}
            if req.status != "pending":
                return {"ok": False, "error": f"审批已处理（{req.status}）"}
            if time.time() - req.created_at > self.ttl:
                req.status = "timed_out"
                return {"ok": False, "error": "审批已超时（默认拒绝）"}
            req.status = "approved" if action == "approve" else "rejected"
        return {"ok": True, "approval_id": approval_id, "status": req.status}

    def set_mode(self, mode: str) -> None:
        """切换权限模式（会话级）"""
        if mode not in PERMISSION_MODES:
            raise ValueError(f"权限模式必须是 {PERMISSION_MODES}，收到: {mode}")
        self.mode = mode
