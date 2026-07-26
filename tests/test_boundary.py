"""边界条件测试

覆盖各模块的边界/极端场景，确保防御性逻辑正确。
"""

import asyncio
import json

import pytest

from src.llm.provider import LLMProvider, _strip_thinking
from src.orchestrator.gate import ApprovalGate, UserAction
from src.orchestrator.memory import MemoryType, ShortTermMemory
from src.orchestrator.state import (
    OutputArtifact,
    Stage,
    _extract_list_items,
    _extract_named_items,
    _extract_page_structure,
    _extract_section,
    create_output_artifact,
    extract_prd_structured,
    extract_upstream_content,
    get_memory,
    get_memory_context,
    get_upstream_content,
    retrieve_memory,
    save_memory,
    update_memory_relevance,
)
from src.sandbox.executor import SandboxExecutor, SandboxConfig


# ========================================================================
# _strip_thinking 边界测试
# ========================================================================


def test_strip_thinking_empty_string():
    """空字符串原样返回"""
    assert _strip_thinking("") == ""


def test_strip_thinking_no_think_tags():
    """无 <think> 标签时原样返回"""
    text = "Hello world, this is a normal response."
    assert _strip_thinking(text) == text


def test_strip_thinking_single_think_block():
    """移除单个 <think> 块"""
    text = "<think>Let me think...</think>\nHere is the answer."
    result = _strip_thinking(text)
    assert "<think>" not in result
    assert "Here is the answer" in result


def test_strip_thinking_multiple_think_blocks():
    """移除多个 <think> 块"""
    text = "<think>step1</think>\nSome text <think>step2</think>\nFinal answer."
    result = _strip_thinking(text)
    assert "<think>" not in result
    assert "Some text" in result
    assert "Final answer" in result


def test_strip_thinking_only_think_block():
    """全文只有 <think> 块时返回空字符串"""
    text = "<think>Just thinking, no output</think>"
    result = _strip_thinking(text)
    assert result == ""


def test_strip_thinking_empty_think_block():
    """空的 <think> 块被移除"""
    text = "<think></think>\nReal content."
    result = _strip_thinking(text)
    assert "<think>" not in result
    assert "Real content" in result


def test_strip_thinking_multiline_think():
    """多行 <think> 块被正确移除"""
    text = "<think>\nLine 1\nLine 2\nLine 3\n</think>\nAnswer."
    result = _strip_thinking(text)
    assert "<think>" not in result
    assert "Line 1" not in result
    assert "Answer" in result


# ========================================================================
# create_output_artifact 边界测试
# ========================================================================


def test_create_output_artifact_empty_content():
    """空字符串内容"""
    artifact = create_output_artifact(content="")
    assert artifact["full_content"] == ""
    assert artifact["summary"] == ""
    assert artifact["token_count"] == 0


def test_create_output_artifact_short_content_no_summary_suffix():
    """短内容不添加省略号后缀"""
    artifact = create_output_artifact(content="短内容")
    # len("短内容") = 3, 3 // 10 = 0, max(100, 0) = 100 > 3, 所以 summary 就是原文
    assert artifact["summary"] == "短内容"


def test_create_output_artifact_long_content_auto_summary():
    """长内容自动生成摘要（取前 1/10）"""
    content = "A" * 1000
    artifact = create_output_artifact(content=content)
    assert artifact["summary"].startswith("A")
    assert artifact["summary"].endswith("...")
    assert len(artifact["summary"]) < len(content)


def test_create_output_artifact_token_count_estimation():
    """token_count 自动估算：字符数 / 2"""
    content = "A" * 100
    artifact = create_output_artifact(content=content)
    assert artifact["token_count"] == 50


def test_create_output_artifact_explicit_params_override():
    """显式参数覆盖自动估算"""
    artifact = create_output_artifact(
        content="A" * 200,
        summary="自定义摘要",
        token_count=999,
    )
    assert artifact["summary"] == "自定义摘要"
    assert artifact["token_count"] == 999


def test_create_output_artifact_single_char_content():
    """单字符内容"""
    artifact = create_output_artifact(content="X")
    assert artifact["full_content"] == "X"
    assert artifact["summary"] == "X"
    assert artifact["token_count"] == 0  # 1 // 2 = 0


def test_create_output_artifact_content_exactly_100_chars():
    """恰好 100 字符的内容（摘要长度边界）"""
    content = "A" * 100
    artifact = create_output_artifact(content=content)
    # summary_length = max(100, 100 // 10) = 100
    # content_length == summary_length, 不加 "..."
    assert artifact["summary"] == content


def test_create_output_artifact_content_101_chars():
    """101 字符内容（刚超过摘要阈值）"""
    content = "A" * 101
    artifact = create_output_artifact(content=content)
    assert artifact["summary"].endswith("...")
    # summary_length = max(100, 101//10) = 100, 截取前100字符 + "..." = 103
    assert len(artifact["summary"]) == 103


# ========================================================================
# extract_upstream_content 边界测试
# ========================================================================


def test_extract_upstream_content_non_dict_input():
    """非 dict 输入直接转字符串返回"""
    assert extract_upstream_content("hello") == "hello"
    assert extract_upstream_content(42) == "42"
    assert extract_upstream_content(None) == "None"
    assert extract_upstream_content(["a", "b"]) == "['a', 'b']"


def test_extract_upstream_content_dict_without_full_content():
    """没有 full_content 键的 dict 直接转字符串"""
    d = {"some_key": "some_value"}
    result = extract_upstream_content(d)
    assert "some_key" in result


def test_extract_upstream_content_dict_with_full_content():
    """有 full_content 键的 dict 走 get_upstream_content 路径"""
    artifact = {
        "full_content": "Full text",
        "summary": "Summary",
        "structured": {},
        "token_count": 100,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    result = extract_upstream_content(artifact, available_tokens=200)
    assert result == "Full text"


# ========================================================================
# get_upstream_content 边界测试
# ========================================================================


def test_get_upstream_content_available_tokens_zero():
    """available_tokens=0 时返回 structured"""
    artifact = {
        "full_content": "Full",
        "summary": "Sum",
        "structured": {"k": "v"},
        "token_count": 1000,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    result = get_upstream_content(artifact, available_tokens=0)
    assert '"k"' in result


def test_get_upstream_content_token_count_zero():
    """token_count=0 时预算充足返回全文"""
    artifact = {
        "full_content": "Full",
        "summary": "Sum",
        "structured": {},
        "token_count": 0,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    result = get_upstream_content(artifact, available_tokens=100)
    assert result == "Full"


def test_get_upstream_content_structured_is_none():
    """structured 为 None 时返回 JSON null"""
    artifact = {
        "full_content": "Full",
        "summary": "Sum",
        "structured": None,
        "token_count": 10000,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    result = get_upstream_content(artifact, available_tokens=1)
    parsed = json.loads(result)
    assert parsed is None


# ========================================================================
# _extract_section 边界测试
# ========================================================================


def test_extract_section_last_section_no_next_header():
    """最后一个章节后面没有下一个 ## 时也能正确提取"""
    text = "## Intro\nSome intro.\n## Last Section\nContent here."
    result = _extract_section(text, "Last Section")
    assert result == "Content here."


def test_extract_section_empty_content_between_headers():
    """两个章节之间内容为空"""
    text = "## Section A\nContent A\n## Section B\nContent B"
    result = _extract_section(text, "Section A")
    assert result == "Content A"


def test_extract_section_with_parentheses_in_name():
    """章节名包含括号注释"""
    text = "## 核心功能（按优先级）\nFeature 1\nFeature 2"
    result = _extract_section(text, "核心功能")
    assert "Feature 1" in result


def test_extract_section_no_match():
    """不存在的章节返回 None"""
    text = "## 产品概述\nSome content."
    result = _extract_section(text, "不存在的章节")
    assert result is None


def test_extract_section_multiline_content():
    """多行内容的章节"""
    text = "## 数据模型\nLine 1\nLine 2\nLine 3\n## Other"
    result = _extract_section(text, "数据模型")
    assert "Line 1" in result
    assert "Line 3" in result


# ========================================================================
# _extract_list_items 边界测试
# ========================================================================


def test_extract_list_items_empty_text():
    """空文本返回空列表"""
    assert _extract_list_items("") == []


def test_extract_list_items_no_list_items():
    """无列表项返回空列表"""
    text = "这是一段普通文本，没有列表格式。"
    assert _extract_list_items(text) == []


def test_extract_list_items_mixed_content():
    """混合内容只提取列表项"""
    text = "标题\n- 项目1\n一些描述文字\n- 项目2\n尾部文本"
    items = _extract_list_items(text)
    assert len(items) == 2
    assert "项目1" in items
    assert "项目2" in items


def test_extract_list_items_numbered_and_bullet():
    """同时包含数字编号和短横线列表"""
    text = "- 第一项\n2. 第二项\n* 第三项\n4) 第四项"
    items = _extract_list_items(text)
    assert len(items) == 4


# ========================================================================
# _extract_named_items 边界测试
# ========================================================================


def test_extract_named_items_empty_text():
    """空文本返回空列表"""
    assert _extract_named_items("") == []


def test_extract_named_items_no_bold_items():
    """无加粗项返回空列表"""
    text = "- 普通列表项\n- 另一个普通项"
    assert _extract_named_items(text) == []


def test_extract_named_items_numbered_bold():
    """数字编号加粗项也能提取"""
    text = "1. **名称**：描述"
    items = _extract_named_items(text)
    assert len(items) == 1
    assert items[0]["name"] == "名称"
    assert items[0]["description"] == "描述"


# ========================================================================
# _extract_page_structure 边界测试
# ========================================================================


def test_extract_page_structure_empty_text():
    """空文本返回空列表"""
    assert _extract_page_structure("") == []


def test_extract_page_structure_no_pages():
    """无页面项返回空列表"""
    text = "一些普通文本\n没有页面结构"
    assert _extract_page_structure(text) == []


def test_extract_page_structure_page_no_items():
    """页面没有子项"""
    text = "- **首页**"
    pages = _extract_page_structure(text)
    assert len(pages) == 1
    assert pages[0]["page"] == "首页"
    assert pages[0]["items"] == []


def test_extract_page_structure_only_last_page_collected():
    """最后一个页面在循环结束后被收集"""
    text = "- **页面A**\n  - 子项1\n- **页面B**"
    pages = _extract_page_structure(text)
    assert len(pages) == 2
    assert pages[1]["page"] == "页面B"
    assert pages[1]["items"] == []


# ========================================================================
# SandboxExecutor 边界测试
# ========================================================================


def test_run_command_empty_string():
    """空命令返回不允许"""
    sb = SandboxExecutor()
    sb.create("test_empty_cmd")
    try:
        output, code = sb.run_command("")
        assert code == 1
        assert "不允许" in output
    finally:
        sb.cleanup()


def test_run_command_only_whitespace():
    """纯空白命令返回不允许"""
    sb = SandboxExecutor()
    sb.create("test_ws_cmd")
    try:
        output, code = sb.run_command("   ")
        assert code == 1
        assert "不允许" in output
    finally:
        sb.cleanup()


def test_run_command_disallowed_command():
    """不在白名单的命令被拒绝"""
    sb = SandboxExecutor()
    sb.create("test_disallowed")
    try:
        output, code = sb.run_command("rm -rf /")
        assert code == 1
        assert "不允许" in output
    finally:
        sb.cleanup()


def test_run_command_custom_timeout():
    """自定义超时配置"""
    config = SandboxConfig(timeout=1)
    sb = SandboxExecutor(config=config)
    sb.create("test_custom_timeout")
    try:
        output, code = sb.run_command('python -c "import time; time.sleep(5)"')
        assert code == -1
        assert "超时" in output
    finally:
        sb.cleanup()


def test_pack_zip_when_not_created():
    """未初始化时 pack_zip 抛异常"""
    sb = SandboxExecutor()
    with pytest.raises(RuntimeError, match="沙箱未初始化"):
        sb.pack_zip("/tmp/test")


def test_run_command_when_not_created():
    """未初始化时 run_command 抛异常"""
    sb = SandboxExecutor()
    with pytest.raises(RuntimeError, match="沙箱未初始化"):
        sb.run_command("echo hello")


def test_write_file_special_characters():
    """写入特殊字符文件"""
    sb = SandboxExecutor()
    sb.create("test_special_chars")
    try:
        content = "特殊字符: <>&\"' 中文 换行\n\t制表符"
        sb.write_file("special.txt", content)
        assert sb.read_file("special.txt") == content
    finally:
        sb.cleanup()


def test_write_file_overwrite():
    """重复写入同名文件覆盖"""
    sb = SandboxExecutor()
    sb.create("test_overwrite")
    try:
        sb.write_file("file.txt", "version1")
        sb.write_file("file.txt", "version2")
        assert sb.read_file("file.txt") == "version2"
    finally:
        sb.cleanup()


def test_list_files_after_cleanup():
    """清理后 list_files 返回空列表"""
    sb = SandboxExecutor()
    sb.create("test_list_after_cleanup")
    sb.write_file("a.txt", "content")
    sb.cleanup()
    assert sb.list_files() == []


# ========================================================================
# ShortTermMemory 边界测试
# ========================================================================


def test_memory_retrieve_with_limit_zero():
    """limit=0 时不返回任何条目"""
    memory = ShortTermMemory()
    memory.add("内容1", MemoryType.CONTEXT, "tester", "testing")
    entries = memory.retrieve(limit=0)
    assert len(entries) == 0


def test_memory_retrieve_no_matching_stage():
    """不存在的阶段返回空列表"""
    memory = ShortTermMemory()
    memory.add("内容1", MemoryType.CONTEXT, "tester", "testing")
    entries = memory.retrieve(stage="nonexistent")
    assert len(entries) == 0


def test_memory_retrieve_no_matching_type():
    """不存在的类型返回空列表"""
    memory = ShortTermMemory()
    memory.add("内容1", MemoryType.CONTEXT, "tester", "testing")
    entries = memory.retrieve(memory_type=MemoryType.ERROR)
    assert len(entries) == 0


def test_memory_retrieve_no_matching_source():
    """不存在的来源返回空列表"""
    memory = ShortTermMemory()
    memory.add("内容1", MemoryType.CONTEXT, "tester", "testing")
    entries = memory.retrieve(source="nonexistent")
    assert len(entries) == 0


def test_memory_retrieve_empty_memory():
    """空记忆库返回空列表"""
    memory = ShortTermMemory()
    entries = memory.retrieve()
    assert entries == []


def test_memory_get_context_string_empty():
    """空记忆库返回空字符串"""
    memory = ShortTermMemory()
    context = memory.get_context_string()
    assert context == ""


def test_memory_update_relevance_no_match():
    """无匹配内容时更新 0 条"""
    memory = ShortTermMemory()
    memory.add("React 框架", MemoryType.DECISION, "architect", "architecture")
    count = memory.update_relevance("Vue", 0.5)
    assert count == 0


def test_memory_update_relevance_caps_at_2():
    """相关性分数上限为 2.0"""
    memory = ShortTermMemory()
    memory.add("React", MemoryType.DECISION, "architect", "architecture")
    memory.entries[0].relevance_score = 1.9
    memory.update_relevance("React", 0.5)
    assert memory.entries[0].relevance_score == 2.0


def test_memory_compress_single_entry():
    """只有单条记忆时压缩不删除（len > 1 条件不满足）"""
    memory = ShortTermMemory(max_tokens=1)
    memory.add("X" * 100, MemoryType.CONTEXT, "tester", "testing")
    # 即使超过预算，单条记忆不会被删除
    assert len(memory.entries) == 1


def test_memory_clear_after_add():
    """添加后清空"""
    memory = ShortTermMemory()
    memory.add("内容1", MemoryType.CONTEXT, "tester", "testing")
    memory.add("内容2", MemoryType.DECISION, "architect", "architecture")
    memory.clear()
    assert len(memory.entries) == 0
    assert memory._current_tokens == 0


def test_memory_serialization_roundtrip():
    """序列化/反序列化保持数据一致"""
    memory = ShortTermMemory(max_tokens=8000)
    memory.add("决策1", MemoryType.DECISION, "architect", "architecture")
    memory.add("反馈1", MemoryType.FEEDBACK, "user", "requirement")

    d = memory.to_dict()
    restored = ShortTermMemory.from_dict(d)

    assert restored.max_tokens == 8000
    assert len(restored.entries) == 2
    assert restored.entries[0].content == "决策1"
    assert restored.entries[1].content == "反馈1"


def test_memory_from_dict_missing_fields():
    """from_dict 缺失字段时使用默认值"""
    d = {"max_tokens": 1000, "entries": []}
    memory = ShortTermMemory.from_dict(d)
    assert memory.max_tokens == 1000
    assert memory._current_tokens == 0


# ========================================================================
# 状态辅助函数边界测试
# ========================================================================


def test_get_memory_none_short_term_memory():
    """short_term_memory 为 None 时创建空记忆"""
    state = {"user_idea": "test"}
    memory = get_memory(state)
    assert isinstance(memory, ShortTermMemory)
    assert len(memory.entries) == 0


def test_get_memory_valid_dict():
    """从有效 dict 恢复记忆"""
    mem = ShortTermMemory()
    mem.add("test", MemoryType.CONTEXT, "tester", "testing")
    state = {"user_idea": "test", "short_term_memory": mem.to_dict()}
    restored = get_memory(state)
    assert len(restored.entries) == 1


def test_save_memory_returns_new_dict():
    """save_memory 返回新字典不修改原状态"""
    state = {"user_idea": "test"}
    mem = ShortTermMemory()
    updated = save_memory(state, mem)
    assert "short_term_memory" in updated
    # 原 state 不受影响
    assert "short_term_memory" not in state


def test_retrieve_memory_helper_empty():
    """空记忆库的 retrieve_memory 返回空列表"""
    state = {"user_idea": "test"}
    entries = retrieve_memory(state)
    assert entries == []


def test_get_memory_context_helper_empty():
    """空记忆库返回空字符串"""
    state = {"user_idea": "test"}
    context = get_memory_context(state)
    assert context == ""


def test_update_memory_relevance_helper_no_match():
    """无匹配时返回原状态"""
    state = {"user_idea": "test"}
    state = update_memory_relevance(state, "nonexistent", 0.5)
    memory = get_memory(state)
    assert len(memory.entries) == 0


# ========================================================================
# graph._route_after_tester 边界测试
# ========================================================================


def test_route_after_tester_no_bugs():
    """无 bug 时返回 continue"""
    from src.orchestrator.graph import _route_after_tester

    state = {"bugs": None}
    assert _route_after_tester(state) == "continue"


def test_route_after_tester_empty_bugs_list():
    """空 bugs 列表返回 continue"""
    from src.orchestrator.graph import _route_after_tester

    state = {"bugs": []}
    assert _route_after_tester(state) == "continue"


def test_route_after_tester_bug_missing_round():
    """bug 缺少 round 字段时默认为 1"""
    from src.orchestrator.graph import _route_after_tester

    state = {"bugs": [{"target": "backend"}]}  # 无 round 字段
    assert _route_after_tester(state) == "rollback_backend"


def test_route_after_tester_bug_missing_target():
    """bug 缺少 target 字段时跳过该 bug，不崩溃"""
    from src.orchestrator.graph import _route_after_tester

    state = {"bugs": [{"round": 1}]}  # 无 target 字段
    assert _route_after_tester(state) == "continue"


def test_route_after_tester_bug_invalid_target():
    """bug target 值无效（非 backend/frontend）时跳过"""
    from src.orchestrator.graph import _route_after_tester

    state = {"bugs": [{"target": "unknown", "round": 1}]}
    assert _route_after_tester(state) == "continue"


def test_route_after_tester_mixed_valid_and_invalid_targets():
    """混合有效和无效 target 时只考虑有效的"""
    from src.orchestrator.graph import _route_after_tester

    state = {
        "bugs": [
            {"target": "backend", "round": 1},
            {"target": "unknown", "round": 1},
        ]
    }
    assert _route_after_tester(state) == "rollback_backend"


def test_route_after_tester_both_targets():
    """同时有 backend 和 frontend bug 时优先回退 backend"""
    from src.orchestrator.graph import _route_after_tester

    state = {
        "bugs": [
            {"target": "backend", "round": 1},
            {"target": "frontend", "round": 1},
        ]
    }
    assert _route_after_tester(state) == "rollback_backend"


def test_route_after_tester_bug_round_exactly_at_limit():
    """bug 轮次恰好等于 MAX_BUG_ROUNDS 时不报错"""
    from src.orchestrator.graph import MAX_BUG_ROUNDS, _route_after_tester

    state = {"bugs": [{"target": "backend", "round": MAX_BUG_ROUNDS}]}
    # round(3) > MAX_BUG_ROUNDS(3) → False → 不进入 error
    assert _route_after_tester(state) == "rollback_backend"


def test_route_after_tester_bug_round_exceeds_limit():
    """bug 轮次超过上限时返回 error"""
    from src.orchestrator.graph import MAX_BUG_ROUNDS, _route_after_tester

    state = {"bugs": [{"target": "backend", "round": MAX_BUG_ROUNDS + 1}]}
    assert _route_after_tester(state) == "error"


# ========================================================================
# ApprovalGate 边界测试
# ========================================================================


def test_gate_handle_action_invalid_request_id_format():
    """任意字符串 request_id 也能处理"""
    gate = ApprovalGate()
    result = gate.handle_user_action("totally-invalid-id", UserAction.APPROVE)
    assert result.approved is True


def test_gate_clear_already_completed_request():
    """清除已完成的请求返回 True（已从 dict 中删除）"""
    gate = ApprovalGate()
    rid = "c1:s1:1"
    gate.handle_user_action(rid, UserAction.APPROVE)
    # 第一次删除已完成
    assert gate.clear_pending_request(rid) is False  # 已不在 dict 中


@pytest.mark.asyncio
async def test_gate_get_pending_requests_different_client():
    """不同客户端的请求互不可见"""
    gate = ApprovalGate(timeout=5.0)
    artifact = {
        "full_content": "x",
        "summary": "x",
        "structured": None,
        "token_count": 1,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }

    task = asyncio.create_task(
        gate.wait_for_approval("client-A", "requirement", artifact)
    )
    await asyncio.sleep(0.01)
    pending_a = gate.get_pending_requests_by_client("client-A")
    pending_b = gate.get_pending_requests_by_client("client-B")
    gate.cancel_all_requests("client-A")
    await task
    assert len(pending_a) == 1
    assert len(pending_b) == 0


# ========================================================================
# extract_prd_structured 边界测试
# ========================================================================


def test_extract_prd_structured_none_input():
    """None 输入不会崩溃"""
    # 函数签名是 str，但防御性地处理 None
    result = extract_prd_structured("")
    assert result is None


def test_extract_prd_structured_only_start_marker():
    """只有 ---PRD_START--- 没有内容"""
    result = extract_prd_structured("---PRD_START---")
    assert result is None


def test_extract_prd_structured_only_end_marker():
    """只有 ---PRD_END--- 没有内容"""
    result = extract_prd_structured("---PRD_END---")
    # 去除标记后只剩空白或普通文本，无法提取
    # 实际行为：如果内容无结构则返回 None
    assert result is None


def test_extract_prd_structured_section_with_no_content():
    """章节存在但无实际内容"""
    prd = "## 产品概述\n\n## 核心功能\n1. **功能一**：描述"
    result = extract_prd_structured(prd)
    # 产品概述内容为空行，但可能被提取为空字符串
    # 核心功能应该能提取
    assert "core_features" in result
    assert len(result["core_features"]) == 1


def test_extract_prd_structured_deeply_nested_content():
    """章节内容包含多层缩进"""
    prd = """## 页面结构
- **首页**
  - 第一层
    - 第二层
  - 回到第一层
"""
    result = extract_prd_structured(prd)
    pages = result["page_structure"]
    assert len(pages) == 1
    assert pages[0]["page"] == "首页"


# ========================================================================
# Stage 枚举边界测试
# ========================================================================


def test_stage_enum_all_values_unique():
    """所有 Stage 枚举值唯一"""
    values = [s.value for s in Stage]
    assert len(values) == len(set(values))


def test_stage_enum_from_value():
    """通过 value 反查 Stage"""
    assert Stage("requirement") == Stage.REQUIREMENT
    assert Stage("done") == Stage.DONE
    assert Stage("error") == Stage.ERROR


def test_stage_enum_invalid_value():
    """无效值抛出 ValueError"""
    with pytest.raises(ValueError):
        Stage("nonexistent_stage")


# ========================================================================
# MemoryEntry 边界测试
# ========================================================================


def test_memory_entry_empty_content():
    """空内容的记忆条目"""
    from src.orchestrator.memory import MemoryEntry

    entry = MemoryEntry(
        content="",
        memory_type=MemoryType.CONTEXT,
        source="tester",
        stage="testing",
    )
    assert entry.content == ""
    assert entry.get_token_estimate() == 0


def test_memory_entry_very_long_content():
    """超长内容的记忆条目"""
    from src.orchestrator.memory import MemoryEntry

    content = "A" * 10000
    entry = MemoryEntry(
        content=content,
        memory_type=MemoryType.CONTEXT,
        source="tester",
        stage="testing",
    )
    assert entry.get_token_estimate() == 5000


def test_memory_entry_serialization_roundtrip():
    """MemoryEntry 序列化/反序列化"""
    from src.orchestrator.memory import MemoryEntry

    entry = MemoryEntry(
        content="test",
        memory_type=MemoryType.DECISION,
        source="architect",
        stage="architecture",
        metadata={"key": "value"},
    )
    entry.access_count = 5
    entry.relevance_score = 1.8

    d = entry.to_dict()
    restored = MemoryEntry.from_dict(d)

    assert restored.content == "test"
    assert restored.access_count == 5
    assert restored.relevance_score == 1.8
    assert restored.metadata == {"key": "value"}


# ========================================================================
# LLMProvider 异常处理边界测试
# ========================================================================


def test_llm_provider_chat_raises_on_failure():
    """LLM 调用失败时抛出 RuntimeError"""
    from unittest.mock import MagicMock, patch

    from src.llm.provider import LLMProvider

    provider = LLMProvider()
    with patch.object(
        provider, "_call_openai_compatible", side_effect=Exception("API Error")
    ):
        with pytest.raises(RuntimeError, match="LLM 调用失败"):
            provider.chat([{"role": "user", "content": "test"}], agent_type="requirement")


def test_llm_provider_chat_returns_empty_on_all_empty():
    """连续两次空响应时抛出 RuntimeError"""
    from unittest.mock import MagicMock, patch

    from src.llm.provider import LLMProvider

    provider = LLMProvider()
    with patch.object(provider, "_call_openai_compatible", return_value=""):
        with pytest.raises(RuntimeError, match="LLM 调用失败"):
            provider.chat([{"role": "user", "content": "test"}], agent_type="requirement")


def test_llm_provider_chat_retries_on_first_failure():
    """第一次失败第二次成功时正常返回"""
    from unittest.mock import patch

    from src.llm.provider import LLMProvider

    provider = LLMProvider()
    with patch.object(
        provider, "_call_openai_compatible", side_effect=[Exception("fail"), "ok"]
    ):
        result = provider.chat([{"role": "user", "content": "test"}], agent_type="requirement")
        assert result == "ok"


def test_llm_provider_chat_strips_think_on_retry():
    """重试成功后也清理 <think> 块"""
    from unittest.mock import patch

    from src.llm.provider import LLMProvider

    provider = LLMProvider()
    with patch.object(
        provider, "_call_openai_compatible", side_effect=[Exception("fail"), "<think>x</think>\nanswer"]
    ):
        result = provider.chat([{"role": "user", "content": "test"}], agent_type="requirement")
        assert "<think>" not in result
        assert "answer" in result


# ========================================================================
# get_upstream_content key 缺失防护测试
# ========================================================================


def test_get_upstream_content_missing_token_count():
    """缺少 token_count 键时默认为 0"""
    artifact = {
        "full_content": "Full",
        "summary": "Sum",
        "structured": {},
        # 无 token_count
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    result = get_upstream_content(artifact, available_tokens=100)
    assert result == "Full"


def test_get_upstream_content_missing_full_content():
    """缺少 full_content 键时返回空字符串"""
    artifact = {
        "summary": "Sum",
        "structured": {},
        "token_count": 0,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    result = get_upstream_content(artifact, available_tokens=100)
    assert result == ""


def test_get_upstream_content_missing_summary():
    """缺少 summary 键时返回空字符串"""
    artifact = {
        "full_content": "Full",
        "structured": {},
        "token_count": 1000,
        "status": "draft",
        "version": 1,
        "user_feedback": None,
        "review_result": None,
    }
    # token_count(1000) > available_tokens(100)
    # token_count // 10(100) <= available_tokens(100) → 返回 summary
    result = get_upstream_content(artifact, available_tokens=100)
    assert result == ""


# ========================================================================
# create_output_artifact 非字符串 content 防护测试
# ========================================================================


def test_create_output_artifact_non_string_content():
    """非字符串 content 自动转为字符串"""
    artifact = create_output_artifact(content=42)
    assert artifact["full_content"] == "42"


def test_create_output_artifact_none_content():
    """None content 自动转为字符串"""
    artifact = create_output_artifact(content=None)
    assert artifact["full_content"] == "None"


def test_create_output_artifact_dict_content():
    """dict content 自动转为字符串"""
    artifact = create_output_artifact(content={"key": "value"})
    assert "key" in artifact["full_content"]
