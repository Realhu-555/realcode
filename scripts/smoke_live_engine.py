"""M2a 冒烟：验证主进程 LiveEngine 能读到用户当前打开的 QGIS 工程状态。

前置：QGIS 已打开并启用 GIS Assistant Live 插件（复制 Token 到 .env LIVE_QGIS_TOKEN）。

运行：
    venv\\Scripts\\python.exe scripts/smoke_live_engine.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gis_toolkit.live_engine import LiveEngine  # noqa: E402


def main() -> int:
    engine = LiveEngine()
    info = engine.get_project_info()
    print("get_project_info:", json.dumps(info, ensure_ascii=True, indent=2))
    layers = engine.list_layers()
    print("list_layers:", json.dumps(layers, ensure_ascii=True))
    print("SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
