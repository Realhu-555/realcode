"""GIS 助手会话（多轮连续对话）测试 — 引擎状态复用 + 对话历史保留"""

import json

from src.gis_toolkit.agent import GisToolAgent
from src.gis_toolkit.engine import GisEngine
from src.gis_toolkit.session import GisSession, GisSessionStore


class FakeLLM:
    """按预设响应序列返回的假 LLM，记录每次收到的消息"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[list[dict]] = []

    def chat_with_tools(self, messages, tools, agent_type=None, model_id=None):
        self.calls.append(list(messages))
        if not self.responses:
            return {"content": "完成", "tool_calls": None}
        return self.responses.pop(0)


def _tc(tool_id, name, args):
    return {
        "id": tool_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)},
    }


def _point_csv(tmp_path):
    p = tmp_path / "points.csv"
    p.write_text(
        "province,gdp,lon,lat\n北京,100,116.4,39.9\n上海,200,121.5,31.2\n",
        encoding="utf-8",
    )
    return str(p)


def test_store_reuses_session():
    """同一 session_id 复用同一会话；不同 id 各自独立"""
    store = GisSessionStore(ttl=3600)
    sid1, sess1 = store.get_or_create()
    sid2, sess2 = store.get_or_create(sid1)
    assert sid1 == sid2
    assert sess1 is sess2
    _, sess3 = store.get_or_create()
    assert sess3 is not sess1
    store.clear()


def test_session_engine_keeps_layer_between_rounds(tmp_path):
    """第一轮 load_data 后，第二轮直接 inspect 即可（引擎状态复用）"""
    csv = _point_csv(tmp_path)
    out = tmp_path / "out"
    engine = GisEngine(out_dir=str(out), allowed_roots=[str(tmp_path)])
    sess = GisSession("s-test-1", out)
    sess.engine = engine

    agent = GisToolAgent(engine=engine, max_steps=12)
    agent.llm = FakeLLM(
        [
            {"content": None, "tool_calls": [_tc("c1", "load_data", {"path": csv})]},
            {
                "content": None,
                "tool_calls": [_tc("c2", "finish", {"outputs": [], "summary": "ok"})],
            },
            # 第二轮：不再 load，直接 inspect
            {"content": None, "tool_calls": [_tc("c3", "inspect_data", {})]},
            {
                "content": None,
                "tool_calls": [_tc("c4", "finish", {"outputs": [], "summary": "ok"})],
            },
        ]
    )

    r1 = agent.run("加载数据", session=sess)
    assert r1["steps"] == 2
    assert len(sess.history) == 1

    r2 = agent.run("当前图层有多少行", session=sess)
    assert r2["trajectory"][0]["tool"] == "inspect_data"
    assert r2["trajectory"][0]["result"]["rows"] == 2
    assert len(sess.history) == 2
    # 第二轮 user 消息即用户请求（无 data_file 提示）
    second_user = [m for m in agent.llm.calls[2] if m["role"] == "user"][-1]
    assert second_user["content"] == "当前图层有多少行"
    # 历史被保存到会话
    assert len(sess.messages) > 0
    assert sess.messages[0]["role"] == "user"


def test_new_session_starts_fresh(tmp_path):
    """不带 session 的新一轮 = 全新引擎（没有上一轮图层）"""
    csv = _point_csv(tmp_path)
    out = tmp_path / "out"
    engine = GisEngine(out_dir=str(out), allowed_roots=[str(tmp_path)])
    sess = GisSession("s-test-2", out)
    sess.engine = engine

    agent = GisToolAgent(engine=engine, max_steps=12)
    agent.llm = FakeLLM(
        [
            {"content": None, "tool_calls": [_tc("c1", "load_data", {"path": csv})]},
            {
                "content": None,
                "tool_calls": [_tc("c2", "finish", {"outputs": [], "summary": "ok"})],
            },
        ]
    )
    agent.run("加载数据", session=sess)

    # 新会话（无 session）→ 直接 inspect 应报"没有图层"
    fresh = GisToolAgent(
        engine=GisEngine(out_dir=str(out), allowed_roots=[str(tmp_path)]), max_steps=12
    )
    fresh.llm = FakeLLM(
        [
            {"content": None, "tool_calls": [_tc("c3", "inspect_data", {})]},
            {"content": None, "tool_calls": [_tc("c4", "finish", {"outputs": [], "summary": "x"})]},
        ]
    )
    r = fresh.run("看看")
    assert r["trajectory"][0]["result"]["status"] == "error"
    assert "没有图层" in r["trajectory"][0]["result"]["error"]


def test_store_persist_list_and_detail(tmp_path):
    """save 后 list 返回摘要、get_detail 返回轮次数据"""
    store = GisSessionStore(db_path=str(tmp_path / "sessions.json"), ttl=3600)
    sid, sess = store.get_or_create(user_id="u1")
    sess.append_round(
        [],
        "把 gdp_demo.csv 做分级设色图",
        "已完成",
        {
            "steps": 2,
            "outputs": ["map.png"],
            "trajectory": [
                {"step": 1, "tool": "load_data", "args": {}, "result": {"status": "ok"}}
            ],
            "timed_out": False,
        },
    )
    store.save("u1", sess)

    items = store.list_sessions("u1")
    assert len(items) == 1
    assert items[0]["session_id"] == sid
    assert items[0]["title"] == "把 gdp_demo.csv 做分级设色图"
    assert items[0]["rounds"] == 1

    detail = store.get_detail("u1", sid)
    assert detail is not None
    assert detail["rounds"][0]["user"] == "把 gdp_demo.csv 做分级设色图"
    assert detail["rounds"][0]["outputs"] == ["map.png"]

    # 其它用户隔离
    assert store.list_sessions("u2") == []


def test_store_delete(tmp_path):
    store = GisSessionStore(db_path=str(tmp_path / "sessions.json"), ttl=3600)
    sid, sess = store.get_or_create(user_id="u1")
    store.save("u1", sess)
    assert store.delete("u1", sid) is True
    assert store.get_detail("u1", sid) is None
    assert store.list_sessions("u1") == []
    assert store.delete("u1", sid) is False


def test_store_restore_from_persistence(tmp_path):
    """新 store 实例能通过持久化 JSON 恢复会话详情"""
    db = str(tmp_path / "sessions.json")
    store1 = GisSessionStore(db_path=db, ttl=3600)
    sid, sess = store1.get_or_create(user_id="u1")
    sess.append_round(
        [], "分析数据", "完成", {"steps": 1, "outputs": [], "trajectory": [], "timed_out": False}
    )
    store1.save("u1", sess)

    store2 = GisSessionStore(db_path=db, ttl=3600)
    sid2, sess2 = store2.get_or_create(sid, user_id="u1")
    assert sid2 == sid
    assert sess2.title == "分析数据"
    assert len(sess2.rounds) == 1
    assert sess2.messages == []
