"""GisToolAgent 工具调用循环测试 — fake LLM 驱动各场景"""

import json
from pathlib import Path

from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.engine import GisEngine
from src.gis_toolkit.session import GisSession


class FakeLLM:
    """按预设响应序列返回的假 LLM"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[list[dict]] = []

    def chat_with_tools(self, messages, tools, agent_type=None, model_id=None):
        self.calls.append(list(messages))
        return self._next()

    def chat_with_tools_stream(
        self, messages, tools, agent_type=None, model_id=None, on_text_delta=None
    ):
        """流式版：把 content 逐字符作为文本增量回调，返回与 chat_with_tools 相同结构"""
        self.calls.append(list(messages))
        resp = self._next()
        content = resp.get("content") or ""
        if on_text_delta and content:
            for ch in content:
                on_text_delta(ch)
        return resp

    def chat(self, messages, agent_type=None, model_id=None):
        """纯对话调用（滚动摘要等场景）"""
        self.calls.append(list(messages))
        if self.responses:
            return self.responses.pop(0)
        return {"content": "会话摘要", "tool_calls": None}

    def _next(self):
        if not self.responses:
            return {"content": "完成", "tool_calls": None}
        return self.responses.pop(0)


def _tc(tool_id, name, args):
    return {
        "id": tool_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)},
    }


def _agent(tmp_path, responses, max_steps=12):
    engine = GisEngine(out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)])
    agent = GisToolAgent(engine=engine, max_steps=max_steps)
    agent.llm = FakeLLM(responses)
    return agent


def _point_csv(tmp_path):
    p = tmp_path / "points.csv"
    p.write_text("province,gdp,lon,lat\n北京,100,116.4,39.9\n上海,200,121.5,31.2\n", encoding="utf-8")
    return str(p)


# ── T6 checker 校验回环 ──────────────────────────────

def _empty_png(tmp_path):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    p = out / "map.png"
    p.write_bytes(b"")  # 空 PNG，校验必失败
    return p


def test_check_failure_returns_error_and_escalates(tmp_path):
    """产物校验失败 → error 回给 LLM；连续失败超限 → 强制提示停止"""
    agent = _agent(tmp_path, [])
    bad = _empty_png(tmp_path)
    agent.engine.render_map = lambda output="map.png": {
        "status": "ok",
        "message": "ok",
        "outputs": ["map.png"],
        "output_paths": [str(bad)],
    }
    r1 = agent._execute_with_check("render_map", {"output": "map.png"})
    assert r1["status"] == "error"
    assert "请修正参数后重试" in r1["error"]
    assert r1["check_failed"]

    agent._execute_with_check("render_map", {"output": "map.png"})
    r3 = agent._execute_with_check("render_map", {"output": "map.png"})
    assert "连续失败" in r3["error"]

    # 产物恢复正常后，校验通过并重置计数
    good = tmp_path / "out" / "map.png"
    good.write_bytes(b"\x89PNG" + b"\x00" * 100)
    agent.engine.render_map = lambda output="map.png": {
        "status": "ok",
        "message": "ok",
        "outputs": ["map.png"],
        "output_paths": [str(good)],
    }
    assert agent._execute_with_check("render_map", {"output": "map.png"})["status"] == "ok"
    assert agent._check_failures == {}


def test_run_recover_after_check_failure(tmp_path):
    """完整流：LLM 第一次出图失败（空文件），看到 error 后第二次成功"""
    csv = _point_csv(tmp_path)
    bad = _empty_png(tmp_path)

    def fake_render(output="map.png"):
        if fake_render.n == 0:
            fake_render.n += 1
            return {
                "status": "ok",
                "message": "ok",
                "outputs": ["map.png"],
                "output_paths": [str(bad)],
            }
        good = tmp_path / "out" / "map.png"
        good.write_bytes(b"\x89PNG" + b"\x00" * 200)
        return {
            "status": "ok",
            "message": "ok",
            "outputs": ["map.png"],
            "output_paths": [str(good)],
        }

    fake_render.n = 0
    agent = _agent(
        tmp_path,
        [
            {"content": None, "tool_calls": [_tc("c1", "load_data", {"path": csv})]},
            {"content": None, "tool_calls": [_tc("c2", "render_map", {"output": "map.png"})]},
            {"content": None, "tool_calls": [_tc("c3", "render_map", {"output": "map.png"})]},
            {"content": None, "tool_calls": [_tc("c4", "finish", {"outputs": ["map.png"], "summary": "完成"})]},
        ],
    )
    agent.engine.render_map = fake_render
    res = agent.run(csv)
    assert res["status"] if isinstance(res, dict) and "status" in res else True
    # 第二次 render_map 成功，finish 正常
    tools_called = [t["tool"] for t in res["trajectory"]]
    assert tools_called.count("render_map") == 2
    assert tools_called[-1] == "finish"


# ── T7 滚动摘要（短期记忆压缩）────────────────────────

def _session_with_history(tmp_path, n_messages: int):
    out_dir = tmp_path / "sess_out"
    out_dir.mkdir(exist_ok=True)
    sess = GisSession("test-sess", out_dir)
    sess.messages = [
        {"role": "user", "content": f"第 {i} 轮问题：加载数据并做分析" + "长文本" * 500}
        for i in range(n_messages)
    ]
    return sess


def test_roll_summary_when_over_threshold(tmp_path):
    """历史超阈值时生成滚动摘要并裁剪到窗口"""
    sess = _session_with_history(tmp_path, 60)
    agent = _agent(tmp_path, [])
    agent._maybe_roll_summary(sess)
    assert sess.summary  # 摘要已生成
    assert len(sess.messages) <= 40  # 已裁剪


def test_roll_summary_skips_below_threshold(tmp_path):
    """历史未超阈值时不触发压缩"""
    sess = _session_with_history(tmp_path, 3)
    agent = _agent(tmp_path, [])
    agent._maybe_roll_summary(sess)
    assert sess.summary == ""
    assert len(sess.messages) == 3


def test_prepare_messages_injects_summary_and_window(tmp_path):
    """构造消息：system 注入摘要，历史只取最近窗口"""
    sess = _session_with_history(tmp_path, 60)
    sess.summary = "已完成 gdp_demo 分级设色，产物 choropleth.png"
    agent = _agent(tmp_path, [])
    msgs = agent._prepare_messages("继续分析", None, sess, "")
    assert "历史会话摘要" in msgs[0]["content"]
    assert "choropleth.png" in msgs[0]["content"]
    # system + 窗口历史 + user
    assert len(msgs) == 1 + 40 + 1
    assert msgs[-1]["role"] == "user"


# ── T8 思考展示 / T9 subagent 预留 ────────────────────

def test_run_stream_emits_tool_reason(tmp_path):
    """工具调用前输出理由（tool_reason 事件）"""
    csv = _point_csv(tmp_path)
    agent = _agent(
        tmp_path,
        [
            {
                "content": "我需要先加载数据文件。",
                "tool_calls": [_tc("c1", "load_data", {"path": csv})],
            },
            {"content": "完成", "tool_calls": None},
        ],
    )
    events: list[dict] = []
    agent.run_stream(csv, on_event=lambda e: events.append(e))
    reasons = [e for e in events if e["type"] == "tool_reason"]
    assert reasons, "应发出 tool_reason 事件"
    assert "加载数据" in reasons[0]["reason"]
    assert reasons[0]["step"] == 1


def test_execute_subtask_default_unsupported(tmp_path):
    """subagent 未配置时返回 unsupported，不影响主流程"""
    agent = _agent(tmp_path, [])
    res = agent.execute_subtask("做复杂分析")
    assert res["status"] == "unsupported"


def test_execute_subtask_with_injected_impl(tmp_path):
    """注入 sub_agent 实现后生效"""
    agent = _agent(tmp_path, [])
    agent.sub_agent = lambda task, context: {
        "status": "ok",
        "result": f"子任务完成: {task}",
    }
    res = agent.execute_subtask("统计各省 GDP")
    assert res["status"] == "ok"
    assert "统计各省 GDP" in res["result"]


# ── T11 轨迹落盘 ─────────────────────────────────────

def test_save_trace_writes_json(tmp_path):
    """轨迹落盘：_save_trace 写入可解析的 JSON 到 data/gis_traces/"""
    import json as _json

    trace_dir = Path("data/gis_traces")
    before = set(trace_dir.glob("*.json")) if trace_dir.is_dir() else set()
    agent = _agent(tmp_path, [])
    agent._save_trace(
        "用户请求",
        "最终回答",
        ["choropleth.png"],
        [{"step": 1, "tool": "load_data", "args": {}, "result": {"status": "ok"}}],
    )
    after = set(trace_dir.glob("*.json"))
    new_files = after - before
    assert new_files, "应生成新的轨迹文件"
    trace = _json.loads(next(iter(new_files)).read_text(encoding="utf-8"))
    assert trace["user_request"] == "用户请求"
    assert "choropleth.png" in trace["outputs"]
    assert trace["trajectory"][0]["tool"] == "load_data"
    # 清理测试生成的轨迹
    for f in new_files:
        f.unlink()


def test_full_flow(tmp_path):
    """load → inspect → choropleth → finish 完整链路"""
    csv = _point_csv(tmp_path)
    agent = _agent(
        tmp_path,
        [
            {"content": None, "tool_calls": [_tc("c1", "load_data", {"path": csv})]},
            {"content": None, "tool_calls": [_tc("c2", "inspect_data", {})]},
            {"content": None, "tool_calls": [_tc("c3", "choropleth", {"column": "gdp", "output": "map.png"})]},
            {"content": None, "tool_calls": [_tc("c4", "finish", {"outputs": ["map.png"], "summary": "完成"})]},
        ],
    )
    result = agent.run("画分级设色图")
    assert not result["timed_out"]
    assert result["steps"] == 4
    assert result["outputs"] == ["map.png"]
    assert [t["tool"] for t in result["trajectory"]] == [
        "load_data", "inspect_data", "choropleth", "finish",
    ]
    # 每个工具结果都是 ok / finished
    assert all(t["result"]["status"] in {"ok", "finished"} for t in result["trajectory"])
    # 消息序列：assistant(tool_calls) 后紧跟 tool 结果
    assert agent.llm.calls[1][-1]["role"] == "tool"
    assert agent.llm.calls[1][-1]["tool_call_id"] == "c1"
    # tool 消息内容可 JSON 解析
    tool_content = json.loads(agent.llm.calls[1][-1]["content"])
    assert tool_content["status"] == "ok"


def test_error_then_recover(tmp_path):
    """先失败（列不存在）→ 依据 error 修正后成功"""
    csv = _point_csv(tmp_path)
    agent = _agent(
        tmp_path,
        [
            {"content": None, "tool_calls": [_tc("c1", "load_data", {"path": csv})]},
            {"content": None, "tool_calls": [_tc("c2", "choropleth", {"column": "nope", "output": "m.png"})]},
            {"content": None, "tool_calls": [_tc("c3", "choropleth", {"column": "gdp", "output": "m.png"})]},
            {"content": None, "tool_calls": [_tc("c4", "finish", {"outputs": ["m.png"], "summary": "修正完成"})]},
        ],
    )
    result = agent.run("画图")
    assert result["outputs"] == ["m.png"]
    assert result["trajectory"][1]["result"]["status"] == "error"
    assert "列不存在" in result["trajectory"][1]["result"]["error"]
    assert result["trajectory"][2]["result"]["status"] == "ok"


def test_unknown_tool_becomes_error(tmp_path):
    """未知工具名 → status=error（不中断会话）"""
    csv = _point_csv(tmp_path)
    agent = _agent(
        tmp_path,
        [
            {"content": None, "tool_calls": [_tc("c1", "no_such_tool", {})]},
            {"content": None, "tool_calls": [_tc("c2", "load_data", {"path": csv})]},
            {"content": None, "tool_calls": [_tc("c3", "finish", {"outputs": [], "summary": "x"})]},
        ],
    )
    result = agent.run("测试")
    assert result["trajectory"][0]["result"]["status"] == "error"
    assert "未知工具" in result["trajectory"][0]["result"]["error"]


def test_no_tool_call_ends_with_final(tmp_path):
    """LLM 直接给文字答复 → 立即结束"""
    agent = _agent(tmp_path, [{"content": "没有图层，无法操作", "tool_calls": None}])
    result = agent.run("你好")
    assert result["steps"] == 1
    assert result["final"] == "没有图层，无法操作"
    assert result["trajectory"] == []
    assert not result["timed_out"]


def test_max_steps_timeout(tmp_path):
    """LLM 无限调工具 → 步数上限触发 timed_out"""
    agent = _agent(
        tmp_path,
        [
            {"content": None, "tool_calls": [_tc(f"c{i}", "inspect_data", {})]}
            for i in range(20)
        ],
        max_steps=3,
    )
    result = agent.run("无限循环")
    assert result["steps"] == 3
    assert result["timed_out"] is True


def test_engine_error_does_not_crash(tmp_path):
    """未加载图层时 buffer → error 且不抛异常"""
    agent = _agent(
        tmp_path,
        [
            {"content": None, "tool_calls": [_tc("c1", "buffer", {"distance": 1.0})]},
            {"content": None, "tool_calls": [_tc("c2", "finish", {"outputs": [], "summary": "x"})]},
        ],
    )
    result = agent.run("buffer")
    assert result["trajectory"][0]["result"]["status"] == "error"
    assert "没有图层" in result["trajectory"][0]["result"]["error"]


def test_preloaded_data_skips_load(tmp_path):
    """run(data_file=...) 预加载后，LLM 直接 inspect"""
    csv = _point_csv(tmp_path)
    engine = GisEngine(data_file=csv, out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)])
    agent = GisToolAgent(engine=engine, max_steps=12)
    agent.llm = FakeLLM(
        [
            {"content": None, "tool_calls": [_tc("c1", "inspect_data", {})]},
            {"content": None, "tool_calls": [_tc("c2", "finish", {"outputs": [], "summary": "x"})]},
        ]
    )
    result = agent.run("看看数据", data_file=csv)
    assert result["trajectory"][0]["tool"] == "inspect_data"
    assert result["trajectory"][0]["result"]["rows"] == 2


def test_demo_file_hint_lists_demo_files(tmp_path, monkeypatch):
    """无显式数据文件时，system prompt 注入可用演示文件清单（忽略非数据文件）"""
    monkeypatch.chdir(tmp_path)
    demo = tmp_path / "data" / "gis_demo"
    demo.mkdir(parents=True)
    (demo / "gdp_demo.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (demo / "readme.txt").write_text("ignore", encoding="utf-8")

    hint = GisToolAgent._demo_file_hint()
    assert "data/gis_demo/gdp_demo.csv" in hint
    assert "readme.txt" not in hint


def test_system_prompt_contains_demo_hint_when_no_file(tmp_path, monkeypatch):
    """未传 data_file 时：user 消息为原始请求，system 消息含演示文件路径"""
    monkeypatch.chdir(tmp_path)
    demo = tmp_path / "data" / "gis_demo"
    demo.mkdir(parents=True)
    (demo / "gdp_demo.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    agent = _agent(tmp_path, [{"content": "完成", "tool_calls": None}])
    agent.run("把 gdp_demo.csv 画成分级设色图")

    system_msg = agent.llm.calls[0][0]["content"]
    user_msg = agent.llm.calls[0][1]["content"]
    assert "data/gis_demo/gdp_demo.csv" in system_msg
    assert user_msg == "把 gdp_demo.csv 画成分级设色图"


def test_data_file_prompt_has_no_garbled_text(tmp_path):
    """传入 data_file 时 user 提示为正常中文，无乱码占位符"""
    csv = _point_csv(tmp_path)
    engine = GisEngine(out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)])
    agent = GisToolAgent(engine=engine, max_steps=12)
    agent.llm = FakeLLM([{"content": "完成", "tool_calls": None}])
    agent.run("分析", data_file=csv)

    user_msg = agent.llm.calls[0][1]["content"]
    assert "数据文件已就绪" in user_msg
    assert "?" not in user_msg


def test_run_stream_emits_events_in_order(tmp_path):
    """流式事件按输出顺序：文本增量穿插在工具调用之间，tool_call 先于 tool_result，最终 done"""
    csv = _point_csv(tmp_path)
    agent = _agent(
        tmp_path,
        [
            {"content": "开始处理", "tool_calls": [_tc("c1", "load_data", {"path": csv})]},
            {"content": "正在绘图", "tool_calls": [_tc("c2", "choropleth", {"column": "gdp", "output": "map.png"})]},
            {"content": "完成，这是结果", "tool_calls": [_tc("c3", "finish", {"outputs": ["map.png"], "summary": "完成"})]},
        ],
    )
    events: list[dict] = []
    result = agent.run_stream("画分级设色图", on_event=events.append)
    assert result["outputs"] == ["map.png"]
    assert not result["timed_out"]
    types = [e["type"] for e in events]
    assert types[0] == "text_delta"
    assert types[-1] == "done"
    assert "tool_call" in types and "tool_result" in types
    # 每个 tool_call 都在其 tool_result 之前
    calls = [i for i, e in enumerate(events) if e["type"] == "tool_call"]
    results = [i for i, e in enumerate(events) if e["type"] == "tool_result"]
    assert len(calls) == len(results) == 3
    assert all(calls[i] < results[i] for i in range(3))
    # 文本增量累积后与各轮 content 一致
    text = "".join(e["delta"] for e in events if e["type"] == "text_delta")
    assert text == "开始处理正在绘图完成，这是结果"
    # done 事件携带最终产物
    done = next(e for e in events if e["type"] == "done")
    assert done["outputs"] == ["map.png"]
    assert done["steps"] == 3


def test_run_stream_sends_done_without_session(tmp_path):
    """未传 session 时也发送 done 事件（end-to-end 事件自洽）"""
    agent = _agent(
        tmp_path,
        [{"content": "没有图层，无法操作", "tool_calls": None}],
    )
    events: list[dict] = []
    result = agent.run_stream("你好", on_event=events.append)
    assert result["final"] == "没有图层，无法操作"
    assert events[-1]["type"] == "done"
    assert events[-1]["final"] == "没有图层，无法操作"
