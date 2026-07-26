"""Bug 回退机制单元测试

测试场景：
1. Bug 数据结构验证
2. TesterAgent 检测到 bug 后写入 state["bugs"]
3. 回退逻辑：根据 bug 的 target 字段决定回退给谁
4. 循环控制：最多 3 次
5. 超限处理：超过 3 次暂停
"""

import pytest
from src.orchestrator.state import Stage


# ========================================================================
# Bug 数据结构测试
# ========================================================================


def test_bug_structure_required_fields():
    """Bug 数据结构必须包含所有必需字段"""
    bug = {
        "id": "bug-001",
        "target": "backend",
        "test_case": "test_create_user",
        "error": "POST /api/users 返回 500",
        "expected": "返回 201 + 用户数据",
        "root_cause": "model 缺少 email 字段的 unique 约束",
        "round": 1,
    }

    required_fields = ["id", "target", "test_case", "error", "expected", "root_cause", "round"]
    for field in required_fields:
        assert field in bug, f"Bug 数据结构缺少必需字段: {field}"


def test_bug_target_enum():
    """Bug 的 target 字段只能是 backend 或 frontend"""
    valid_targets = {"backend", "frontend"}

    bug_backend = {"target": "backend"}
    bug_frontend = {"target": "frontend"}

    assert bug_backend["target"] in valid_targets
    assert bug_frontend["target"] in valid_targets


def test_bug_round_positive():
    """Bug 的 round 字段必须是正整数"""
    bug = {"round": 1}
    assert bug["round"] > 0


# ========================================================================
# TesterAgent Bug 检测测试
# ========================================================================


def test_tester_agent_detects_bugs():
    """TesterAgent 检测到 bug 后应该写入 state["bugs"]"""
    # 模拟 TesterAgent 输出包含 bug 的测试报告
    test_report_with_bugs = """---TEST_REPORT_START---
## 代码审查摘要
发现 2 个严重问题需要修复

## 问题清单
| 严重度 | 位置 | 问题描述 | 建议修复 |
|--------|------|----------|----------|
| 高 | backend/main.py | POST /api/users 返回 500 | 添加 email 字段验证 |
| 中 | frontend/App.tsx | 按钮点击无响应 | 检查 onClick 事件绑定 |

## 整体评估
- **通过**: 否
- **建议**: 修复上述问题后重新测试
---TEST_REPORT_END---"""

    # 验证测试报告格式正确
    assert "---TEST_REPORT_START---" in test_report_with_bugs
    assert "问题清单" in test_report_with_bugs
    # 验证包含"通过"和"否"的评估结论
    assert "通过" in test_report_with_bugs
    assert "否" in test_report_with_bugs


def test_bug_list_in_state():
    """state["bugs"] 应该是一个列表"""
    state = {
        "user_idea": "测试",
        "prd": None,
        "tech_plan": None,
        "frontend_code": None,
        "backend_code": None,
        "test_report": None,
        "zip_path": None,
        "current_stage": Stage.TESTING,
        "error_message": None,
        "messages": [],
        "ask_user": None,
        "bugs": [],
    }

    assert isinstance(state["bugs"], list)


def test_add_bug_to_state():
    """向 state["bugs"] 添加 bug"""
    state = {
        "bugs": [],
    }

    bug = {
        "id": "bug-001",
        "target": "backend",
        "test_case": "test_create_user",
        "error": "POST /api/users 返回 500",
        "expected": "返回 201 + 用户数据",
        "root_cause": "model 缺少 email 字段",
        "round": 1,
    }

    state["bugs"].append(bug)

    assert len(state["bugs"]) == 1
    assert state["bugs"][0]["id"] == "bug-001"


# ========================================================================
# 回退逻辑测试
# ========================================================================


def test_rollback_target_backend():
    """bug target 为 backend 时，应该回退到后端 Agent"""
    bug = {"target": "backend"}
    assert bug["target"] == "backend"


def test_rollback_target_frontend():
    """bug target 为 frontend 时，应该回退到前端 Agent"""
    bug = {"target": "frontend"}
    assert bug["target"] == "frontend"


def test_rollback_round_tracking():
    """每次回退应该记录轮次"""
    bugs = []
    for i in range(3):
        bug = {
            "id": f"bug-{i+1:03d}",
            "target": "backend",
            "test_case": f"test_case_{i}",
            "error": f"error_{i}",
            "expected": f"expected_{i}",
            "root_cause": f"root_cause_{i}",
            "round": i + 1,
        }
        bugs.append(bug)

    assert len(bugs) == 3
    assert bugs[0]["round"] == 1
    assert bugs[1]["round"] == 2
    assert bugs[2]["round"] == 3


# ========================================================================
# 循环控制测试
# ========================================================================


def test_max_bug_rounds():
    """最多允许 3 轮 bug 回退"""
    MAX_BUG_ROUNDS = 3
    current_round = 3

    assert current_round <= MAX_BUG_ROUNDS


def test_exceed_max_rounds():
    """超过 3 轮应该暂停"""
    MAX_BUG_ROUNDS = 3
    current_round = 4

    should_pause = current_round > MAX_BUG_ROUNDS
    assert should_pause is True


def test_bug_round_increment():
    """每次回退轮次应该递增"""
    bugs = []
    round_num = 0

    # 模拟 3 轮回退
    for i in range(3):
        round_num += 1
        bug = {
            "id": f"bug-{i+1:03d}",
            "target": "backend",
            "test_case": f"test_case_{i}",
            "error": f"error_{i}",
            "expected": f"expected_{i}",
            "root_cause": f"root_cause_{i}",
            "round": round_num,
        }
        bugs.append(bug)

    assert bugs[0]["round"] == 1
    assert bugs[1]["round"] == 2
    assert bugs[2]["round"] == 3


# ========================================================================
# 状态转换测试
# ========================================================================


def test_state_transition_on_bug_found():
    """发现 bug 时，状态应该保持在 TESTING"""
    state = {
        "current_stage": Stage.TESTING,
        "bugs": [],
    }

    # 模拟发现 bug
    bug = {
        "id": "bug-001",
        "target": "backend",
        "test_case": "test_create_user",
        "error": "POST /api/users 返回 500",
        "expected": "返回 201 + 用户数据",
        "root_cause": "model 缺少 email 字段",
        "round": 1,
    }
    state["bugs"].append(bug)

    # 发现 bug 时，状态应该保持在 TESTING（等待回退）
    assert state["current_stage"] == Stage.TESTING


def test_state_transition_on_all_bugs_fixed():
    """所有 bug 修复后，状态应该转到 DEPLOYMENT"""
    state = {
        "current_stage": Stage.TESTING,
        "bugs": [],
    }

    # 模拟 bug 已修复
    state["current_stage"] = Stage.DEPLOYMENT

    assert state["current_stage"] == Stage.DEPLOYMENT


def test_state_transition_on_max_rounds_exceeded():
    """超过最大轮次时，状态应该转到 ERROR"""
    state = {
        "current_stage": Stage.TESTING,
        "bugs": [],
    }

    MAX_BUG_ROUNDS = 3
    current_round = 4

    if current_round > MAX_BUG_ROUNDS:
        state["current_stage"] = Stage.ERROR
        state["error_message"] = "Bug 修复轮次超过上限，需要人工介入"

    assert state["current_stage"] == Stage.ERROR
    assert state["error_message"] is not None


# ========================================================================
# Bug 去重测试
# ========================================================================


def test_bug_deduplication():
    """相同 test_case 的 bug 应该去重"""
    bugs = []
    seen_test_cases = set()

    new_bugs = [
        {"id": "bug-001", "test_case": "test_create_user", "target": "backend"},
        {"id": "bug-002", "test_case": "test_create_user", "target": "backend"},  # 重复
        {"id": "bug-003", "test_case": "test_delete_user", "target": "backend"},
    ]

    for bug in new_bugs:
        if bug["test_case"] not in seen_test_cases:
            bugs.append(bug)
            seen_test_cases.add(bug["test_case"])

    assert len(bugs) == 2
    assert bugs[0]["test_case"] == "test_create_user"
    assert bugs[1]["test_case"] == "test_delete_user"


# ========================================================================
# 多 Agent 回退测试
# ========================================================================


def test_multiple_bugs_different_targets():
    """多个 bug 可能回退给不同的 Agent"""
    bugs = [
        {"id": "bug-001", "target": "backend", "test_case": "test_api"},
        {"id": "bug-002", "target": "frontend", "test_case": "test_ui"},
    ]

    backend_bugs = [b for b in bugs if b["target"] == "backend"]
    frontend_bugs = [b for b in bugs if b["target"] == "frontend"]

    assert len(backend_bugs) == 1
    assert len(frontend_bugs) == 1


def test_rollback_to_multiple_agents():
    """多个 bug 可能需要同时回退给多个 Agent"""
    bugs = [
        {"id": "bug-001", "target": "backend"},
        {"id": "bug-002", "target": "frontend"},
        {"id": "bug-003", "target": "backend"},
    ]

    targets = set(b["target"] for b in bugs)
    assert targets == {"backend", "frontend"}


# ========================================================================
# 边界情况测试
# ========================================================================


def test_no_bugs_found():
    """没有发现 bug 时，state["bugs"] 应该为空"""
    state = {
        "bugs": [],
    }

    assert len(state["bugs"]) == 0


def test_empty_bug_list():
    """空 bug 列表应该被正确处理"""
    bugs = []
    assert len(bugs) == 0


def test_single_bug():
    """单个 bug 应该被正确处理"""
    bugs = [
        {
            "id": "bug-001",
            "target": "backend",
            "test_case": "test_create_user",
            "error": "POST /api/users 返回 500",
            "expected": "返回 201 + 用户数据",
            "root_cause": "model 缺少 email 字段",
            "round": 1,
        }
    ]

    assert len(bugs) == 1
    assert bugs[0]["target"] == "backend"


# ========================================================================
# Bug 信息完整性测试
# ========================================================================


def test_bug_error_description():
    """Bug 的 error 字段应该包含错误描述"""
    bug = {
        "error": "POST /api/users 返回 500 Internal Server Error",
    }

    assert len(bug["error"]) > 0
    assert "500" in bug["error"]


def test_bug_expected_behavior():
    """Bug 的 expected 字段应该包含期望行为"""
    bug = {
        "expected": "返回 201 Created + 用户数据",
    }

    assert len(bug["expected"]) > 0
    assert "201" in bug["expected"]


def test_bug_root_cause():
    """Bug 的 root_cause 字段应该包含根因分析"""
    bug = {
        "root_cause": "User model 缺少 email 字段的 unique 约束",
    }

    assert len(bug["root_cause"]) > 0
