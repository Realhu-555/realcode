"""插件侧工具执行器 — 操作「用户当前打开的 QGIS 工程」（必须在 GUI 主线程调用）。

与主进程 LiveEngine 一一对应，语义对齐 geopandas/qgis 引擎：
- 当前图层 = 会话内最近一次 load_data / buffer / duplicate_layer 得到的工程图层；
- 结果图层会真实加入 QgsProject（用户在图层树可见），并置为当前图层；
- 产物文件写入每次 invoke 请求携带的 out_dir（由主进程白名单决定，插件不另做路径信任）。

本文件只实现 M2b 首批工具；其余工具由 invoke() 返回明确的不支持提示。
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

DEFAULT_CRS = "EPSG:4326"
_LON_COLS = ("lon", "lng", "longitude", "经度", "x")
_LAT_COLS = ("lat", "latitude", "纬度", "y")
_SAFE_NAME = re.compile(r"^[\w.\-]+$")

STATE: dict = {"layer": None, "out_dir": None}


# ── 通用小工具 ──


def _result(message: str, **extra) -> dict:
    return {"status": "ok", "message": message, **extra}


def _crs_str(layer: QgsVectorLayer) -> str:
    return layer.crs().authid() or layer.crs().toWkt()


def _field_names(layer: QgsVectorLayer) -> list[str]:
    return [field.name() for field in layer.fields()]


def _geometry_type(layer: QgsVectorLayer) -> str:
    return QgsWkbTypes.displayString(layer.wkbType())


def _summary(layer: QgsVectorLayer) -> dict:
    return {
        "name": layer.name(),
        "rows": int(layer.featureCount()),
        "columns": _field_names(layer),
        "crs": _crs_str(layer),
        "geometry_type": _geometry_type(layer),
    }


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _current() -> QgsVectorLayer:
    layer = STATE.get("layer")
    if layer is None or not layer.isValid():
        raise RuntimeError("当前没有可操作图层，请先 load_data 加载一个图层")
    return layer


def _out_dir() -> str:
    out_dir = STATE.get("out_dir")
    if not out_dir:
        raise RuntimeError("缺少产物输出目录（out_dir）")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    return out_dir


def _sanitize_filename(name: str) -> str:
    base = os.path.basename(name or "")
    if not base or not _SAFE_NAME.match(base):
        raise RuntimeError(f"非法产物文件名: {name!r}（只允许字母/数字/._-，禁止路径）")
    return base


def _pick_col(headers: list[str], candidates: tuple[str, ...]) -> str | None:
    lower = {str(h).lower(): h for h in headers}
    for cand in candidates:
        if cand.lower() in lower:
            return str(lower[cand.lower()])
    return None


def _new_memory_layer(name: str, geom_type: str, crs: str, fields=None) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"{geom_type}?crs={crs}", name, "memory")
    if fields is not None:
        layer.dataProvider().addAttributes(fields)
        layer.updateFields()
    return layer


def _ensure_unique_name(name: str) -> str:
    """若工程里已有同名图层，追加序号，避免混淆。"""
    existing = {layer.name() for layer in QgsProject.instance().mapLayers().values()}
    if name not in existing:
        return name
    index = 2
    while f"{name}_{index}" in existing:
        index += 1
    return f"{name}_{index}"


def _add_to_project(layer: QgsVectorLayer) -> None:
    """把图层加入当前工程并设为当前图层。"""
    QgsProject.instance().addMapLayer(layer)
    STATE["layer"] = layer


def _load_layer(path: str) -> QgsVectorLayer:
    """按后缀加载外部数据：CSV → delimitedtext 点层；其余 → ogr。"""
    name = Path(path).stem
    if path.lower().endswith(".csv"):
        with open(path, encoding="utf-8-sig", newline="") as fh:
            headers = [h.strip().strip('"') for h in next(csv.reader(fh))]
        x_col = _pick_col(headers, _LON_COLS)
        y_col = _pick_col(headers, _LAT_COLS)
        if not (x_col and y_col):
            raise RuntimeError(f"CSV 缺少经纬度列（表头: {headers}），无法转成空间数据")
        uri = (
            f"file:///{path.replace(os.sep, '/')}"
            f"?delimiter=,&xField={x_col}&yField={y_col}&crs={DEFAULT_CRS}&encoding=UTF-8"
        )
        layer = QgsVectorLayer(uri, name, "delimitedtext")
    else:
        layer = QgsVectorLayer(path, name, "ogr")
    if not layer.isValid():
        raise RuntimeError(f"无法加载 {path}，QGIS 图层无效")
    if not layer.crs().isValid():
        layer.setCrs(QgsCoordinateReferenceSystem(DEFAULT_CRS))
    return layer


def _require_editing() -> QgsVectorLayer:
    layer = _current()
    if not layer.isEditable():
        raise RuntimeError("未开始编辑，请先 start_editing")
    return layer


def _memory_type_string(layer: QgsVectorLayer) -> str:
    """把图层 wkbType 映射为 memory provider 能识别的几何类型名。"""
    return QgsWkbTypes.displayString(layer.wkbType())


def _check_geometry_compatible(layer: QgsVectorLayer, geometry: QgsGeometry) -> None:
    """新增要素前预检几何类型：不匹配时提前报错，避免 commit 阶段才失败。"""
    wkb_type = geometry.wkbType()
    if wkb_type == QgsWkbTypes.Unknown:
        return
    layer_geom_type = QgsWkbTypes.geometryType(layer.wkbType())
    feature_geom_type = QgsWkbTypes.geometryType(wkb_type)
    if layer_geom_type != QgsWkbTypes.UnknownGeometry and layer_geom_type != feature_geom_type:
        expected = _memory_type_string(layer)
        got = QgsWkbTypes.displayString(wkb_type)
        raise RuntimeError(
            f"几何类型不匹配：当前图层是 {expected}，不能添加 {got}。"
            "请加载点/线/面类型匹配的数据，或换个匹配的几何。"
        )


def _infer_qvariant(value):
    if isinstance(value, bool):
        return QVariant.Bool
    if isinstance(value, int):
        return QVariant.Int
    if isinstance(value, float):
        return QVariant.Double
    return QVariant.String


# ── M2b 首批工具 ──


def tool_load_data(path: str) -> dict:
    layer = _load_layer(path)
    layer.setName(_ensure_unique_name(layer.name()))
    _add_to_project(layer)
    return _result(
        f"已加载 {layer.name()} 到当前工程（{layer.featureCount()} 行）",
        layer=_summary(layer),
    )


def tool_inspect_data() -> dict:
    layer = _current()
    extent = layer.extent()
    samples = []
    for index, feature in enumerate(layer.getFeatures()):
        if index >= 5:
            break
        samples.append(
            {field.name(): _jsonable(feature.attribute(field.name())) for field in layer.fields()}
        )
    return {
        "status": "ok",
        "message": f"图层 {layer.featureCount()} 行，CRS: {_crs_str(layer)}",
        **_summary(layer),
        "bounds": [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()],
        "sample_rows": samples,
    }


def tool_buffer(distance: float) -> dict:
    layer = _current()
    out = _new_memory_layer(
        _ensure_unique_name(layer.name() + "_buffer"),
        "MultiPolygon",
        _crs_str(layer),
        layer.fields(),
    )
    out.startEditing()
    for feature in layer.getFeatures():
        geometry = feature.geometry()
        if geometry is None or geometry.isEmpty():
            continue
        new_geometry = geometry.buffer(float(distance), 16)
        new_geometry.convertToMultiType()
        new_feature = QgsFeature(out.fields())
        new_feature.setGeometry(new_geometry)
        new_feature.setAttributes(feature.attributes())
        out.addFeature(new_feature)
    out.commitChanges()
    _add_to_project(out)
    return _result(
        f"已生成 {distance} 单位缓冲区并加入工程（图层: {out.name()}，CRS: {_crs_str(out)}）",
        layer=_summary(out),
    )


def tool_start_editing() -> dict:
    layer = _current()
    if layer.isEditable():
        raise RuntimeError("已在编辑会话中，先 commit_edits 或 rollback_edits")
    if not layer.startEditing():
        raise RuntimeError("开始编辑失败")
    return _result("已开始编辑会话（修改在 commit 前不生效）")


def tool_add_features(geometry: str, attributes: dict | None = None) -> dict:
    layer = _require_editing()
    g = QgsGeometry.fromWkt(geometry)
    if g.isNull():
        raise RuntimeError(f"无效 WKT 几何: {geometry}")
    _check_geometry_compatible(layer, g)
    feature = QgsFeature(layer.fields())
    feature.setGeometry(g)
    for key, value in (attributes or {}).items():
        index = layer.fields().indexOf(key)
        if index >= 0:
            feature.setAttribute(index, value)
    if not layer.addFeature(feature):
        raise RuntimeError("新增要素失败")
    return _result("已新增 1 个要素（待 commit）")


def tool_update_features(where: str, attributes: dict) -> dict:
    layer = _require_editing()
    expression = QgsExpression(where)
    if expression.hasParserError():
        raise RuntimeError(f"条件表达式无效: {expression.parserErrorString()}")
    context = QgsExpressionContext()
    context.appendScope(QgsExpressionContextUtils.layerScope(layer))
    updated = 0
    for feature in layer.getFeatures():
        context.setFeature(feature)
        if not expression.evaluate(context):
            continue
        for key, value in (attributes or {}).items():
            index = layer.fields().indexOf(key)
            if index < 0:
                raise RuntimeError(f"列不存在: {key}（可用列: {_field_names(layer)}）")
            layer.changeAttributeValue(feature.id(), index, value)
        updated += 1
    return _result(f"已更新 {updated} 个要素（待 commit）")


def tool_delete_features(ids: list) -> dict:
    layer = _require_editing()
    feature_ids = [feature.id() for feature in layer.getFeatures()]
    drop = [feature_ids[int(i)] for i in ids if 0 <= int(i) < len(feature_ids)]
    if not drop:
        raise RuntimeError("所有行号越界或 ids 为空")
    if not layer.deleteFeatures(drop):
        raise RuntimeError("删除要素失败")
    return _result(f"已删除 {len(drop)} 个要素（待 commit）")


def tool_calculate_field(expression: str, field_name: str, where: str | None = None) -> dict:
    layer = _require_editing()
    columns = _field_names(layer)
    if field_name in columns:
        raise RuntimeError(f"字段已存在: {field_name}（可用列: {columns}）")
    expr = QgsExpression(expression)
    if expr.hasParserError():
        raise RuntimeError(f"计算表达式无效: {expr.parserErrorString()}")
    for column in expr.referencedColumns():
        if column and column not in columns:
            raise RuntimeError(f"表达式引用了不存在的字段: {column}（可用列: {columns}）")
    context = QgsExpressionContext()
    context.appendScope(QgsExpressionContextUtils.layerScope(layer))
    where_expr = None
    if where:
        where_expr = QgsExpression(where)
        if where_expr.hasParserError():
            raise RuntimeError(f"条件表达式无效: {where_expr.parserErrorString()}")
        for column in where_expr.referencedColumns():
            if column and column not in columns:
                raise RuntimeError(f"条件引用了不存在的字段: {column}（可用列: {columns}）")
    qtype = QVariant.String
    for feature in layer.getFeatures():
        context.setFeature(feature)
        if where_expr is not None and not where_expr.evaluate(context):
            continue
        value = expr.evaluate(context)
        if value is not None:
            qtype = _infer_qvariant(value)
            break
    field = QgsField(field_name, qtype)
    if not layer.addAttribute(field):
        raise RuntimeError("添加字段失败")
    layer.updateFields()
    index = layer.fields().indexOf(field_name)
    calculated = 0
    for feature in layer.getFeatures():
        context.setFeature(feature)
        if where_expr is not None and not where_expr.evaluate(context):
            continue
        layer.changeAttributeValue(feature.id(), index, expr.evaluate(context))
        calculated += 1
    return _result(f"已新增字段 {field_name}（待 commit，计算 {calculated} 个要素）")


def tool_commit_edits() -> dict:
    layer = _current()
    if not layer.isEditable():
        raise RuntimeError("未开始编辑，请先 start_editing")
    if not layer.commitChanges():
        errors = list(layer.commitErrors())
        layer.rollBack()
        detail = ("；".join(errors[:5])) if errors else "未知原因"
        raise RuntimeError(f"提交失败，已回滚：{detail}")
    return _result("已提交编辑，修改已生效")


def tool_rollback_edits() -> dict:
    layer = _current()
    if not layer.isEditable():
        raise RuntimeError("未开始编辑，请先 start_editing")
    layer.rollBack()
    return _result("已回滚编辑，修改已丢弃")


def tool_export_geojson(output: str = "layer.geojson") -> dict:
    layer = _current()
    filename = _sanitize_filename(output)
    out_path = os.path.join(_out_dir(), filename)
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GeoJSON"
    options.fileEncoding = "utf-8"
    error, _, _, msg = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, out_path, QgsCoordinateTransformContext(), options
    )
    if error != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"导出 GeoJSON 失败: {error} {msg}")
    return _result(
        f"已导出 {filename}（{layer.featureCount()} 行）",
        output=filename,
        size_bytes=os.path.getsize(out_path),
    )


def tool_duplicate_layer() -> dict:
    """复制当前图层为内存新图层并加入工程（QGIS 3.40 无 duplicateLayer API，逐要素复制）。"""
    layer = _current()
    new_layer = _new_memory_layer(
        _ensure_unique_name(layer.name() + "_copy"),
        _memory_type_string(layer),
        _crs_str(layer),
        layer.fields(),
    )
    new_layer.startEditing()
    for feature in layer.getFeatures():
        new_feature = QgsFeature(new_layer.fields())
        new_feature.setGeometry(feature.geometry())
        new_feature.setAttributes(feature.attributes())
        new_layer.addFeature(new_feature)
    if not new_layer.commitChanges():
        raise RuntimeError("复制图层提交失败")
    _add_to_project(new_layer)
    return _result(f"已复制当前图层为新图层 {new_layer.name()}", layer=_summary(new_layer))


def tool_rename_layer(new_name: str) -> dict:
    layer = _current()
    name = str(new_name).strip()
    if not name:
        raise RuntimeError("图层名称不能为空")
    layer.setName(name)
    return _result(f"当前图层已重命名为 {name}")


def tool_remove_layer() -> dict:
    layer = STATE.get("layer")
    if layer is None or not layer.isValid():
        raise RuntimeError("当前没有图层，无需移除")
    layer_id = layer.id()
    STATE["layer"] = None
    QgsProject.instance().removeMapLayer(layer_id)
    return _result("已从工程移除当前图层")


def tool_get_crs() -> dict:
    layer = _current()
    return {"status": "ok", "crs": _crs_str(layer), "message": f"当前图层 CRS: {_crs_str(layer)}"}


def tool_field_statistics(column: str) -> dict:
    layer = _current()
    if column not in _field_names(layer):
        raise RuntimeError(f"列不存在: {column}（可用列: {_field_names(layer)}）")
    numbers = []
    missing = 0
    for feature in layer.getFeatures():
        value = feature[column]
        if value is None:
            missing += 1
            continue
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            missing += 1
    if not numbers:
        raise RuntimeError(f"列 {column} 没有可统计的数值")
    count = len(numbers)
    mean = sum(numbers) / count
    variance = sum((x - mean) ** 2 for x in numbers) / count
    return {
        "status": "ok",
        "column": column,
        "count": count,
        "mean": round(mean, 6),
        "std": round(variance**0.5, 6),
        "min": min(numbers),
        "max": max(numbers),
        "missing": missing,
    }


def tool_unique_values(column: str) -> dict:
    layer = _current()
    if column not in _field_names(layer):
        raise RuntimeError(f"列不存在: {column}（可用列: {_field_names(layer)}）")
    values = sorted(
        {str(feature[column]) for feature in layer.getFeatures() if feature[column] is not None}
    )
    truncated = len(values) > 50
    return {
        "status": "ok",
        "column": column,
        "count": len(values),
        "values": values[:50],
        "truncated": truncated,
    }


_HANDLERS = {
    "load_data": tool_load_data,
    "inspect_data": tool_inspect_data,
    "buffer": tool_buffer,
    "start_editing": tool_start_editing,
    "add_features": tool_add_features,
    "update_features": tool_update_features,
    "delete_features": tool_delete_features,
    "calculate_field": tool_calculate_field,
    "commit_edits": tool_commit_edits,
    "rollback_edits": tool_rollback_edits,
    "export_geojson": tool_export_geojson,
    "duplicate_layer": tool_duplicate_layer,
    "rename_layer": tool_rename_layer,
    "remove_layer": tool_remove_layer,
    "get_crs": tool_get_crs,
    "field_statistics": tool_field_statistics,
    "unique_values": tool_unique_values,
}


def invoke(payload: dict) -> dict:
    """执行一次工具调用（必须在 QGIS GUI 主线程）。"""
    tool = payload.get("tool")
    handler = _HANDLERS.get(tool)
    if handler is None:
        raise RuntimeError(f"插件尚未支持工具 {tool}（M2b 首批: {sorted(_HANDLERS)})")
    STATE["out_dir"] = payload.get("out_dir")
    return handler(**(payload.get("args") or {}))
