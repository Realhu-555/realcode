"""GIS 基准任务集评测器测试 — 检查函数 + run_one 汇总逻辑"""

from pathlib import Path

from src.gis_toolkit import bench
from src.gis_toolkit.engine import GisEngine


def _result(tools, outputs=None):
    return {
        "trajectory": [{"tool": t} for t in tools],
        "outputs": outputs or [],
        "steps": len(tools),
        "timed_out": False,
        "final": "",
    }


# ── 检查函数 ─────────────────────────────────────────

def test_tool_called():
    ok, _ = bench._tool_called(_result(["load_data", "choropleth"]), "choropleth")
    assert ok is True
    ok, _ = bench._tool_called(_result(["load_data"]), "choropleth")
    assert ok is False


def test_finish_called():
    assert bench._finish_called(_result(["choropleth", "finish"]))[0] is True
    assert bench._finish_called(_result(["choropleth"]))[0] is False
    assert bench._finish_called(_result([]))[0] is False


def test_has_output():
    assert bench._has_output(_result([], ["a.png", "b.csv"]), ".png")[0] is True
    assert bench._has_output(_result([], ["b.csv"]), ".png")[0] is False


def test_file_and_png_checks(tmp_path):
    engine = GisEngine(out_dir=str(tmp_path), allowed_roots=[str(tmp_path), "data"])
    assert bench._file_exists(engine, "nope.png")[0] is False
    p = engine.out_dir / "map.png"
    p.write_bytes(b"x" * 15_000)
    assert bench._file_exists(engine, "map.png")[0] is True
    assert bench._png_size_ok(engine, "map.png", 10_000)[0] is True
    assert bench._png_size_ok(engine, "map.png", 99_999)[0] is False


def test_csv_checks(tmp_path):
    engine = GisEngine(out_dir=str(tmp_path), allowed_roots=[str(tmp_path), "data"])
    (engine.out_dir / "s.csv").write_text("province,gdp\n北京,100\n上海,200\n", encoding="utf-8-sig")
    assert bench._csv_rows(engine, "s.csv", 2)[0] is True
    assert bench._csv_rows(engine, "s.csv", 3)[0] is False
    assert bench._csv_columns(engine, "s.csv", ["province", "gdp"])[0] is True
    assert bench._csv_sum_total(engine, "s.csv", "gdp", 300.0)[0] is True
    assert bench._csv_sum_total(engine, "s.csv", "gdp", 301.0)[0] is False


def test_buffer_area_grew(tmp_path):
    engine = GisEngine(out_dir=str(tmp_path), allowed_roots=[str(tmp_path), "data"])
    assert bench._buffer_area_grew(engine)[0] is False  # 无图层
    engine.load_data(bench.CITIES_GEOJSON)
    engine.buffer(1.0)
    ok, _ = bench._buffer_area_grew(engine)
    assert ok is True


# ── run_one 汇总逻辑 ─────────────────────────────────

def test_run_one_all_pass(tmp_path, monkeypatch):
    def fake_run(self, request, data_file=None):
        self.engine.out_dir.mkdir(parents=True, exist_ok=True)
        (self.engine.out_dir / "choropleth.png").write_bytes(b"\x89PNG" + b"0" * 12_000)
        self.engine.outputs.append("choropleth.png")
        return _result(["choropleth", "finish"], ["choropleth.png"])

    monkeypatch.setattr(bench.GisToolAgent, "run", fake_run)
    report = bench.run_one(bench.TASKS[0], Path(tmp_path))
    assert report["pass"] is True
    assert all(c["pass"] for c in report["checks"])


def test_run_one_detects_missing_tool(tmp_path, monkeypatch):
    def fake_run(self, request, data_file=None):
        return _result(["finish"], [])

    monkeypatch.setattr(bench.GisToolAgent, "run", fake_run)
    report = bench.run_one(bench.TASKS[0], Path(tmp_path))
    assert report["pass"] is False
    failed = [c for c in report["checks"] if not c["pass"]]
    assert any(c["name"] == "tool_called_choropleth" for c in failed)
