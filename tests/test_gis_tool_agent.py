"""GisToolAgent 工具调用循环测试 — fake LLM 驱动各场景"""

import json

from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.engine import GisEngine


class FakeLLM:
    """按预设响应序列返回的假 LLM"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[list[dict]] = []

    def chat_with_tools(self, messages, tools, agent_type=None, model_id=None):
        self.calls.append(list(messages))  # ????????? list
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
