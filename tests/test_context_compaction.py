"""会话上下文管理与 auto-compact 工具函数单测（C1-C3 纯函数层 + session 持久化）

覆盖：
- C1：触发阈值按模型 context_window × pct 缩放（不再固定 24000）
- C2：tool-pair-safe 窗口切分 / FullReplace 材料截断
- C3：退化摘要拒绝 / 缩减率校验
- session.compacted 持久化 roundtrip
"""

import pytest
from src.gis_toolkit import context as ctx
from src.gis_toolkit.engine import GisEngine
from src.gis_toolkit.session import GisSession


@pytest.fixture(autouse=True)
def _session_engine_local(monkeypatch):
    """GisSession 构造按 .env 的 GIS_ENGINE=live 会连 QGIS 插件（8756）；
    测试环境统一替换为本地 geopandas 引擎，不依赖 QGIS 是否打开。"""

    def _fake_engine(**kwargs):
        kwargs.pop("engine", None)
        return GisEngine(**kwargs)

    monkeypatch.setattr("src.gis_toolkit.session.create_gis_engine", _fake_engine)


# ── C1 触发阈值 ─────────────────────────────────────────────────────


def test_trigger_threshold_scales_with_context_window():
    """阈值 = context × pct：128k×85%=108800，32k×85%=27200，不再是固定 24000"""
    assert ctx.trigger_threshold(128000) == 108800
    assert ctx.trigger_threshold(32768) == int(32768 * 0.85)
    assert ctx.trigger_threshold(32768, pct=80) == int(32768 * 0.80)
    assert ctx.trigger_threshold(128000) > ctx.trigger_threshold(32000)


def test_target_threshold_scales_with_context_window():
    assert ctx.target_threshold(128000) == 64000
    assert ctx.target_threshold(128000, pct=30) == int(128000 * 0.30)


def test_estimate_tokens_text_min_one():
    assert ctx.estimate_tokens_text("") == 0
    assert ctx.estimate_tokens_text("你好") == 1
    assert abs(ctx.estimate_tokens_text("a" * 300) - 100) <= 1


# ── C2 窗口与压缩材料 ───────────────────────────────────────────────


def _round_trip(n_rounds: int) -> list[dict]:
    msgs: list[dict] = []
    for i in range(n_rounds):
        msgs.append({"role": "user", "content": f"u{i}"})
        msgs.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": f"c{i}",
                        "type": "function",
                        "function": {"name": "load_data", "arguments": f'{{"f": "{i}"}}'},
                    }
                ],
            }
        )
        msgs.append({"role": "tool", "tool_call_id": f"c{i}", "content": f"ok{i}"})
    return msgs


def test_window_messages_aligned_no_orphan_tool():
    """窗口起点 tool-pair-safe：不出现孤立 tool（起点是 tool 时向前对齐到 assistant）"""
    msgs = _round_trip(15)  # 45 条
    win = ctx.window_messages(msgs, 40)
    # 45-40=5 落在 tool 上，向前对齐到 assistant(4)：窗口可能比 limit 多 1 条
    assert len(win) <= 41
    if win[0].get("role") == "tool":
        raise AssertionError("窗口起点不应是 tool")
    for j, m in enumerate(win):
        if m.get("role") == "tool":
            assert win[j - 1].get("role") == "assistant"


def test_window_messages_full_when_within_limit():
    msgs = _round_trip(3)  # 9 条
    assert ctx.window_messages(msgs, 40) == msgs


def test_material_for_compact_respects_cap():
    """材料总字符量 ≤ cap，且不出现孤立 tool 开头"""
    msgs = _round_trip(20)  # 60 条
    mat = ctx.material_for_compact(msgs, cap_chars=1000)
    chars = sum(len(m.get("content") or "") for m in mat)
    assert chars <= 1000
    assert mat[0]["role"] != "tool"


def test_material_for_compact_empty():
    assert ctx.material_for_compact([]) == []


def test_messages_to_text_flattens_tool_calls():
    msgs = [
        {"role": "user", "content": "加载数据"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "c0",
                    "type": "function",
                    "function": {"name": "load_data", "arguments": '{"f": "a.geojson"}'},
                }
            ],
        },
    ]
    text = ctx.messages_to_text(msgs)
    assert "[user] 加载数据" in text
    assert 'load_data({"f": "a.geojson"})' in text
    assert ctx.messages_to_text([]) == ""


# ── C3 质量护栏 ─────────────────────────────────────────────────────


def test_degenerate_rejects_empty_and_short():
    assert ctx.is_degenerate_summary("") is True
    assert ctx.is_degenerate_summary("   ") is True
    assert ctx.is_degenerate_summary("太短") is True  # < min_chars


def test_degenerate_rejects_identical_to_old():
    old = "旧摘要：已完成 gdp_map.png 分级设色"
    assert ctx.is_degenerate_summary(old, old) is True


def test_degenerate_rejects_repeated_lines():
    text = "产物 gdp_map.png\n产物 gdp_map.png\n产物 gdp_map.png"
    assert ctx.is_degenerate_summary(text) is True


def test_normal_summary_accepted():
    text = "已完成 GDP 分级设色（产物 gdp_map.png）；图层状态已保留；经济损失约 120 亿。"
    assert ctx.is_degenerate_summary(text, "旧摘要") is False


def test_single_line_summary_not_degenerate():
    """单行摘要不应被行重复规则误判"""
    text = "已完成 GDP 分级设色，产物 gdp_map.png，结论广东省受灾最重约 120 亿。"
    assert ctx.is_degenerate_summary(text) is False


def test_reduction_ok_ratio():
    assert ctx.reduction_ok(1000, 100) is True
    assert ctx.reduction_ok(1000, 900, max_ratio=0.8) is False
    assert ctx.reduction_ok(1000, 0) is False


# ── session.compacted 持久化 ────────────────────────────────────────


def test_session_compacted_roundtrip(tmp_path):
    out = tmp_path / "sessions"
    out.mkdir(exist_ok=True)
    sess = GisSession("s1", out)
    sess.summary = "已完成分析，产物 gdp_map.png"
    sess.compacted = True
    sess.messages = [{"role": "user", "content": "hi"}]
    d = sess.to_dict()
    assert d["compacted"] is True

    restored = GisSession.from_dict(d)
    assert restored.compacted is True
    assert restored.summary == sess.summary


def test_session_compacted_default_false(tmp_path):
    out = tmp_path / "sessions"
    out.mkdir(exist_ok=True)
    sess = GisSession("s2", out)
    assert sess.compacted is False
    # 旧数据无 compacted 键 → 默认 False（向后兼容）
    d = sess.to_dict()
    d.pop("compacted", None)
    restored = GisSession.from_dict(d)
    assert restored.compacted is False
