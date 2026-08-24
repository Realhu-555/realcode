"""Gate 4 — 记忆系统收尾：向量化语义检索 + 主动压缩阈值 + 跨会话召回

覆盖 P1 记忆系统待办：
1. 经验教训写入时同步生成向量（lesson_embeddings）
2. 语义检索：按相关性召回，而非仅字面子串匹配
3. get_relevant_lessons 升级为向量检索（兼容回退）
4. 主动压缩：接近阈值（80%）即提前滚动摘要，避免"爆了才压"
5. 10+ 轮长对话上下文有界
6. 跨会话召回历史结论与产物引用（_build_ltm_hint）
"""

import json

from src.gis_toolkit.agent import (
    COMPACT_THRESHOLD_TOKENS,
    HISTORY_WINDOW_MESSAGES,
    GisToolAgent,
)
from src.gis_toolkit.engine import GisEngine
from src.orchestrator.long_term_memory import Lesson, LongTermMemory

# ── Fake LLM（复用 test_gis_tool_agent 模式） ──────────────────────


class FakeLLM:
    """按预设响应序列返回的假 LLM"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[list[dict]] = []

    def chat_with_tools(self, messages, tools, agent_type=None, model_id=None):
        self.calls.append(list(messages))
        return self._next()

    def chat(self, messages, agent_type=None, model_id=None):
        """纯对话调用（滚动摘要等场景）"""
        self.calls.append(list(messages))
        if self.responses:
            return self.responses.pop(0)
        return {
            "content": "会话摘要：已完成台风经济损失分析，产物 damage_map.png",
            "tool_calls": None,
        }

    def _next(self):
        if not self.responses:
            return {"content": "完成", "tool_calls": None}
        return self.responses.pop(0)


def _agent(tmp_path):
    engine = GisEngine(out_dir=str(tmp_path / "out"), allowed_roots=[str(tmp_path)])
    agent = GisToolAgent(engine=engine, max_steps=12)
    agent.llm = FakeLLM([])
    return agent


def _lesson(id_: str, text: str, agent_name: str = "gis_assistant:u") -> Lesson:
    return Lesson(
        id=id_,
        project_id="p1",
        agent_name=agent_name,
        category="success",
        lesson=text,
    )


# ── 1. 写入向量 ────────────────────────────────────────────────────


def test_save_lesson_writes_embedding(tmp_path):
    """save_lesson 后 lesson_embeddings 表应存在该 lesson 的向量记录"""
    ltm = LongTermMemory(str(tmp_path / "m.db"))
    ltm.save_lesson(
        _lesson("t1", "台风灾情分析完成：广东省受灾最重，经济损失约 120 亿，产物 damage_map.png")
    )
    rows = ltm._get_lesson_embeddings("t1")
    assert rows is not None, "lesson_embeddings 应写入向量"
    emb = json.loads(rows)
    assert isinstance(emb, list) and len(emb) > 0
    # 向量应为归一化（L2 ≈ 1），且非全零
    norm = sum(x * x for x in emb) ** 0.5
    assert abs(norm - 1.0) < 1e-3
    assert any(x != 0 for x in emb)


def test_embed_deterministic(tmp_path):
    """同一文本两次 embedding 应完全一致（可复现检索）"""
    ltm = LongTermMemory(str(tmp_path / "m.db"))
    a = ltm._embed_text("分析广东台风经济损失")
    b = ltm._embed_text("分析广东台风经济损失")
    assert a == b


# ── 2. 语义检索（红：旧实现按子串匹配无法命中） ─────────────────────


def test_semantic_search_hits_related_lesson(tmp_path):
    """查询无字面重合词的语义相关文本，应召回对应 lesson"""
    ltm = LongTermMemory(str(tmp_path / "m.db"))
    ltm.save_lesson(
        _lesson(
            "typhoon", "台风灾情分析完成：广东省受灾最重，经济损失约 120 亿，产物 damage_map.png"
        )
    )
    ltm.save_lesson(_lesson("gdp", "北京各区 GDP 分级设色图已生成，产物 gdp_choropleth.png"))
    hits = ltm.semantic_search_lessons("帮我分析广东台风造成的经济损失", limit=3)
    ids = [h.id for h in hits]
    assert "typhoon" in ids, f"语义检索应命中台风 lesson，实际: {ids}"
    # 相关性最高者应排在首位；GDP lesson 与查询语义无关，可不被召回
    assert ids[0] == "typhoon"


def test_get_relevant_lessons_semantic_hit(tmp_path):
    """get_relevant_lessons 升级后按语义召回（保持原签名）"""
    ltm = LongTermMemory(str(tmp_path / "m.db"))
    ltm.save_lesson(
        _lesson(
            "typhoon", "台风灾情分析完成：广东省受灾最重，经济损失约 120 亿，产物 damage_map.png"
        )
    )
    ltm.save_lesson(_lesson("gdp", "北京各区 GDP 分级设色图已生成，产物 gdp_choropleth.png"))
    hits = ltm.get_relevant_lessons("帮我分析广东台风造成的经济损失", limit=3)
    assert any(h.id == "typhoon" for h in hits)


def test_get_relevant_lessons_empty_db(tmp_path):
    """空库 / 无关查询不崩溃，返回空列表"""
    ltm = LongTermMemory(str(tmp_path / "m.db"))
    assert ltm.get_relevant_lessons("随便问点什么", limit=5) == []
    assert ltm.semantic_search_lessons("随便问点什么", limit=5) == []


def test_get_relevant_lessons_fallback_without_embedding(tmp_path):
    """旧库中无向量的 lesson：get_relevant_lessons 回退文本匹配，不丢失兼容"""
    ltm = LongTermMemory(str(tmp_path / "m.db"))
    # 直接写 lessons 表、不写 embedding，模拟历史数据
    conn = ltm._get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO lessons (id, project_id, agent_name, category, lesson, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            "legacy",
            "p",
            "gis_assistant:u",
            "success",
            "缓冲分析结果已导出 buffer.geojson",
            "2026-01-01T00:00:00",
        ),
    )
    conn.commit()
    conn.close()
    hits = ltm.get_relevant_lessons("缓冲分析", limit=5)
    assert any(h.id == "legacy" for h in hits)


# ── 3. 主动压缩阈值（红：现实现 est<=24000 不压缩） ─────────────────


def _long_session(total_chars: int, n_msgs: int = 15, summary: str = ""):
    """构造总内容长度约为 total_chars 的会话历史（每条消息占位）"""
    import types

    per = max(1, total_chars // n_msgs)
    body = "数据图层已加载并完成分析。" * (per // 11 + 1)
    messages = [{"role": "user", "content": body[:per]} for _ in range(n_msgs)]
    return types.SimpleNamespace(messages=messages, summary=summary)


def test_roll_summary_triggers_before_hard_threshold(tmp_path):
    """历史接近阈值（≥80%）即主动压缩，不必等超限"""
    agent = _agent(tmp_path)
    # est_tokens = total_chars // 3；选 20000 ∈ [19200, 24000)
    session = _long_session(total_chars=60000)
    est = sum(len(str(m.get("content") or "")) for m in session.messages) // 3
    assert 19200 <= est < COMPACT_THRESHOLD_TOKENS
    agent._maybe_roll_summary(session)
    assert session.summary, "主动压缩应生成滚动摘要"
    assert len(session.messages) <= HISTORY_WINDOW_MESSAGES, "压缩后历史窗口应被裁剪"


def test_roll_summary_not_triggered_under_warn_threshold(tmp_path):
    """远低于阈值时不压缩（避免频繁调用 LLM）"""
    agent = _agent(tmp_path)
    session = _long_session(total_chars=45000)  # est = 15000 < 19200
    agent._maybe_roll_summary(session)
    assert session.summary == "", "未达 warn 阈值不应压缩"
    assert len(session.messages) == 15


# ── 4. 长对话上下文有界 ────────────────────────────────────────────


def test_long_conversation_messages_bounded(tmp_path):
    """10+ 轮（60 条）历史注入后，发往 LLM 的消息数有界"""
    agent = _agent(tmp_path)
    import types

    msgs = [
        {
            "role": "user",
            "content": f"第 {i} 轮问题" if i % 2 == 0 else {"content": f"第 {i} 轮结果"},
        }
        for i in range(60)
    ]
    # 构造为真实消息形态
    msgs = []
    for i in range(60):
        if i % 2 == 0:
            msgs.append({"role": "user", "content": f"第 {i} 轮问题"})
        else:
            msgs.append({"role": "assistant", "content": f"第 {i} 轮回答"})
    session = types.SimpleNamespace(messages=msgs, summary="")
    out = agent._prepare_messages("新问题", None, session, "")
    assert len(out) <= HISTORY_WINDOW_MESSAGES + 3
    assert out[-1]["role"] == "user"
    assert out[0]["role"] == "system"


def test_long_conversation_tool_window_alignment(tmp_path):
    """窗口起点对齐：历史从 tool 消息截断时向前扩展，保证 tool 有前导"""
    agent = _agent(tmp_path)
    import types

    msgs = [
        {"role": "user", "content": "请求"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]},
    ]
    for _ in range(45):
        msgs.append({"role": "tool", "tool_call_id": "c1", "content": "{}"})
    session = types.SimpleNamespace(messages=msgs, summary="")
    out = agent._prepare_messages("新问题", None, session, "")
    roles = [m["role"] for m in out[1:-1]]
    assert roles[0] != "tool", "窗口首条不应是 tool 消息（须对齐前导）"
    assert "tool" in roles


# ── 5. 跨会话召回历史结论与产物引用 ────────────────────────────────


def test_cross_session_recall_hint(tmp_path, monkeypatch):
    """历史会话产出的结论与产物文件名，应能在新会话被 hint 召回"""
    import src.web.server as server

    ltm_tmp = LongTermMemory(str(tmp_path / "m.db"))
    ltm_tmp.save_lesson(
        _lesson(
            "typhoon",
            "GIS 任务完成：分析广东台风经济损失 → 广东省受灾最重约 120 亿（产物: damage_map.png）",
        )
    )
    monkeypatch.setattr(server, "ltm", ltm_tmp)
    hint = server._build_ltm_hint("帮我分析广东台风造成的经济损失", "u")
    assert "台风" in hint
    assert "damage_map.png" in hint
