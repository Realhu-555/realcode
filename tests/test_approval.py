"""HITL 审批门单测 — 权限模式 / approve/reject / 超时兜底"""

import threading
import time

import pytest
from src.gis_toolkit.approval import ApprovalGate


def test_readonly_rejects():
    gate = ApprovalGate("readonly")
    r = gate.check("delete_features", {"ids": [1]})
    assert r["status"] == "rejected"
    assert r["approval_id"] is None


def test_auto_allows():
    gate = ApprovalGate("auto")
    assert gate.check("delete_features", {}) is None


def test_safe_tool_always_allows():
    gate = ApprovalGate("ask")
    assert gate.check("choropleth", {}) is None


def test_ask_pending_then_approve():
    gate = ApprovalGate("ask", ttl=15)
    r = gate.check("delete_features", {"ids": [1, 2]})
    assert r["status"] == "pending_approval"
    assert r["approval_id"]

    holder: dict = {}

    def approve_later():
        time.sleep(0.3)
        holder["res"] = gate.resolve(r["approval_id"], "approve")

    t = threading.Thread(target=approve_later)
    t.start()
    verdict = gate.wait_for_approval(r["approval_id"])
    t.join(timeout=10)
    assert verdict == "approved"
    assert holder["res"]["ok"] is True


def test_ask_reject():
    gate = ApprovalGate("ask", ttl=15)
    r = gate.check("delete_features", {})
    gate.resolve(r["approval_id"], "reject")
    verdict = gate.wait_for_approval(r["approval_id"])
    assert verdict == "rejected"


def test_timeout_defaults_reject():
    gate = ApprovalGate("ask", ttl=1)
    r = gate.check("delete_features", {})
    verdict = gate.wait_for_approval(r["approval_id"])
    assert verdict == "timed_out"


def test_resolve_unknown_id():
    gate = ApprovalGate()
    assert gate.resolve("nope1234abcd", "approve")["ok"] is False


def test_double_resolve_fails():
    gate = ApprovalGate("ask", ttl=15)
    r = gate.check("delete_features", {})
    assert gate.resolve(r["approval_id"], "approve")["ok"] is True
    assert gate.resolve(r["approval_id"], "approve")["ok"] is False


def test_set_mode():
    gate = ApprovalGate("ask")
    gate.set_mode("readonly")
    assert gate.mode == "readonly"
    with pytest.raises(ValueError):
        gate.set_mode("bogus")
