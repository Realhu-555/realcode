"""GIS 数据检查工具 — 读取 CSV/GeoJSON 头部信息

安全约束：
- 只读，绝不写文件；
- 大小限制 10MB；
- 路径白名单：仅允许 project 的 data 目录（ctx.project_state["data_root"]）内的文件，
  防止 prompt injection 诱导读取 .env 等敏感文件。
"""

import csv
import json
from pathlib import Path

from src.tools.protocol import ToolContext, ToolDescription, ToolKind, ToolResult

MAX_SIZE_BYTES = 10 * 1024 * 1024
SAMPLE_ROWS = 5


class DataInspectTool:
    """读取数据文件字段清单与前几行样例"""

    tool_id = "data_inspect"
    kind = ToolKind.READ
    description = ToolDescription(
        name="data_inspect",
        description="读取数据文件（CSV/GeoJSON）的字段清单、前几行样例和记录数，用于判断字段名、坐标列、数据规模。只读，不修改任何文件。",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "数据文件路径（项目 data 目录内的相对或绝对路径）",
                },
            },
            "required": ["path"],
        },
    )

    async def execute(self, ctx: ToolContext, path: str) -> ToolResult:
        try:
            info = _inspect(path, _allowed_root(ctx))
            return ToolResult(success=True, data=info)
        except ValueError as exc:
            return ToolResult(success=False, data=None, error=str(exc))


def inspect_file(path: str, data_root: str) -> dict:
    """同步入口：pipeline 预注入 data_schema 用（绕开 async ToolContext）"""
    return _inspect(path, Path(data_root).resolve())


def _allowed_root(ctx: ToolContext) -> Path:
    root = ctx.project_state.get("data_root")
    if not root:
        raise ValueError("未配置 data_root（项目数据目录），拒绝访问")
    return Path(root).resolve()


def _inspect(path: str, root: Path) -> dict:
    target = Path(path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError(f"路径不在允许的数据目录内: {path}") from None
    if not target.is_file():
        raise ValueError(f"文件不存在: {path}")
    size = target.stat().st_size
    if size > MAX_SIZE_BYTES:
        raise ValueError(f"文件超过 10MB 限制: {size} bytes")

    suffix = target.suffix.lower()
    if suffix == ".csv":
        return _inspect_csv(target)
    if suffix == ".geojson":
        return _inspect_geojson(target)
    raise ValueError(f"不支持的文件类型: {suffix}（支持 .csv / .geojson）")


def _inspect_csv(target: Path) -> dict:
    with target.open("r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("CSV 文件为空") from None
        sample = [row for _, row in zip(range(SAMPLE_ROWS), reader, strict=False)]
    return {
        "format": "csv",
        "fields": header,
        "field_count": len(header),
        "sample_rows": sample,
        "row_count": _count_csv_rows(target),
        "note": "若存在经度/纬度或 lon/lat 列，可用 points_from_xy 转为点要素",
    }


def _count_csv_rows(target: Path) -> int:
    count = 0
    with target.open("r", encoding="utf-8-sig", errors="replace") as f:
        for _ in f:
            count += 1
    return max(count - 1, 0)


def _inspect_geojson(target: Path) -> dict:
    data = json.loads(target.read_text(encoding="utf-8"))
    features = data.get("features", [])
    props: dict[str, str] = {}
    geom_types: set[str] = set()
    for ft in features[:50]:
        props.update({k: type(v).__name__ for k, v in (ft.get("properties") or {}).items()})
        gtype = (ft.get("geometry") or {}).get("type")
        if gtype:
            geom_types.add(gtype)
    return {
        "format": "geojson",
        "feature_count": len(features),
        "fields": list(props),
        "field_types": props,
        "geometry_types": sorted(geom_types),
    }
