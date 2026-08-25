"""结果审核 L1：validate_final_numbers 规则校验 + 统计工具 stats 生成单测。

覆盖：精确匹配 / 量级错误（12.6 vs 126）/ 万亿-亿单位换算 / 未引用结论性大数 WARN /
无数字结论 WARN / 无 stats 旧工具向后兼容；summarize/field_statistics/unique_values/load_data 的 stats。
"""


from src.gis_toolkit.engine import GisEngine
from src.gis_toolkit.validate import validate_final_numbers

# ── validate_final_numbers：纯函数 ──


def test_exact_match_passes():
    trajectory = [{"tool": "summarize", "result": {"status": "ok", "stats": {"total": 1000.0}}}]
    out = validate_final_numbers("总销售额为 1000 元，图表已保存", trajectory)
    assert out["verdict"] == "PASS"
    assert out["issues"] == []


def test_magnitude_error_fails():
    # 验收锚点：stats.total=126.3（万亿口径），final 写成 12.6 万亿 → 差 10 倍 → FAIL
    trajectory = [{"tool": "summarize", "result": {"status": "ok", "stats": {"total": 126.3}}}]
    out = validate_final_numbers("全国 GDP 合计约 12.6 万亿元", trajectory)
    assert out["verdict"] == "FAIL"
    assert any("量级" in (i.get("reason") or "") for i in out["issues"])


def test_unit_conversion_passes():
    # final 写 13.56 万亿 = stats 的 135673.2 亿 → 单位换算后一致 → PASS
    trajectory = [{"tool": "summarize", "result": {"status": "ok", "stats": {"total": 135673.2}}}]
    out = validate_final_numbers("全国合计约 13.56 万亿元", trajectory)
    assert out["verdict"] == "PASS"


def test_unverified_large_number_warns():
    # 结论性大数（合计附近、>100）在 stats 中找不到 → WARN
    trajectory = [{"tool": "summarize", "result": {"status": "ok", "stats": {"total": 1000.0}}}]
    out = validate_final_numbers("项目总投资合计约 5000 万元", trajectory)
    assert out["verdict"] == "WARN"


def test_missing_conclusion_warns():
    # 工具有关键统计，但 final 未引用任何数字 → WARN
    trajectory = [{"tool": "summarize", "result": {"status": "ok", "stats": {"total": 1000.0}}}]
    out = validate_final_numbers("任务已完成，图表已保存到产物目录", trajectory)
    assert out["verdict"] == "WARN"


def test_no_stats_no_numbers_passes():
    # 无 stats 且无数字（空任务）→ PASS
    out = validate_final_numbers("没有可执行的数据，已结束", [])
    assert out["verdict"] == "PASS"


def test_no_stats_backward_compat():
    # 旧工具返回不带 stats → 不报错，PASS
    trajectory = [{"tool": "load_data", "result": {"status": "ok", "message": "已加载"}}]
    out = validate_final_numbers("已加载数据文件", trajectory)
    assert out["verdict"] == "PASS"


def test_year_noise_filtered():
    # 年份 2024 不是候选数字（噪声过滤），不影响 1000 的精确匹配 → PASS
    trajectory = [{"tool": "summarize", "result": {"status": "ok", "stats": {"total": 1000.0}}}]
    out = validate_final_numbers("2024 年总销售额为 1000 元", trajectory)
    assert out["verdict"] == "PASS"


def test_aggregated_known_values_multi_stats():
    # 多个工具 stats 合并收集，全部命中 → PASS
    trajectory = [
        {"tool": "load_data", "result": {"status": "ok", "stats": {"rows": 31}}},
        {"tool": "summarize", "result": {"status": "ok", "stats": {"total": 126.3}}},
    ]
    out = validate_final_numbers("共加载 31 个省份，GDP 合计约 126.3 万亿元", trajectory)
    assert out["verdict"] == "PASS"


# ── 统计工具 stats 生成 ──


def _engine(tmp_path, data_file=None):
    return GisEngine(
        data_file=data_file,
        out_dir=str(tmp_path / "out"),
        allowed_roots=[str(tmp_path)],
    )


def _points_csv(tmp_path):
    p = tmp_path / "pts.csv"
    p.write_text(
        "name,prov,val,lon,lat\n"
        "A,北京,100,116,40\n"
        "B,北京,200,117,41\n"
        "C,上海,300,121,31\n",
        encoding="utf-8",
    )
    return str(p)


def test_load_data_stats(tmp_path):
    eng = _engine(tmp_path)
    res = eng.load_data(_points_csv(tmp_path))
    assert res["stats"]["rows"] == 3


def test_summarize_stats_sum(tmp_path):
    eng = _engine(tmp_path, data_file=_points_csv(tmp_path))
    res = eng.summarize(column="val", groupby="prov", agg="sum")
    st = res["stats"]
    assert st["total"] == 600.0
    assert st["rows"] == 3
    assert st["group_count"] == 2
    assert {t["k"] for t in st["top3"]} == {"北京", "上海"}


def test_summarize_stats_count(tmp_path):
    eng = _engine(tmp_path, data_file=_points_csv(tmp_path))
    res = eng.summarize(column="val", groupby="prov", agg="count")
    st = res["stats"]
    assert st["total"] == 3  # count 的 total = 行数
    assert st["rows"] == 3
    assert st["group_count"] == 2


def test_summarize_stats_without_groupby(tmp_path):
    eng = _engine(tmp_path, data_file=_points_csv(tmp_path))
    res = eng.summarize(column="val", agg="mean")
    st = res["stats"]
    assert st["total"] == 200.0
    assert st["group_count"] == 1
    assert res["summary_rows"] == 1


def test_field_statistics_stats(tmp_path):
    eng = _engine(tmp_path, data_file=_points_csv(tmp_path))
    res = eng.field_statistics("val")
    st = res["stats"]
    assert st["count"] == 3
    assert st["min"] == 100.0
    assert st["max"] == 300.0
    assert st["mean"] == 200.0
    assert st["sum"] == 600.0


def test_unique_values_stats(tmp_path):
    eng = _engine(tmp_path, data_file=_points_csv(tmp_path))
    res = eng.unique_values("prov")
    assert res["stats"]["count"] == 2
