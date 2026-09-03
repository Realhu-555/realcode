"""C4/C5 集成测试：Loop 内压缩（tail-keep + 恢复块）与压缩摘要同步长期记忆"""

import json

import pytest
from src.gis_toolkit import context as ctx
from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.engine import GisEngine
from src.gis_toolkit.session import GisSession


@pytest.fixture(autouse=True)
def _session_engine_local(monkeypatch):
    """与 test_gis_tool_agent 一致：会话引擎替换为本地 geopandas 引擎，不依赖 QGIS"""

    def _fake_engine(**kwargs):
        kwargs.pop("engine", None)
        return GisEngine(**kwargs)

    monkeypatch.setattr("src.gis_toolkit.session.create_gis_engine", _fake_engine)


class FakeLLM:
    """tool_responses 供 chat_with_tools；summary_responses 供 chat（压缩摘要独立于主循环）"""

    def __init__(self, tool_responses=None, summary_responses=None):
        self.tool_responses = list(tool_responses or [])
        self.summary_responses = list(summary_responses or [])
        self.calls: list[list[dict]] = []

    def chat_with_tools(self, messages, tools, agent_type=None, model_id=None):
        self.calls.append(list(messages))
        return self._next_tool()

    def chat_with_tools_stream(
        self, messages, tools, agent_type=None, model_id=None, on_text_delta=None
    ):
        self.calls.append(list(messages))
        resp = self._next_tool()
        content = resp.get("content") or ""
        if on_text_delta and content:
            for ch in content:
                on_text_delta(ch)
        return resp

    def chat(self, messages, agent_type=None, model_id=None):
        self.calls.append(list(messages))
        if self.summary_responses:
            return self.summary_responses.pop(0)
        return {"content": "会话摘要：已完成前置处理，产物 map.png", "tool_calls": None}

    def _next_tool(self):
        if not self.tool_responses:
            return {"content": "完成", "tool_calls": None}
        return self.tool_responses.pop(0)


def _tc(tool_id, name, args):
    return {
        "id": tool_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)},
    }


GOOD_SUMMARY = (
    "已完成 GDP 数据分析，产出 gdp_map.png 与 summary.csv，"
    "结论广东省受灾最重约 120 亿，继续审批方案 A。"
)


def _long_tool_result(chars: int = 1200) -> dict:
    return {"status": "ok", "message": "数据加载完成，" + "分析值" * (chars // 3)}


def _loop_agent(tmp_path):
    engine = GisEngine(out_dir=str(tmp_path / "data"), allowed_roots=[str(tmp_path)])
    agent = GisToolAgent(engine=engine)
    return agent


def _loop_messages(rounds: int = 6) -> list[dict]:
    """system + user + rounds×(assistant tc + 大 tool 结果)"""
    msgs = [{"role": "system", "content": "你是 GIS 助手。"},
            {"role": "user", "content": "加载并分析 GDP 数据"}]
    for i in range(rounds):
        msgs.append({"role": "assistant", "content": "", "tool_calls": [_tc(f"c{i}", "load_data", {"file": f"a{i}.csv"})]})
        msgs.append({"role": "tool", "tool_call_id": f"c{i}", "content": json.dumps(_long_tool_result(), ensure_ascii=False)})
    return msgs


def _assert_no_orphan_tool(messages: list[dict]) -> None:
    """校验消息结构：tool 前一条必须是对应 assistant（含 tool_calls），无悬挂"""
    for i, m in enumerate(messages):
        if m.get("role") == "tool":
            assert i > 0 and messages[i - 1].get("role") == "assistant"
            assert messages[i - 1].get("tool_calls")
            ids = {tc.get("id") for tc in messages[i - 1].get("tool_calls") or []}
            assert m.get("tool_call_id") in ids


# ── C4：Loop 内压缩（直接调用 _maybe_compact_loop）────────────────


def test_loop_compact_triggers_and_injects_recovery(monkeypatch, tmp_path):
    agent = _loop_agent(tmp_path)
    monkeypatch.setattr(agent, "_effective_context_window", lambda: 2000)  # trigger=1700
    agent.engine._layer_name = "gdp_points"
    agent.engine._layer = object()
    llm = FakeLLM(summary_responses=[{"content": GOOD_SUMMARY, "tool_calls": None}])
    agent.llm = llm
    msgs = _loop_messages(rounds=6)  # 14 条，估算 > 1700
    assert ctx.estimate_tokens(msgs) >= 1700

    ret = agent._maybe_compact_loop(msgs, "对GDP做分级统计", steps_done=6, compacts_used=0)
    assert ret is not None
    new_msgs, used = ret
    assert used == 1
    sys_text = new_msgs[0]["content"]
    assert "前期执行摘要" in sys_text and GOOD_SUMMARY in sys_text
    assert "恢复状态" in sys_text
    assert "当前图层：gdp_points" in sys_text
    assert "进行中任务：对GDP做分级统计" in sys_text
    assert len(new_msgs) < len(msgs)
    # tail 保留原文完整、结构合法
    _assert_no_orphan_tool(new_msgs)
    assert new_msgs[1:] == msgs[-(len(new_msgs) - 1):]


def test_loop_compact_respects_max_and_min(monkeypatch, tmp_path):
    agent = _loop_agent(tmp_path)
    monkeypatch.setattr(agent, "_effective_context_window", lambda: 2000)
    llm = FakeLLM(summary_responses=[{"content": GOOD_SUMMARY, "tool_calls": None}] * 5)
    agent.llm = llm
    msgs = _loop_messages(rounds=6)

    # 已达上限：不压缩
    assert agent._maybe_compact_loop(msgs, "t", steps_done=1, compacts_used=3) is None
    # 消息不足最小条数：不压缩
    short = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
    assert agent._maybe_compact_loop(short, "t", steps_done=1, compacts_used=0) is None


def test_loop_compact_guardrail_rejects_bad_summary(monkeypatch, tmp_path):
    agent = _loop_agent(tmp_path)
    monkeypatch.setattr(agent, "_effective_context_window", lambda: 2000)
    # 两次都退化 → 放弃本次（护栏不通过，不阻断）
    llm = FakeLLM(summary_responses=[{"content": "嗯", "tool_calls": None},
                                     {"content": "好", "tool_calls": None}])
    agent.llm = llm
    msgs = _loop_messages(rounds=6)
    assert agent._maybe_compact_loop(msgs, "t", steps_done=1, compacts_used=0) is None


# ── C4：run 主循环真实触发（长任务不靠放大 max_steps）────────────


def test_run_performs_loop_compact_and_finishes(monkeypatch, tmp_path):
    engine = GisEngine(out_dir=str(tmp_path / "data"), allowed_roots=[str(tmp_path)])
    n_loads = 16
    tool_responses = [
        {"content": None, "tool_calls": [_tc(f"r{i}", "load_data", {"file": f"f{i}.csv"})]}
        for i in range(n_loads)
    ]
    tool_responses.append(
        {
            "content": None,
            "tool_calls": [
                _tc("fin", "finish", {"explanation": "任务完成", "outputs": ["out.png"]})
            ],
        }
    )
    llm = FakeLLM(
        tool_responses=tool_responses,
        summary_responses=[{"content": GOOD_SUMMARY, "tool_calls": None}] * 3,
    )
    agent = GisToolAgent(engine=engine, max_steps=n_loads + 1)
    agent.llm = llm
    monkeypatch.setattr(agent, "_effective_context_window", lambda: 2000)
    monkeypatch.setattr(agent, "_audit_correction",
                        lambda user_request, final, outputs, trajectory, messages: (final, outputs, None))
    monkeypatch.setattr(agent, "_save_trace", lambda *a, **k: None)

    def _long_tool(name, args):
        if name == "finish":
            return {"status": "finished", "explanation": "任务完成", "outputs": ["out.png"], "summary": "完成"}
        return {"status": "ok", "message": "执行结果，" + "分" * 400}

    monkeypatch.setattr(agent, "_execute_with_check", _long_tool)

    result = agent.run("对 GDP 数据做多步分析直至产出专题图", session=None)
    assert result.get("final") == "任务完成"
    # 至少一次主循环发送时 system 已注入压缩摘要（Loop 压缩真实发生）
    sys_contents = [c[0]["content"] for c in llm.calls if c and c[0].get("role") == "system"]
    assert any("前期执行摘要" in s for s in sys_contents)
    # 每次发送的消息结构合法
    for c in llm.calls:
        _assert_no_orphan_tool(c)


# ── C5：压缩摘要同步长期记忆（on_compact_summary）────────────────


def _compactable_session(tmp_path):
    sess = GisSession("c5", tmp_path / "sessions")
    sess.history = [{"user_request": f"历史请求{i}", "final": f"结论{i}"} for i in range(3)]
    sess.messages = []
    for i in range(12):
        sess.messages.append({"role": "user", "content": f"第{i}步数据 " + "分析" * 340})
    return sess


def test_full_replace_pushes_summary_to_memory_sink(monkeypatch, tmp_path):
    agent = _loop_agent(tmp_path)
    monkeypatch.setattr(agent, "_effective_context_window", lambda: 2000)
    sink: list[str] = []
    agent.on_compact_summary = sink.append
    llm = FakeLLM(summary_responses=[{"content": GOOD_SUMMARY, "tool_calls": None}])
    agent.llm = llm
    sess = _compactable_session(tmp_path)

    assert agent._maybe_compact(sess) is True
    assert sess.compacted is True
    assert sess.summary == GOOD_SUMMARY
    assert sink == [GOOD_SUMMARY]


def test_full_replace_guardrail_skips_sink(monkeypatch, tmp_path):
    agent = _loop_agent(tmp_path)
    monkeypatch.setattr(agent, "_effective_context_window", lambda: 2000)
    sink: list[str] = []
    agent.on_compact_summary = sink.append
    llm = FakeLLM(summary_responses=[{"content": "行", "tool_calls": None},
                                     {"content": "嗯", "tool_calls": None}])
    agent.llm = llm
    sess = _compactable_session(tmp_path)

    assert agent._maybe_compact(sess) is False
    assert sess.compacted is False
    assert sess.summary == ""
    assert sink == []


def test_full_replace_sink_exception_does_not_block(monkeypatch, tmp_path):
    agent = _loop_agent(tmp_path)
    monkeypatch.setattr(agent, "_effective_context_window", lambda: 2000)
    agent.on_compact_summary = lambda s: (_ for _ in ()).throw(RuntimeError("boom"))
    llm = FakeLLM(summary_responses=[{"content": GOOD_SUMMARY, "tool_calls": None}])
    agent.llm = llm
    sess = _compactable_session(tmp_path)

    assert agent._maybe_compact(sess) is True
    assert sess.compacted is True
    assert sess.summary == GOOD_SUMMARY
