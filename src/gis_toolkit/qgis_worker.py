"""QGIS 引擎 worker — 由 QGIS 自带 Python（python-qgis-ltr.bat）运行。

与主进程通过 stdin/stdout JSON-lines 通信：
    请求: {"op": "call"|"ping"|"exit", "tool": "...", "args": {...}}
    响应: {"ok": true, "result": {...}} | {"ok": false, "error": "..."}

本进程只维护「当前图层 + 输出目录」两类状态；产物文件名与输入路径
安全校验由主进程负责（白名单/文件名净化），worker 只做 GIS 运算。
"""

from __future__ import annotations

import io
import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtCore import QSize, QVariant
from PyQt5.QtGui import QColor, QImage
from qgis import processing
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import (
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsClassificationEqualInterval,
    QgsClassificationJenks,
    QgsClassificationQuantile,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsFillSymbol,
    QgsGeometry,
    QgsGraduatedSymbolRenderer,
    QgsMapRendererParallelJob,
    QgsMapSettings,
    QgsPalLayerSettings,
    QgsProject,
    QgsRasterLayer,
    QgsRendererCategory,
    QgsTextFormat,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
    QgsVectorLayerUtils,
    QgsWkbTypes,
)

DEFAULT_CRS = "EPSG:4326"
_LON_COLS = ("lon", "lng", "longitude", "经度", "x")
_LAT_COLS = ("lat", "latitude", "纬度", "y")
_NORM_SUFFIXES = (
    "壮族自治区",
    "维吾尔自治区",
    "回族自治区",
    "特别行政区",
    "自治区",
    "省",
    "市",
)
_OVERLAY_ALGS = {
    "intersection": "native:intersection",
    "union": "native:union",
    "difference": "native:difference",
    "symmetric_difference": "native:symmetricaldifference",
}
_SCHEME_CLASS = {
    "NaturalBreaks": QgsClassificationJenks,
    "Quantiles": QgsClassificationQuantile,
    "EqualInterval": QgsClassificationEqualInterval,
}

_TAB20_HEX = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5",
]

STATE: dict = {}


# ── 初始化 ──

def _find_prefix() -> str:
    """定位 QGIS 前缀目录（含 python/qgis/core 的 apps/qgis-ltr）"""
    candidates = [os.environ.get("QGIS_PREFIX_PATH", "")]
    candidates += [
        r"D:\QGIS\apps\qgis-ltr",
        r"C:\Program Files\QGIS 3.40.10\apps\qgis-ltr",
    ]
    for c in candidates:
        if c and os.path.isdir(os.path.join(c, "python", "qgis", "core")):
            return c
    raise RuntimeError("未找到 QGIS 前缀目录（QGIS_PREFIX_PATH 未设置）")


def _init(out_dir: str) -> None:
    prefix = _find_prefix()
    QgsApplication.setPrefixPath(prefix, True)
    app = QgsApplication([], False)
    app.initQgis()
    STATE["app"] = app  # keep a reference to avoid GC breaking the render thread
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    sys.path.append(os.path.join(prefix, "python", "plugins"))
    from processing.core.Processing import Processing

    Processing.initialize()
    STATE["layer"] = None
    STATE["out_dir"] = os.path.abspath(out_dir)
    STATE["base_map"] = None
    base_path = os.path.join(os.getcwd(), "data", "gis_base", "china_province.geojson")
    if os.path.isfile(base_path):
        base = QgsVectorLayer(base_path, "base", "ogr")
        if base.isValid():
            STATE["base_map"] = base


# ── 通用小工具 ──

def _pick_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    cols = {str(c).lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return str(cols[cand.lower()])
    return None


def _province_norm(name: str) -> str:
    name = str(name).strip()
    for suffix in _NORM_SUFFIXES:
        name = name.replace(suffix, "")
    return name


def _jsonable(v):
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if v is None or isinstance(v, (str, bool)):
        return v
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            return None
        return v
    return str(v)


def _crs_str(layer: QgsVectorLayer) -> str:
    crs = layer.crs()
    return crs.authid() or crs.toWkt()


def _field_names(layer: QgsVectorLayer) -> list[str]:
    return [f.name() for f in layer.fields()]


def _require_layer() -> QgsVectorLayer:
    layer = STATE.get("layer")
    if layer is None:
        raise RuntimeError("当前没有图层，请先 load_data")
    return layer


def _result(message: str, **extra) -> dict:
    data: dict = {"status": "ok", "message": message}
    if STATE.get("layer") is not None:
        data["layer"] = _summary(STATE["layer"])
    data.update(extra)
    return data


def _geometry_type(layer: QgsVectorLayer) -> str:
    """Display geometry type name (aligned with geopandas geom_type)."""
    wkb = layer.wkbType()
    if int(wkb) == 0:  # WkbType.Unknown
        for _ in layer.getFeatures():
            pass
        wkb = layer.wkbType()
    return QgsWkbTypes.displayString(wkb)


def _summary(layer: QgsVectorLayer) -> dict:
    return {
        "rows": int(layer.featureCount()),
        "columns": _field_names(layer),
        "crs": _crs_str(layer),
        "geometry_type": _geometry_type(layer),
    }


def _new_memory_layer(name: str, geom_type: str, crs: str, fields: QgsFields | None = None) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"{geom_type}?crs={crs}", name, "memory")
    if fields is not None:
        layer.dataProvider().addAttributes(fields)
        layer.updateFields()
    return layer


def _load_layer(path: str) -> QgsVectorLayer:
    """按后缀加载图层：CSV → delimitedtext 点层；其余 → ogr"""
    name = os.path.splitext(os.path.basename(path))[0]
    if path.lower().endswith(".csv"):
        head = pd.read_csv(path, nrows=5)
        x_col = _pick_col(head, _LON_COLS)
        y_col = _pick_col(head, _LAT_COLS)
        if not (x_col and y_col):
            raise RuntimeError(
                f"CSV 缺少经纬度列（可用列: {list(head.columns)}），无法转成空间数据"
            )
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


# ── 工具实现 ──

def tool_load_data(path: str) -> dict:
    layer = _load_layer(path)
    STATE["layer"] = layer
    return _result(f"已加载 {os.path.basename(path)}，{layer.featureCount()} 行")


def tool_inspect_data() -> dict:
    layer = _require_layer()
    info = _summary(layer)
    ext = layer.extent()
    bounds = [ext.xMinimum(), ext.yMinimum(), ext.xMaximum(), ext.yMaximum()]
    samples: list[dict] = []
    for i, feat in enumerate(layer.getFeatures()):
        if i >= 5:
            break
        samples.append({f.name(): _jsonable(feat.attribute(f.name())) for f in layer.fields()})
    return {
        "status": "ok",
        "message": f"图层 {layer.featureCount()} 行，CRS: {_crs_str(layer)}",
        **info,
        "bounds": bounds,
        "sample_rows": samples,
    }


def tool_buffer(distance: float) -> dict:
    layer = _require_layer()
    out = _new_memory_layer(
        layer.name() + "_buffer", "MultiPolygon", _crs_str(layer), layer.fields()
    )
    out.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            continue
        new_geom = geom.buffer(float(distance), 16)
        new_geom.convertToMultiType()
        f = QgsFeature(out.fields())
        f.setGeometry(new_geom)
        f.setAttributes(feat.attributes())
        out.addFeature(f)
    out.commitChanges()
    STATE["layer"] = out
    return _result(f"已生成 {distance} 单位缓冲区（CRS: {_crs_str(out)}，单位以坐标系为准）")


def tool_overlay(other_path: str, how: str = "intersection") -> dict:
    layer = _require_layer()
    if how not in _OVERLAY_ALGS:
        raise RuntimeError(
            f"overlay 的 how 必须是 intersection/union/difference/symmetric_difference，收到: {how}"
        )
    other = _load_layer(other_path)
    if _crs_str(layer) != _crs_str(other):
        raise RuntimeError(
            f"两个图层 CRS 不一致（{_crs_str(layer)} vs {_crs_str(other)}），先统一坐标系"
        )
    params = {"INPUT": layer, "OVERLAY": other, "OUTPUT": "memory:"}
    result = processing.run(_OVERLAY_ALGS[how], params)
    out_layer = result["OUTPUT"]
    STATE["layer"] = out_layer
    return _result(f"overlay({how}) 完成，结果 {out_layer.featureCount()} 行")


def tool_choropleth(
    column: str,
    scheme: str = "NaturalBreaks",
    k: int = 5,
    output: str = "choropleth.png",
) -> dict:
    layer = _require_layer()
    if column not in _field_names(layer):
        raise RuntimeError(f"列不存在: {column}（可用列: {_field_names(layer)}）")
    if scheme not in _SCHEME_CLASS:
        raise RuntimeError(f"scheme 必须是 NaturalBreaks/Quantiles/EqualInterval，收到: {scheme}")

    target, note = _prepare_choropleth_layer(layer, column)
    ranges = _apply_graduated(target, column, scheme, int(k))

    map_pil = _qimage_to_pil(_render_map(target))
    legend_img = _render_legend(ranges, column)
    combined = Image.new(
        "RGB", (map_pil.width + legend_img.width, map_pil.height), "white"
    )
    combined.paste(map_pil, (0, 0))
    combined.paste(legend_img, (map_pil.width, 0))
    out_path = os.path.join(STATE["out_dir"], output)
    combined.save(out_path)
    return _result(
        f"已保存分级设色图 {output}{note}",
        size_bytes=os.path.getsize(out_path),
        classes=[[r.lowerValue(), r.upperValue()] for r in ranges],
    )


def _prepare_choropleth_layer(layer: QgsVectorLayer, column: str):
    """点数据优先聚合到省界底图；否则直接用当前图层"""
    note = ""
    is_points = layer.geometryType() == QgsWkbTypes.PointGeometry
    base = STATE.get("base_map")
    if is_points and base is not None:
        if "province" in _field_names(layer) and "name" in _field_names(base):
            agg_layer = _aggregate_to_province(layer, base, column)
            note = "（按省份聚合省界底图）"
            return agg_layer, note
        note = "（省界底图 + 点分级着色）"
        # 底图与点一起渲染：这里返回 (点层, 底图) 特殊组合
        return (layer, base), note
    return layer, note


def _aggregate_to_province(points: QgsVectorLayer, base: QgsVectorLayer, column: str) -> QgsVectorLayer:
    """点层按 province 字段聚合后，把聚合值 join 到省界底图"""
    rows = [
        {f.name(): feat.attribute(f.name()) for f in points.fields()}
        for feat in points.getFeatures()
    ]
    df = pd.DataFrame(rows)
    if column not in df.columns:
        raise RuntimeError(f"列不存在: {column}")
    agg = df.groupby("province")[column].agg("sum").reset_index()
    agg["_norm"] = agg["province"].map(_province_norm)
    val_map = dict(zip(agg["_norm"], agg[column], strict=False))

    fields = QgsFields()
    fields.append(QgsField("name", QVariant.String))
    fields.append(QgsField(column, QVariant.Double))
    out = _new_memory_layer("province_agg", "MultiPolygon", _crs_str(base), fields)
    out.startEditing()
    for feat in base.getFeatures():
        norm = _province_norm(feat.attribute("name"))
        if norm not in val_map:
            continue
        f = QgsFeature(out.fields())
        f.setGeometry(feat.geometry())
        f.setAttributes([feat.attribute("name"), float(val_map[norm])])
        out.addFeature(f)
    out.commitChanges()
    return out


def _apply_graduated(layer: QgsVectorLayer, column: str, scheme: str, k: int):
    renderer = QgsGraduatedSymbolRenderer()
    renderer.setClassAttribute(column)
    renderer.setClassificationMethod(_SCHEME_CLASS[scheme]())
    renderer.updateClasses(layer, k)
    layer.setRenderer(renderer)
    return renderer.ranges()


def _render_map(layers) -> QImage:
    if isinstance(layers, tuple):
        base, points = layers
        render_layers = [base, points]
        extent = points.extent().united(base.extent())
    else:
        render_layers = [layers]
        extent = layers.extent()
    settings = QgsMapSettings()
    settings.setLayers(render_layers)
    settings.setExtent(extent)
    settings.setOutputSize(QSize(1400, 1000))
    settings.setBackgroundColor(QColor("white"))
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    return job.renderedImage()


def _qimage_to_pil(qimg) -> Image.Image:
    """Convert a PyQt5 QImage to a PIL Image in memory."""
    from PyQt5.QtCore import QBuffer, QIODevice

    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    qimg.save(buf, "PNG")
    data = bytes(buf.data())
    buf.close()
    return Image.open(io.BytesIO(data)).convert("RGB")


def _render_legend(ranges, title: str) -> Image.Image:
    """Draw a graduated legend (color bands, values, title) with PIL."""
    band_w, label_w = 56, 200
    band_h = 36
    pad = 44
    legend_h = pad + band_h * len(ranges)
    img = Image.new("RGB", (band_w + label_w, legend_h), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
    font_small = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 12)
    draw.text((0, 4), title, fill=(30, 30, 30), font=font)
    for i, r in enumerate(ranges):
        color = r.symbol().color()
        fill = (color.red(), color.green(), color.blue())
        y0 = pad + i * band_h
        draw.rectangle([0, y0, band_w, y0 + band_h - 2], fill=fill, outline=(120, 120, 120))
        lower = r.lowerValue()
        upper = r.upperValue()
        if i == 0:
            label = f"<= {upper:g}"
        elif i == len(ranges) - 1:
            label = f"> {lower:g}"
        else:
            label = f"{lower:g} - {upper:g}"
        draw.text((band_w + 12, y0 + band_h // 2 - 9), label, fill=(30, 30, 30), font=font_small)
    return img


def tool_scatter_plot(x: str, y: str, output: str = "scatter.png") -> dict:
    layer = _require_layer()
    for col in (x, y):
        if col not in _field_names(layer):
            raise RuntimeError(f"列不存在: {col}（可用列: {_field_names(layer)}）")
    xs, ys = [], []
    for feat in layer.getFeatures():
        try:
            xs.append(float(feat.attribute(x)))
            ys.append(float(feat.attribute(y)))
        except (TypeError, ValueError):
            raise RuntimeError(f"列 {x}/{y} 不是数值类型，无法画散点图") from None
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(xs, ys, s=18, alpha=0.7)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"{x} vs {y}")
    fig.tight_layout()
    out_path = os.path.join(STATE["out_dir"], output)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return _result(f"已保存散点图 {output}", size_bytes=os.path.getsize(out_path))


def tool_summarize(
    column: str,
    groupby: str | None = None,
    agg: str = "sum",
    output: str = "summary.csv",
    sort_by: str | None = None,
    desc: bool = False,
) -> dict:
    layer = _require_layer()
    if column not in _field_names(layer):
        raise RuntimeError(f"列不存在: {column}（可用列: {_field_names(layer)}）")
    if agg not in {"sum", "mean", "count", "min", "max"}:
        raise RuntimeError(f"agg 必须是 sum/mean/count/min/max，收到: {agg}")
    rows = [
        {f.name(): feat.attribute(f.name()) for f in layer.fields()}
        for feat in layer.getFeatures()
    ]
    df = pd.DataFrame(rows)
    if groupby:
        if groupby not in df.columns:
            raise RuntimeError(f"分组列不存在: {groupby}（可用列: {list(df.columns)}）")
        out_df = df.groupby(groupby)[column].agg(agg).reset_index()
    else:
        out_df = pd.DataFrame({column: [getattr(df[column], agg)()]})
    sort_col = sort_by or groupby or column
    if sort_col in out_df.columns:
        out_df = out_df.sort_values(sort_col, ascending=not desc)
    out_path = os.path.join(STATE["out_dir"], output)
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return _result(
        f"已保存统计结果 {output}（{len(out_df)} 行，agg={agg}）",
        summary_rows=int(len(out_df)),
    )


def tool_export_geojson(output: str = "layer.geojson") -> dict:
    layer = _require_layer()
    out_path = os.path.join(STATE["out_dir"], output)
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GeoJSON"
    options.fileEncoding = "utf-8"
    err, _, _, msg = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, out_path, QgsCoordinateTransformContext(), options
    )
    if err != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"导出 GeoJSON 失败: {err} {msg}")
    return _result(f"已导出 {output}", size_bytes=os.path.getsize(out_path))


def tool_save_layer(path: str) -> dict:
    """会话快照：把当前图层写到指定绝对路径（主进程已校验安全）"""
    layer = _require_layer()
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GeoJSON"
    options.fileEncoding = "utf-8"
    err, _, _, msg = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, path, QgsCoordinateTransformContext(), options
    )
    if err != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"快照导出失败: {err} {msg}")
    return {"ok": True}


def tool_join_by_location(other_path: str, predicate: str = "intersects") -> dict:
    layer = _require_layer()
    other = _load_layer(other_path)
    # native:joinattributesbylocation 的 PREDICATE 数字定义（QGIS 3.40 实测）
    # 0 intersect / 1 contain / 2 equal / 3 touch / 4 overlap / 5 are within / 6 cross
    pred_map = {"intersects": 0, "within": 5, "contains": 1}
    if predicate not in pred_map:
        raise RuntimeError(f"predicate 必须是 intersects/within/contains，收到: {predicate}")
    result = processing.run(
        "native:joinattributesbylocation",
        {
            "INPUT": layer,
            "JOIN": other,
            "PREDICATE": [pred_map[predicate]],
            "METHOD": 0,
            "DISCARD_NONMATCHING": True,
            "OUTPUT": "memory:",
        },
    )["OUTPUT"]
    if not result.isValid():
        raise RuntimeError("空间连接失败：结果图层无效")
    STATE["layer"] = result
    return _result(
        f"空间连接完成（predicate={predicate}），结果 {result.featureCount()} 行"
    )


def tool_voronoi() -> dict:
    layer = _require_layer()
    result = processing.run(
        "native:voronoipolygons",
        {"INPUT": layer, "BUFFER": 0.0, "OUTPUT": "memory:"},
    )["OUTPUT"]
    if not result.isValid():
        raise RuntimeError("泰森多边形生成失败：结果图层无效")
    STATE["layer"] = result
    return _result(f"已生成 {result.featureCount()} 个泰森多边形")


def tool_get_crs() -> dict:
    layer = _require_layer()
    crs = layer.crs()
    return {
        "status": "ok",
        "crs": crs.authid() or crs.toWkt(),
        "epsg": crs.postgisSrid() if crs.isValid() else None,
        "description": crs.description() if crs.isValid() else None,
    }


def tool_set_crs(crs: str) -> dict:
    layer = _require_layer()
    new_crs = QgsCoordinateReferenceSystem(crs)
    if not new_crs.isValid():
        raise RuntimeError(f"无效坐标系: {crs!r}（示例 EPSG:4326 / EPSG:3857）")
    layer.setCrs(new_crs)
    return _result(f"已设置坐标系为 {new_crs.authid() or new_crs.toWkt()}")


def tool_list_layers() -> dict:
    layer = STATE.get("layer")
    return {
        "status": "ok",
        "has_layer": layer is not None,
        "layer": _summary(layer) if layer is not None else None,
        "out_dir": STATE.get("out_dir"),
    }


def tool_field_statistics(column: str) -> dict:
    layer = _require_layer()
    if column not in _field_names(layer):
        raise RuntimeError(f"列不存在: {column}（可用列: {_field_names(layer)}）")
    nums: list[float] = []
    missing = 0
    for feat in layer.getFeatures():
        v = feat[column]
        if v is None:
            missing += 1
            continue
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            missing += 1
    if not nums:
        raise RuntimeError(f"列 {column} 没有可统计的数值")
    n = len(nums)
    mean = sum(nums) / n
    var = sum((x - mean) ** 2 for x in nums) / n
    return {
        "status": "ok",
        "column": column,
        "count": n,
        "mean": round(mean, 6),
        "std": round(var**0.5, 6),
        "min": min(nums),
        "max": max(nums),
        "missing": missing,
    }


def tool_unique_values(column: str) -> dict:
    layer = _require_layer()
    if column not in _field_names(layer):
        raise RuntimeError(f"列不存在: {column}（可用列: {_field_names(layer)}）")
    values = sorted(
        {str(f[column]) for f in layer.getFeatures() if f[column] is not None}
    )
    truncated = len(values) > 50
    return {
        "status": "ok",
        "column": column,
        "count": len(values),
        "values": values[:50],
        "truncated": truncated,
    }


def tool_transform_coords(target_crs: str) -> dict:
    layer = _require_layer()
    new_crs = QgsCoordinateReferenceSystem(target_crs)
    if not new_crs.isValid():
        raise RuntimeError(
            f"无效坐标系: {target_crs!r}（示例 EPSG:3857 / EPSG:32650）"
        )
    result = processing.run(
        "native:reprojectlayer",
        {"INPUT": layer, "TARGET_CRS": new_crs, "OUTPUT": "memory:"},
    )["OUTPUT"]
    if not result.isValid():
        raise RuntimeError("重投影失败：结果图层无效")
    STATE["layer"] = result
    return _result(f"已重投影到 {new_crs.authid() or new_crs.toWkt()}")


def tool_render_map(output: str = "map.png") -> dict:
    layer = _require_layer()
    out_path = os.path.join(STATE["out_dir"], output)
    settings = QgsMapSettings()
    settings.setLayers([layer])
    settings.setExtent(layer.extent())
    settings.setOutputSize(QSize(1000, 800))
    settings.setBackgroundColor(QColor(255, 255, 255))
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    image = job.renderedImage()
    if not image.save(out_path, "PNG"):
        raise RuntimeError(f"渲染保存失败: {out_path}")
    return _result(
        f"已保存地图 {output}", size_bytes=os.path.getsize(out_path)
    )


def tool_run_algorithm(algorithm: str, params: dict | None = None) -> dict:
    layer = _require_layer()
    params = params or {}
    alg_map = {
        "dissolve": ("native:dissolve", "dissolve"),
        "centroids": ("native:centroids", "centroids"),
        "convexhull": ("native:convexhull", "convexhull"),
    }
    if algorithm not in alg_map:
        raise RuntimeError(
            f"未知算法: {algorithm}（白名单: dissolve/centroids/convexhull）"
        )
    alg_id, label = alg_map[algorithm]
    if algorithm == "dissolve":
        field = params.get("field")
        if not field or field not in _field_names(layer):
            raise RuntimeError(
                f"dissolve 需要有效的 field 参数（可用列: {_field_names(layer)}）"
            )
        alg_params = {"INPUT": layer, "FIELD": [field], "OUTPUT": "memory:"}
    else:
        alg_params = {"INPUT": layer, "OUTPUT": "memory:"}
    result = processing.run(alg_id, alg_params)["OUTPUT"]
    if not result.isValid():
        raise RuntimeError(f"{label} 失败：结果图层无效")
    STATE["layer"] = result
    return _result(f"{label} 完成，结果 {result.featureCount()} 行")


def tool_load_raster(path: str) -> dict:
    layer = QgsRasterLayer(path, os.path.basename(path), "gdal")
    if not layer.isValid():
        raise RuntimeError(f"无法加载栅格 {path}（需 TIFF/GeoTIFF）")
    STATE["raster"] = layer
    crs = layer.crs()
    ext = layer.extent()
    return {
        "status": "ok",
        "message": f"已加载栅格 {os.path.basename(path)}",
        "raster": {
            "width": int(layer.width()),
            "height": int(layer.height()),
            "bands": int(layer.bandCount()),
            "crs": crs.authid() or crs.toWkt(),
            "bounds": [
                ext.xMinimum(),
                ext.yMinimum(),
                ext.xMaximum(),
                ext.yMaximum(),
            ],
            "path": os.path.abspath(path),
        },
    }


# ── 编辑会话（Gate 6：HITL 审批联动）───────────────

def _require_editing() -> QgsVectorLayer:
    layer = _require_layer()
    if not layer.isEditable():
        raise RuntimeError("未开始编辑，请先 start_editing")
    return layer


def tool_start_editing() -> dict:
    layer = _require_layer()
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
    feat = QgsFeature(layer.fields())
    feat.setGeometry(g)
    for key, value in (attributes or {}).items():
        idx = layer.fields().indexOf(key)
        if idx >= 0:
            feat.setAttribute(idx, value)
    if not layer.addFeature(feat):
        raise RuntimeError("新增要素失败")
    return _result("已新增 1 个要素（待 commit）")


def tool_update_features(where: str, attributes: dict) -> dict:
    layer = _require_editing()
    expr = QgsExpression(where)
    if expr.hasParserError():
        raise RuntimeError(f"条件表达式无效: {expr.parserErrorString()}")
    ctx = QgsExpressionContext()
    ctx.appendScope(QgsExpressionContextUtils.layerScope(layer))
    n = 0
    for feat in layer.getFeatures():
        ctx.setFeature(feat)
        if not expr.evaluate(ctx):
            continue
        for key, value in (attributes or {}).items():
            idx = layer.fields().indexOf(key)
            if idx < 0:
                raise RuntimeError(f"列不存在: {key}（可用列: {_field_names(layer)}）")
            layer.changeAttributeValue(feat.id(), idx, value)
        n += 1
    return _result(f"已更新 {n} 个要素（待 commit）")


def tool_update_geometry(feature_id: int, geometry: str) -> dict:
    layer = _require_editing()
    g = QgsGeometry.fromWkt(geometry)
    if g.isNull():
        raise RuntimeError(f"无效 WKT 几何: {geometry}")
    fids = [f.id() for f in layer.getFeatures()]
    if feature_id < 0 or feature_id >= len(fids):
        raise RuntimeError(f"要素行号越界: {feature_id}（共 {len(fids)} 行）")
    if not layer.changeGeometry(fids[feature_id], g):
        raise RuntimeError("修改几何失败")
    return _result(f"已更新要素 #{feature_id} 几何（待 commit）")


def tool_delete_features(ids: list) -> dict:
    layer = _require_editing()
    fids = [f.id() for f in layer.getFeatures()]
    drop = [fids[int(i)] for i in ids if 0 <= int(i) < len(fids)]
    if not drop:
        raise RuntimeError("所有行号越界或 ids 为空")
    if not layer.deleteFeatures(drop):
        raise RuntimeError("删除要素失败")
    return _result(f"已删除 {len(drop)} 个要素（待 commit）")


def tool_commit_edits() -> dict:
    layer = _require_layer()
    if not layer.isEditable():
        raise RuntimeError("未开始编辑，请先 start_editing")
    if not layer.commitChanges():
        layer.rollBack()
        raise RuntimeError("提交失败，已回滚")
    return _result("已提交编辑，修改已生效")


def tool_rollback_edits() -> dict:
    layer = _require_layer()
    if not layer.isEditable():
        raise RuntimeError("未开始编辑，请先 start_editing")
    layer.rollBack()
    return _result("已回滚编辑，修改已丢弃")


def tool_duplicate_layer() -> dict:
    layer = _require_layer()
    new_layer = QgsVectorLayerUtils.duplicateLayer(layer, layer.name() + "_copy")
    if not new_layer or not new_layer.isValid():
        raise RuntimeError("复制图层失败")
    STATE["layer"] = new_layer
    return _result("已复制当前图层")


def tool_categorized(column: str, output: str = "categorized.png") -> dict:
    layer = _require_layer()
    if column not in _field_names(layer):
        raise RuntimeError(f"列不存在: {column}（可用列: {_field_names(layer)}）")
    values = sorted(
        {str(f[column]) for f in layer.getFeatures() if f[column] is not None}
    )
    if not values:
        raise RuntimeError(f"列 {column} 没有有效分类值")
    renderer = QgsCategorizedSymbolRenderer(column, [])
    for i, v in enumerate(values):
        sym = QgsFillSymbol.createSimple(
            {
                "color": _TAB20_HEX[i % len(_TAB20_HEX)],
                "outline_color": "#666666",
                "outline_width": "0.3",
            }
        )
        renderer.addCategory(QgsRendererCategory(v, sym, v))
    layer.setRenderer(renderer)
    image = _render_map(layer)
    out_path = os.path.join(STATE["out_dir"], output)
    if not image.save(out_path, "PNG"):
        raise RuntimeError(f"保存分类设色图失败: {out_path}")
    return _result(
        f"已保存分类设色图 {output}（{len(values)} 个类别）",
        size_bytes=os.path.getsize(out_path),
        classes=len(values),
    )


def tool_set_labeling(label_field: str, enabled: bool = True) -> dict:
    layer = _require_layer()
    if label_field not in _field_names(layer):
        raise RuntimeError(
            f"列不存在: {label_field}（可用列: {_field_names(layer)}）"
        )
    if enabled:
        settings = QgsPalLayerSettings()
        settings.fieldName = label_field
        settings.setFormat(QgsTextFormat())
        settings.enabled = True
        layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
        layer.setLabelsEnabled(True)
    else:
        layer.setLabelsEnabled(False)
    return _result(f"已{'启用' if enabled else '关闭'}标注（字段 {label_field}）")


def tool_get_project_info() -> dict:
    layer = STATE.get("layer")
    layer_info = _summary(layer) if layer is not None else None
    raster = STATE.get("raster")
    raster_info = None
    if raster is not None:
        ext = raster.extent()
        crs = raster.crs()
        raster_info = {
            "width": int(raster.width()),
            "height": int(raster.height()),
            "bands": int(raster.bandCount()),
            "crs": crs.authid() or crs.toWkt(),
            "bounds": [
                ext.xMinimum(),
                ext.yMinimum(),
                ext.xMaximum(),
                ext.yMaximum(),
            ],
        }
    return {
        "status": "ok",
        "engine": "qgis",
        "layer": layer_info,
        "raster": raster_info,
        "out_dir": STATE.get("out_dir"),
    }


def tool_save_project(path: str = "gis_project.qgz") -> dict:
    project = QgsProject.instance()
    project.removeAllMapLayers()
    layer = STATE.get("layer")
    if layer is not None:
        project.addMapLayer(layer)
    raster = STATE.get("raster")
    if raster is not None:
        project.addMapLayer(raster)
    if not project.write(path):
        raise RuntimeError(f"保存工程失败: {path}")
    return _result(f"已保存工程 {os.path.basename(path)}")


HANDLERS = {
    "load_data": tool_load_data,
    "inspect_data": tool_inspect_data,
    "buffer": tool_buffer,
    "overlay": tool_overlay,
    "choropleth": tool_choropleth,
    "scatter_plot": tool_scatter_plot,
    "summarize": tool_summarize,
    "export_geojson": tool_export_geojson,
    "save_layer": tool_save_layer,
    "join_by_location": tool_join_by_location,
    "voronoi": tool_voronoi,
    "get_crs": tool_get_crs,
    "set_crs": tool_set_crs,
    "list_layers": tool_list_layers,
    "field_statistics": tool_field_statistics,
    "unique_values": tool_unique_values,
    "transform_coords": tool_transform_coords,
    "render_map": tool_render_map,
    "run_algorithm": tool_run_algorithm,
    "load_raster": tool_load_raster,
    "start_editing": tool_start_editing,
    "add_features": tool_add_features,
    "update_features": tool_update_features,
    "update_geometry": tool_update_geometry,
    "delete_features": tool_delete_features,
    "commit_edits": tool_commit_edits,
    "rollback_edits": tool_rollback_edits,
    "duplicate_layer": tool_duplicate_layer,
    "categorized": tool_categorized,
    "set_labeling": tool_set_labeling,
    "get_project_info": tool_get_project_info,
    "save_project": tool_save_project,
}


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: qgis_worker.py <out_dir>\n")
        return 2
    _init(sys.argv[1])
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"ok": False, "error": "非法请求"}, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue
        op = req.get("op")
        if op == "exit":
            break
        if op == "ping":
            resp = {"ok": True, "result": {"pong": True}}
        elif op == "call":
            handler = HANDLERS.get(req.get("tool"))
            if handler is None:
                resp = {"ok": False, "error": f"未知工具: {req.get('tool')}"}
            else:
                try:
                    result = handler(**(req.get("args") or {}))
                    resp = {"ok": True, "result": result}
                except Exception as exc:  # 工具异常回传主进程，不让 worker 崩溃
                    resp = {"ok": False, "error": str(exc)}
        else:
            resp = {"ok": False, "error": f"未知操作: {op}"}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
