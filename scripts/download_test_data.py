"""下载 GIS 测试数据（DataV.GeoAtlas 中国行政区划边界）。

用法：
    python scripts/download_test_data.py

数据来源：https://datav.aliyun.com/portal/school/atlas/area_selector
说明：行政边界来自公开 GeoAtlas 服务，仅用于本地功能测试。
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = PROJECT_ROOT / "data" / "gis_base"
BASE_URL = "https://geo.datav.aliyun.com/areas_v3/bound/"

# 输出文件名 → DataV 源文件名（adcode_full.json）
TARGETS: dict[str, str] = {
    # 全国（含省级 35 要素）
    "china_provinces_full.geojson": "100000_full.json",
    # 直辖市/特别行政区：区县级
    "beijing_districts.geojson": "110000_full.json",
    "shanghai_districts.geojson": "310000_full.json",
    "chongqing_districts.geojson": "500000_full.json",
    "hongkong_districts.geojson": "810000_full.json",
    "macau_districts.geojson": "820000_full.json",
    # 省份：市级
    "guangdong_cities.geojson": "440000_full.json",
    "sichuan_cities.geojson": "510000_full.json",
    "zhejiang_cities.geojson": "330000_full.json",
    "jiangsu_cities.geojson": "320000_full.json",
    "henan_cities.geojson": "410000_full.json",
    "shandong_cities.geojson": "370000_full.json",
    "hubei_cities.geojson": "420000_full.json",
    "shaanxi_cities.geojson": "610000_full.json",
    "taiwan_cities.geojson": "710000_full.json",
    # 地级市：区县级
    "guangzhou_districts.geojson": "440100_full.json",
    "chengdu_districts.geojson": "510100_full.json",
}


def download(name: str, src: str) -> None:
    path = BASE_DIR / name
    if path.exists():
        print(f"跳过(已存在): {name}")
        return
    req = urllib.request.Request(BASE_URL + src, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read()
    data = json.loads(raw)
    features = data.get("features", [])
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"下载 {name}: {len(features)} 个要素, {len(raw) // 1024}KB")


def main() -> int:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    failed = 0
    for name, src in TARGETS.items():
        try:
            download(name, src)
        except Exception as exc:  # noqa: BLE001 - 单个文件失败不阻断整体
            failed += 1
            print(f"失败 {name}: {exc}")
    print(f"完成，失败 {failed} 个")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
