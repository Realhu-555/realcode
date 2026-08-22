"""产物校验器（T6）— 工具产物生成后自动校验，FAIL 由 agent 回环重试。

校验规则（引擎无关，只用文件路径）：
- PNG/JPG：文件存在且非空；
- CSV：文件存在且可读、有数据行；
- GeoJSON/SHP：文件存在且可读、有要素。
"""

from __future__ import annotations

from pathlib import Path

_PNG_EXTS = {".png", ".jpg", ".jpeg"}
_CSV_EXTS = {".csv"}
_VECTOR_EXTS = {".geojson", ".json", ".shp", ".zip"}


def check_outputs(result: dict) -> list[str]:
    """校验工具返回中的产物，返回错误列表（空列表 = 通过）"""
    errors: list[str] = []
    paths = result.get("output_paths") or []
    if not paths:
        return errors  # 无产物声明，跳过校验
    for p in paths:
        path = Path(p)
        if not path.is_file():
            errors.append(f"产物文件不存在: {p}")
            continue
        ext = path.suffix.lower()
        if ext in _PNG_EXTS:
            if path.stat().st_size <= 0:
                errors.append(f"图片产物为空: {p}")
        elif ext in _CSV_EXTS:
            errors.extend(_check_csv(path))
        elif ext in _VECTOR_EXTS:
            errors.extend(_check_vector(path))
    return errors


def _check_csv(path: Path) -> list[str]:
    try:
        import pandas as pd

        df = pd.read_csv(path, nrows=2)
        if df.empty:
            return [f"CSV 产物无数据行: {path}"]
        return []
    except Exception as exc:
        return [f"CSV 产物无法读取: {path}（{exc}）"]


def _check_vector(path: Path) -> list[str]:
    try:
        import geopandas as gpd

        gdf = gpd.read_file(path, rows=1)
        if len(gdf) == 0:
            return [f"矢量产物无要素: {path}"]
        return []
    except Exception as exc:
        return [f"矢量产物无法读取: {path}（{exc}）"]
