"""GIS 沙箱安全扫描与脚本执行测试"""

from src.sandbox.executor import SandboxExecutor
from src.sandbox.security import scan_script

# ── scan_script：拒绝危险模式 ──────────────────────────


def test_scan_rejects_os_remove():
    violations = scan_script('import os\nos.remove("data.csv")')
    assert any("os.remove" in v for v in violations)


def test_scan_rejects_shutil_rmtree():
    violations = scan_script('import shutil\nshutil.rmtree(".")')
    assert any("shutil.rmtree" in v for v in violations)


def test_scan_rejects_network_import():
    for mod in ("requests", "socket", "urllib"):
        violations = scan_script(f"import {mod}\nprint(1)")
        assert any(mod in v for v in violations), mod


def test_scan_rejects_os_import():
    violations = scan_script("import os\nprint(os.getcwd())")
    assert any("os" in v for v in violations)


def test_scan_rejects_eval_and_exec():
    assert any("eval" in v for v in scan_script('eval("1+1")'))
    assert any("exec" in v for v in scan_script('exec("x=1")'))


def test_scan_rejects_open_write_mode():
    violations = scan_script('with open("out.csv", "w") as f:\n    f.write("1")')
    assert any("写模式" in v for v in violations)
    # 只读打开允许
    assert scan_script('with open("data.csv") as f:\n    print(f.read())') == []


def test_scan_rejects_absolute_path():
    violations = scan_script('with open("C:/Users/me/.env") as f:\n    print(f.read())')
    assert any("绝对路径" in v for v in violations)


def test_scan_rejects_syntax_error():
    violations = scan_script("def broken(:")
    assert any("语法错误" in v for v in violations)


# ── scan_script：允许正常 GIS 脚本 ─────────────────────


def test_scan_allows_geopandas_script():
    source = (
        "import pandas as pd\n"
        "import geopandas as gpd\n"
        "import matplotlib.pyplot as plt\n"
        'df = pd.read_csv("gdp.csv")\n'
        'gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")\n'
        "fig, ax = plt.subplots()\n"
        'gdf.plot(ax=ax, column="gdp")\n'
        'fig.savefig("out.png")\n'
        'print("DONE")\n'
    )
    assert scan_script(source) == []


# ── run_script：沙箱内执行 ─────────────────────────────


def test_run_script_ok(sandbox: SandboxExecutor):
    output, code = sandbox.run_script("main.py", 'print("hello sandbox")')
    assert code == 0
    assert "hello sandbox" in output


def test_run_script_rejects_os_remove(sandbox: SandboxExecutor):
    output, code = sandbox.run_script("evil.py", 'import os\nos.remove("x.csv")')
    assert code == -2
    assert "安全扫描拒绝" in output


def test_run_script_writes_and_reads_file(sandbox: SandboxExecutor):
    source = (
        "import pandas as pd\n"
        'df = pd.DataFrame({"a": [1, 2, 3]})\n'
        'df.to_csv("out.csv", index=False)\n'
        'print("ROWS:", len(df))\n'
    )
    output, code = sandbox.run_script("main.py", source)
    assert code == 0
    assert "ROWS: 3" in output
    assert sandbox.file_exists("out.csv")
    assert "a" in sandbox.read_file("out.csv")
