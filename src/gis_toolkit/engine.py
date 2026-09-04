"""GIS 引擎 — 基于 GeoPandas 的实现（工具接口面向未来 PyQGIS 对接抽象）

每个工具返回可 JSON 序列化的摘要 dict；产物（图/CSV/GeoJSON）写入引擎输出目录。
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import matplotlib
import requests

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False

DEFAULT_CRS = "EPSG:4326"
MAX_FILE_BYTES = 10 * 1024 * 1024
_LON_COLS = ("lon", "lng", "longitude", "经度", "x")
_LAT_COLS = ("lat", "latitude", "纬度", "y")
_SAFE_NAME = re.compile(r"^[\w.\-]+$")


def _pick_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    """按候选名（忽略大小写）找列；找不到返回 None"""
    cols = {str(c).lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return str(cols[cand.lower()])
    return None


def _sanitize_filename(name: str) -> str:
    """产物文件名净化：拒绝空、绝对路径、路径穿越、非法字符"""
    if not name or not _SAFE_NAME.match(name):
        raise GisEngineError(f"非法产物文件名: {name!r}（只允许字母/数字/._-，禁止路径）")
    return name


def _jsonable(obj):
    """????? JSON ??????shapely?WKT?numpy ???????????str"""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_jsonable(v) for v in obj]
    if obj is None or isinstance(obj, str | int | float | bool):
        return obj
    if hasattr(obj, "wkt"):  # shapely ??
        return obj.wkt
    if hasattr(obj, "item"):  # numpy ??
        return obj.item()
    if hasattr(obj, "tolist"):  # numpy ??
        return obj.tolist()
    return str(obj)


# 3D 演示静态目录（后端启动时同步 frontend/3d-demo → src/web/static/3d-demo 并挂载 /3d-demo）
_3D_STATIC_DIR = Path("src/web/static/3d-demo")
_OSM_DATA_DIR = Path("data/gis_3d")
_OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
_OVERPASS_HEADERS = {
    "User-Agent": "gis-3d-demo/0.1 (educational demo)",
    "Accept": "application/json",
}


def _estimate_height(tags: dict) -> float:
    """OSM 建筑高度估算：height 优先 → building:levels×3 → 按类型默认（演示用，非测绘）"""
    raw = tags.get("height")
    if raw:
        m = re.match(r"\s*([\d.]+)", str(raw))
        if m:
            return float(m.group(1))
    lv = tags.get("building:levels")
    if lv:
        m = re.match(r"\s*([\d.]+)", str(lv))
        if m:
            return float(m.group(1)) * 3.0
    building = (tags.get("building") or "").lower()
    if building in ("garage", "carport"):
        return 4.0
    if building in ("shed", "greenhouse", "roof"):
        return 3.0
    return 10.0


def _apply_height_field(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """为 3D 预览补齐 height_m 字段：已有 height_m/height 直接用，levels×3，否则默认 10"""
    out = gdf.copy()
    cols = {str(c).lower(): c for c in out.columns}
    values: list[float] = []
    for _, row in out.iterrows():
        h: float | None = None
        src = None
        if "height_m" in cols:
            src = cols["height_m"]
        elif "height" in cols:
            src = cols["height"]
        if src is not None and pd.notna(row.get(src)) and str(row[src]).strip():
            m = re.match(r"\s*([\d.]+)", str(row[src]))
            if m:
                h = float(m.group(1))
        if h is None and "building:levels" in cols:
            lv = cols["building:levels"]
            if pd.notna(row.get(lv)) and str(row[lv]).strip():
                m = re.match(r"\s*([\d.]+)", str(row[lv]))
                if m:
                    h = float(m.group(1)) * 3.0
        values.append(h if h is not None else 10.0)
    out["height_m"] = values
    return out


def _check_input_path(path: str, roots: list[Path]) -> Path:
    """校验输入路径：必须在白名单内、存在、且 ≤10MB"""
    resolved = Path(path).resolve()
    if not any(resolved == root or root in resolved.parents for root in roots):
        raise GisEngineError(f"拒绝访问白名单外的文件: {path}")
    if not resolved.is_file():
        raise GisEngineError(f"文件不存在: {path}")
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise GisEngineError(f"文件超过 {MAX_FILE_BYTES // 1024 // 1024}MB 限制: {path}")
    return resolved


class GisEngineError(RuntimeError):
    """GIS 工具执行失败（错误消息会回传给 LLM，供其修正）"""


class GisEngine:
    """单会话 GIS 引擎：当前图层 + 产物清单 + 输出目录"""

    def __init__(
        self,
        data_file: str | None = None,
        out_dir: str = "data/gis_toolkit_out",
        allowed_roots: list[str] | None = None,
    ) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        # 输入白名单：默认只允许项目 data/ 目录（设计文档 7 节）
        self._roots = [Path(r).resolve() for r in (allowed_roots or ["data"])]
        self.outputs: list[str] = []
        self._layer: gpd.GeoDataFrame | None = None
        self._layer_name: str | None = None  # 当前图层名称（load_data 时取文件名）
        self._editing: gpd.GeoDataFrame | None = None  # 编辑会话缓冲区
        self._raster: str | None = None  # 当前栅格文件路径（栅格状态与矢量状态并存）
        self._label_field: str | None = None  # 标注字段（Gate 7）
        self._basemap: dict | None = None  # 底图状态（Gate 8：local 栅格 / xyz / wms 配置）
        self._base_map: gpd.GeoDataFrame | None = self._load_base_map()
        if data_file:
            self.load_data(data_file)

    # ── 底图 / 名称归一化 ──
    def _load_base_map(self) -> gpd.GeoDataFrame | None:
        """加载内置中国省界底图（data/gis_base/china_province.geojson），失败返回 None"""
        base_path = Path("data/gis_base/china_province.geojson")
        if not base_path.is_file():
            return None
        try:
            gdf = gpd.read_file(base_path)
            return gdf if "name" in gdf.columns else None
        except Exception:
            return None

    @staticmethod
    def _province_norm(name: str) -> str:
        """省级名称归一化：'北京市' → '北京'、'内蒙古自治区' → '内蒙古'"""
        name = name.strip()
        for suffix in (
            "壮族自治区",
            "维吾尔自治区",
            "回族自治区",
            "特别行政区",
            "自治区",
            "省",
            "市",
        ):
            name = name.replace(suffix, "")
        return name

    # ── 内部工具 ──
    def _check_input(self, path: str) -> Path:
        """??????????????????? ?10MB"""
        return _check_input_path(path, self._roots)

    def _summary(self, gdf: gpd.GeoDataFrame) -> dict:
        geom_col = gdf.geometry.name
        return {
            "name": self._layer_name,
            "rows": int(len(gdf)),
            "columns": [str(c) for c in gdf.columns if c != geom_col],
            "crs": gdf.crs.to_string() if gdf.crs else None,
            "geometry_type": (
                gdf.geometry.geom_type.mode().iloc[0]
                if len(gdf) and gdf.geometry.notna().any()
                else None
            ),
        }

    def _result(self, message: str, **extra) -> dict:
        data: dict = {"status": "ok", "message": message}
        if self._layer is not None:
            data["layer"] = self._summary(self._layer)
        data["outputs"] = list(self.outputs)
        data["output_paths"] = self._output_paths()
        data.update(extra)
        return data

    def _output_paths(self) -> list[str]:
        """产物绝对路径（文件名 → out_dir 下的完整路径），供 LLM/用户直接定位"""
        return [str((self.out_dir / o).resolve()) for o in self.outputs]

    def _load_any(self, path: str) -> gpd.GeoDataFrame:
        """加载任意文件为 GeoDataFrame（CSV 按经纬度列转点）"""
        resolved = self._check_input(path)
        if resolved.suffix.lower() == ".csv":
            df = pd.read_csv(resolved)
            x_col = _pick_col(df, _LON_COLS)
            y_col = _pick_col(df, _LAT_COLS)
            if not (x_col and y_col):
                raise GisEngineError(
                    f"CSV 缺少经纬度列（可用列: {list(df.columns)}），无法转成空间数据"
                )
            gdf = gpd.GeoDataFrame(
                df, geometry=gpd.points_from_xy(df[x_col], df[y_col]), crs=DEFAULT_CRS
            )
        else:
            gdf = gpd.read_file(resolved)
            if gdf.crs is None:
                gdf = gdf.set_crs(DEFAULT_CRS)
        return gdf

    # ── 工具实现（名称与设计文档 schema 对齐，未来换 PyQGIS 保持签名不变）──
    def load_data(self, path: str) -> dict:
        """加载数据文件为当前图层（CSV 需含经纬度列；GeoJSON/zip 直接读取）"""
        gdf = self._load_any(path)
        self._layer = gdf
        self._layer_name = Path(path).stem
        return self._result(
            f"已加载 {Path(path).name}，{len(gdf)} 行", stats={"rows": int(len(gdf))}
        )

    def rename_layer(self, new_name: str) -> dict:
        """重命名当前图层（仅改名称元数据，不影响底层数据文件）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        new_name = str(new_name).strip()
        if not new_name:
            raise GisEngineError("图层名称不能为空")
        self._layer_name = new_name
        return self._result(f"当前图层已重命名为 {new_name}")

    def remove_layer(self) -> dict:
        """移除当前图层（丢弃其引用与编辑会话缓冲区）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，无需移除")
        self._layer = None
        self._layer_name = None
        self._editing = None
        return self._result("已移除当前图层")

    def export_layer_inventory(self, output: str = "layer_inventory.json") -> dict:
        """导出当前图层清单到 JSON 文件（名称/行数/字段/CRS/几何类型/范围/产物）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        gdf = self._layer
        bounds = gdf.total_bounds.tolist() if len(gdf) else None
        inventory = {
            "name": self._layer_name,
            "rows": int(len(gdf)),
            "columns": [str(c) for c in gdf.columns if c != gdf.geometry.name],
            "crs": gdf.crs.to_string() if gdf.crs else None,
            "geometry_type": (
                gdf.geometry.geom_type.mode().iloc[0]
                if len(gdf) and gdf.geometry.notna().any()
                else None
            ),
            "bounds": bounds,
            "outputs": list(self.outputs),
            "exported_at": datetime.now().isoformat(timespec="seconds"),
        }
        fname = Path(output).name  # 只取文件名，防路径穿越
        if not fname.endswith(".json"):
            fname = f"{fname}.json"
        fpath = self.out_dir / fname
        fpath.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
        self.outputs.append(fname)
        return self._result(
            f"图层清单已导出到 {fname}", inventory_file=fname, inventory_name=self._layer_name
        )

    def inspect_data(self) -> dict:
        """查看当前图层：字段、行数、CRS、范围、样例行"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        gdf = self._layer
        info = self._summary(gdf)
        bounds = gdf.total_bounds.tolist() if len(gdf) else None
        non_geom = (
            gdf.drop(columns=[gdf.geometry.name]) if gdf.geometry.name in gdf.columns else gdf
        )
        sample = _jsonable(non_geom.head(5).to_dict(orient="records"))
        return {
            "status": "ok",
            "message": f"???? {len(gdf)} ??CRS: {gdf.crs}",
            **info,
            "bounds": bounds,
            "sample_rows": sample,
            "stats": {
                "rows": int(len(gdf)),
                "columns": info.get("columns") or [],
                "crs": str(gdf.crs) if gdf.crs else None,
                "geometry_type": info.get("geometry_type"),
                "bounds": bounds,
            },
        }

    def buffer(self, distance: float) -> dict:
        """对当前图层所有要素做缓冲区（distance 单位以当前 CRS 为准）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        gdf = self._layer.copy()
        gdf.geometry = gdf.geometry.buffer(distance)
        self._layer = gdf
        stats = {
            "distance": float(distance),
            "features": int(len(gdf)),
            "geometry_type": str(gdf.geometry.geom_type.mode().iloc[0]) if len(gdf) else None,
            "crs": str(gdf.crs) if gdf.crs else None,
        }
        return self._result(
            f"已生成 {distance} 单位缓冲区（CRS: {self._layer.crs}，单位以坐标系为准）",
            stats=stats,
        )

    def overlay(self, other_path: str, how: str = "intersection") -> dict:
        """与另一图层做空间叠加（intersection/union/difference/symmetric_difference）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if how not in {"intersection", "union", "difference", "symmetric_difference"}:
            raise GisEngineError(
                f"overlay 的 how 必须是 intersection/union/difference/symmetric_difference，收到: {how}"
            )
        other = self._load_any(other_path)
        if self._layer.crs != other.crs:
            raise GisEngineError(
                f"两个图层 CRS 不一致（{self._layer.crs} vs {other.crs}），先统一坐标系"
            )
        result = gpd.overlay(self._layer, other, how=how)
        self._layer = result
        return self._result(f"overlay({how}) 完成，结果 {len(result)} 行")

    def choropleth(
        self,
        column: str,
        scheme: str = "NaturalBreaks",
        k: int = 5,
        output: str = "choropleth.png",
    ) -> dict:
        """对数值列做分级设色图并保存 PNG（scheme: NaturalBreaks/Quantiles/EqualInterval）

        点数据 + 内置中国省界底图时：优先按省份聚合为省面地图；
        无省份列则底图叠加点着色；面数据直接分级设色。
        """
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if column not in self._layer.columns:
            raise GisEngineError(f"列不存在: {column}（可用列: {list(self._layer.columns)}）")
        out = self.out_dir / _sanitize_filename(output)
        fig, ax = plt.subplots(figsize=(10, 8))
        note = ""
        aggregated = False
        missing_provinces: list[str] = []
        try:
            layer = self._layer
            is_points = bool(len(layer)) and bool(layer.geometry.geom_type.eq("Point").all())
            if (
                is_points
                and self._base_map is not None
                and "name" in self._base_map.columns
                and "province" in layer.columns
            ):
                # 按省聚合：省界底图 merge 点数据的省聚合值 → 省面分级设色
                agg = (
                    layer.drop(columns=[layer.geometry.name])
                    .groupby("province")[column]
                    .agg("sum")
                    .reset_index()
                )
                agg["_province_norm"] = agg["province"].map(self._province_norm)
                base = self._base_map.copy()
                base["_province_norm"] = base["name"].map(self._province_norm)
                merged = base.merge(agg, on="_province_norm", how="left")
                missing = sorted(merged.loc[merged[column].isna(), "name"].tolist())
                merged.plot(
                    column=column,
                    scheme=scheme,
                    k=int(k),
                    cmap="YlOrRd",
                    legend=True,
                    ax=ax,
                    missing_kwds={"color": "#e6ddd0", "edgecolor": "#9a9082", "linewidth": 0.5},
                    legend_kwds={
                        "title": column,
                        "loc": "lower right",
                        "fontsize": 8,
                        "title_fontsize": 9,
                    },
                )
                aggregated = True
                missing_provinces = list(missing)
                missing_note = "、".join(missing[:10]) + (" 等" if len(missing) > 10 else "")
                note = f"（按省份聚合省界底图，{len(missing)} 个无数据省份：{missing_note}）"
            elif is_points and self._base_map is not None:
                # 底图 + 点叠加着色
                self._base_map.plot(ax=ax, color="#f0e9dd", edgecolor="#9a9082", linewidth=0.5)
                layer.plot(
                    column=column,
                    scheme=scheme,
                    k=int(k),
                    cmap="YlOrRd",
                    legend=True,
                    ax=ax,
                    markersize=42,
                    legend_kwds={
                        "title": column,
                        "loc": "lower right",
                        "fontsize": 8,
                        "title_fontsize": 9,
                    },
                )
                note = "（省界底图 + 点分级着色）"
            else:
                layer.plot(
                    column=column,
                    scheme=scheme,
                    k=int(k),
                    cmap="YlOrRd",
                    legend=True,
                    ax=ax,
                    legend_kwds={
                        "title": column,
                        "loc": "lower right",
                        "fontsize": 8,
                        "title_fontsize": 9,
                    },
                )
        except Exception as exc:
            plt.close(fig)
            raise GisEngineError(f"分级设色失败（检查 scheme/k 或列是否为数值）: {exc}") from exc
        ax.set_title(f"{column} 分级设色 ({scheme}, k={k}){note}")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.outputs.append(output)
        size_bytes = int(out.stat().st_size)
        stats = {
            "output": output,
            "size_bytes": size_bytes,
            "scheme": scheme,
            "k": int(k),
            "aggregated": aggregated,
            "missing_provinces": missing_provinces,
        }
        return self._result(f"已保存分级设色图 {output}{note}", size_bytes=size_bytes, stats=stats)

    def scatter_plot(self, x: str, y: str, output: str = "scatter.png") -> dict:
        """两个数值列的散点图"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        for col in (x, y):
            if col not in self._layer.columns:
                raise GisEngineError(f"列不存在: {col}（可用列: {list(self._layer.columns)}）")
        out = self.out_dir / _sanitize_filename(output)
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.scatter(self._layer[x], self._layer[y], s=18, alpha=0.7)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(f"{x} vs {y}")
        fig.tight_layout()
        fig.savefig(out, dpi=150)
        plt.close(fig)
        self.outputs.append(output)
        size_bytes = int(out.stat().st_size)
        return self._result(
            f"已保存散点图 {output}",
            size_bytes=size_bytes,
            stats={"output": output, "x": x, "y": y, "size_bytes": size_bytes},
        )

    def summarize(
        self,
        column: str,
        groupby: str | None = None,
        agg: str = "sum",
        output: str = "summary.csv",
        sort_by: str | None = None,
        desc: bool = False,
    ) -> dict:
        """对数值列聚合统计（可选按 groupby 列分组），导出 CSV；可按结果列排序"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if column not in self._layer.columns:
            raise GisEngineError(f"列不存在: {column}（可用列: {list(self._layer.columns)}）")
        if agg not in {"sum", "mean", "count", "min", "max"}:
            raise GisEngineError(f"agg 必须是 sum/mean/count/min/max，收到: {agg}")
        df = self._layer.drop(columns=[self._layer.geometry.name])
        stats: dict = {"rows": int(len(df)), "group_count": 1}
        if groupby:
            if groupby not in df.columns:
                raise GisEngineError(f"分组列不存在: {groupby}（可用列: {list(df.columns)}）")
            out_df = df.groupby(groupby)[column].agg(agg).reset_index()
            stats["group_count"] = int(len(out_df))
        else:
            out_df = pd.DataFrame({column: [getattr(df[column], agg)()]})
        # stats：可核对关键数字（来自真实计算结果，供结果审核 L1 使用，禁止 LLM 生成）
        value_col = column if column in out_df.columns else out_df.columns[-1]
        if agg in {"sum", "mean"}:
            stats["total"] = _jsonable(getattr(df[column], agg)())
        elif agg == "count":
            stats["total"] = int(df[column].count())
        if len(out_df) and value_col in out_df.columns:
            top = (
                out_df.nlargest(3, value_col)
                if str(out_df[value_col].dtype).startswith(("float", "int", "Int", "Float"))
                else out_df.head(3)
            )
            stats["top3"] = [
                {"k": str(r[groupby] if groupby else r[value_col]), "v": _jsonable(r[value_col])}
                for _, r in top.iterrows()
            ]
        else:
            stats["top3"] = []
        sort_col = sort_by or groupby or column
        if sort_col in out_df.columns:
            out_df = out_df.sort_values(sort_col, ascending=not desc)
        out = self.out_dir / _sanitize_filename(output)
        out_df.to_csv(out, index=False, encoding="utf-8-sig")
        self.outputs.append(output)
        return self._result(
            f"已保存统计结果 {output}（{len(out_df)} 行，agg={agg}）",
            summary_rows=int(len(out_df)),
            stats=stats,
        )

    def export_geojson(self, output: str = "layer.geojson") -> dict:
        """把当前图层导出为 GeoJSON"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        out = self.out_dir / _sanitize_filename(output)
        self._layer.to_file(out, driver="GeoJSON")
        self.outputs.append(output)
        size_bytes = int(out.stat().st_size)
        return self._result(
            f"已导出 {output}",
            size_bytes=size_bytes,
            stats={"output": output, "size_bytes": size_bytes, "features": int(len(self._layer))},
        )

    def join_by_location(self, other_path: str, predicate: str = "intersects") -> dict:
        """把另一图层按空间关系并入当前图层（结果成为新的当前图层）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if predicate not in {"intersects", "within", "contains"}:
            raise GisEngineError(f"predicate 必须是 intersects/within/contains，收到: {predicate}")
        other = self._load_any(other_path)
        if self._layer.crs != other.crs:
            raise GisEngineError(
                f"两个图层 CRS 不一致（{self._layer.crs} vs {other.crs}），先统一坐标系"
            )
        result = gpd.sjoin(self._layer, other, how="inner", predicate=predicate)
        self._layer = result
        return self._result(f"空间连接完成（predicate={predicate}），结果 {len(result)} 行")

    def join_by_attribute(
        self,
        other_path: str,
        left_key: str,
        right_key: str,
        how: str = "inner",
    ) -> dict:
        """把 CSV/表按关键字段属性连接到当前图层（结果成为新的当前图层）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if how not in {"inner", "left"}:
            raise GisEngineError(f"how 必须是 inner/left，收到: {how}")
        resolved = self._check_input(other_path)
        if resolved.suffix.lower() == ".csv":
            other = pd.read_csv(resolved)
        else:
            gdf = gpd.read_file(resolved)
            other = (
                gdf.drop(columns=[gdf.geometry.name]) if gdf.geometry.name in gdf.columns else gdf
            )
        if left_key not in self._layer.columns:
            raise GisEngineError(
                f"当前图层缺少连接字段 {left_key}（可用: {list(self._layer.columns)}）"
            )
        if right_key not in other.columns:
            raise GisEngineError(f"关联表缺少连接字段 {right_key}（可用: {list(other.columns)}）")
        result = self._layer.merge(other, left_on=left_key, right_on=right_key, how=how)
        geom_col = result.geometry.name
        if geom_col not in result.columns or result[geom_col].isna().all():
            raise GisEngineError("属性连接失败：结果缺少有效几何列")
        self._layer = result
        return self._result(
            f"属性连接完成（{left_key} = {right_key}, how={how}），结果 {len(result)} 行"
        )

    def voronoi(self) -> dict:
        """对当前点图层生成泰森多边形（结果成为新的当前图层）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        layer = self._layer
        if not len(layer) or not layer.geometry.geom_type.eq("Point").all():
            raise GisEngineError("voronoi 只支持点图层（当前不是纯点数据）")
        try:
            import shapely
            from shapely.ops import voronoi_diagram

            pts = layer.geometry.union_all()
            minx, miny, maxx, maxy = layer.total_bounds
            envelope = shapely.geometry.box(minx, miny, maxx, maxy)
            polys = voronoi_diagram(pts, envelope=envelope)
            result = gpd.GeoDataFrame(geometry=list(polys.geoms), crs=layer.crs)
        except Exception as exc:
            raise GisEngineError(f"生成泰森多边形失败: {exc}") from exc
        self._layer = result
        return self._result(f"已生成 {len(result)} 个泰森多边形")

    def get_crs(self) -> dict:
        """查看当前图层坐标系"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        crs = self._layer.crs
        return {
            "status": "ok",
            "crs": crs.to_string() if crs else None,
            "epsg": crs.to_epsg() if crs else None,
            "description": crs.name if crs else None,
        }

    def set_crs(self, crs: str) -> dict:
        """重设当前图层坐标系（只改声明，不重投影）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        try:
            import pyproj

            new_crs = pyproj.CRS.from_user_input(crs)
        except Exception as exc:
            raise GisEngineError(f"无效坐标系: {crs!r}（示例 EPSG:4326 / EPSG:3857）") from exc
        self._layer = self._layer.set_crs(new_crs, allow_override=True)
        return self._result(f"已设置坐标系为 {new_crs}")

    def list_layers(self) -> dict:
        """查看当前会话状态快照"""
        return {
            "status": "ok",
            "has_layer": self._layer is not None,
            "layer": self._summary(self._layer) if self._layer is not None else None,
            "outputs": list(self.outputs),
            "output_paths": self._output_paths(),
            "out_dir": str(self.out_dir.resolve()),
        }

    def field_statistics(self, column: str) -> dict:
        """对数值列做字段统计"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if column not in self._layer.columns:
            raise GisEngineError(f"列不存在: {column}（可用列: {list(self._layer.columns)}）")
        col = pd.to_numeric(self._layer[column], errors="coerce")
        if col.dropna().empty:
            raise GisEngineError(f"列 {column} 没有可统计的数值（检查是否为数值列）")
        desc = col.describe()
        return {
            "status": "ok",
            "column": column,
            "count": int(desc["count"]),
            "mean": _jsonable(desc["mean"]),
            "std": _jsonable(desc["std"]),
            "min": _jsonable(desc["min"]),
            "max": _jsonable(desc["max"]),
            "missing": int(col.isna().sum()),
            "stats": {
                "count": int(desc["count"]),
                "min": _jsonable(desc["min"]),
                "max": _jsonable(desc["max"]),
                "mean": _jsonable(desc["mean"]),
                "std": _jsonable(desc["std"]),
                "median": _jsonable(desc["50%"]),
                "sum": _jsonable(float(col.sum())),
            },
        }

    def unique_values(self, column: str) -> dict:
        """查看某列唯一取值（最多 50 个）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if column not in self._layer.columns:
            raise GisEngineError(f"列不存在: {column}（可用列: {list(self._layer.columns)}）")
        values = [str(v) for v in self._layer[column].dropna().unique().tolist()]
        truncated = len(values) > 50
        return {
            "status": "ok",
            "column": column,
            "count": len(values),
            "values": values[:50],
            "truncated": truncated,
            "stats": {"count": len(values)},
        }

    def transform_coords(self, target_crs: str) -> dict:
        """把当前图层重投影到目标坐标系"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        try:
            import pyproj

            new_crs = pyproj.CRS.from_user_input(target_crs)
        except Exception as exc:
            raise GisEngineError(
                f"无效坐标系: {target_crs!r}（示例 EPSG:3857 / EPSG:32650）"
            ) from exc
        try:
            self._layer = self._layer.to_crs(new_crs)
        except Exception as exc:
            raise GisEngineError(f"重投影失败: {exc}") from exc
        return self._result(f"已重投影到 {new_crs}")

    def render_map(self, output: str = "map.png") -> dict:
        """把当前图层渲染成 PNG（面淡色填充、点/线着色）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        out = self.out_dir / _sanitize_filename(output)
        fig, ax = plt.subplots(figsize=(10, 8))
        layer = self._layer
        geom_type = layer.geometry.geom_type.mode().iloc[0] if len(layer) else ""
        self._draw_basemap(ax)
        try:
            if geom_type.startswith("Point"):
                layer.plot(ax=ax, color="#e6550d", markersize=18, alpha=0.8)
            elif geom_type.startswith("Line"):
                layer.plot(ax=ax, color="#3182bd", linewidth=1.2)
            else:
                layer.plot(ax=ax, color="#c6dbef", edgecolor="#3182bd", linewidth=0.5)
        except Exception as exc:
            plt.close(fig)
            raise GisEngineError(f"渲染地图失败: {exc}") from exc
        if self._label_field:
            self._draw_labels(ax, layer)
        ax.set_title("当前图层")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.outputs.append(output)
        return self._result(f"已保存地图 {output}", size_bytes=out.stat().st_size)

    # ── 3D 城市可视化（P3）──────────────────
    def download_osm_buildings(
        self,
        city: str,
        south: float,
        west: float,
        north: float,
        east: float,
    ) -> dict:
        """按 bbox 从 Overpass 下载建筑轮廓，估算高度，存 data/gis_3d/<city>_buildings.geojson"""
        if north <= south or east <= west:
            raise GisEngineError("bbox 无效：要求 north>south、east>west")
        query = (
            f'[out:json][timeout:60];(way["building"]({south},{west},{north},{east}););out geom;'
        )
        try:
            resp = requests.post(
                _OVERPASS_ENDPOINT,
                data={"data": query},
                headers=_OVERPASS_HEADERS,
                timeout=60,
            )
        except requests.RequestException as exc:
            raise GisEngineError(f"请求 Overpass 失败: {exc}") from exc
        if resp.status_code != 200:
            raise GisEngineError(f"Overpass 返回 HTTP {resp.status_code}")
        payload = resp.json()
        features: list[dict] = []
        height_direct = levels_used = default_used = 0
        for el in payload.get("elements", []):
            if el.get("type") != "way":
                continue
            ring = [(p["lon"], p["lat"]) for p in (el.get("geometry") or [])]
            if len(ring) < 3:
                continue
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            tags = el.get("tags") or {}
            if tags.get("height"):
                height_direct += 1
            elif tags.get("building:levels"):
                levels_used += 1
            else:
                default_used += 1
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "osm_id": el["id"],
                        "building": tags.get("building"),
                        "height_m": _estimate_height(tags),
                    },
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                }
            )
        if not features:
            raise GisEngineError("该范围内没有建筑要素，请调整 bbox")
        fc = {"type": "FeatureCollection", "features": features}
        out_dir = _OSM_DATA_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{_sanitize_filename(city)}_buildings.geojson"
        out_path = out_dir / fname
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(fc, fh, ensure_ascii=False)
        return {
            "status": "ok",
            "message": f"已下载 {len(features)} 栋建筑 → {out_path.resolve()}",
            "outputs": list(self.outputs),
            "output_paths": self._output_paths(),
            "file_path": str(out_path.resolve()),
            "stats": {
                "total": len(features),
                "height_direct": height_direct,
                "levels_used": levels_used,
                "default_used": default_used,
            },
            "note": "建筑高度为估算值，仅用于可视化演示，非测绘数据（© OpenStreetMap contributors, ODbL）",
        }

    def render_3d(self, output: str = "render_3d") -> dict:
        """把当前图层导出为 3D 预览 GeoJSON（补齐 height_m），挂载 /3d-demo/ 并返回 URL"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        out = self._apply_height_3d()
        dst = _3D_STATIC_DIR / f"{_sanitize_filename(output)}.geojson"
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False)
        url = f"http://localhost:8080/3d-demo/?data={dst.name}"
        return {
            "status": "ok",
            "message": f"已生成 3D 预览 → {url}",
            "outputs": list(self.outputs) + [dst.name],
            "output_paths": self._output_paths() + [str(dst.resolve())],
            "3d_preview_url": url,
            "note": "建筑高度为估算值，仅用于可视化演示，非测绘数据",
        }

    def _apply_height_3d(self) -> dict:
        """把当前图层（含估算 height_m）转成 GeoJSON dict"""
        gdf = _apply_height_field(self._layer)
        return json.loads(gdf.to_json())

    # ── 底图叠加 / 排版要素（Gate 8）──────────────
    def _draw_basemap(self, ax) -> None:
        """把已加载底图叠加到坐标轴上（local 栅格用真实范围 imshow；xyz/wms 在线瓦片跳过）"""
        if not self._basemap:
            return
        try:
            if self._basemap.get("kind") == "local":
                import rasterio

                bpath = self._basemap["path"]
                with rasterio.open(bpath) as src:
                    window = src.read([1, 2, 3], out_dtype="uint8") if src.count >= 3 else None
                if window is None:
                    return

                ext = self._basemap["extent"]
                ax.imshow(
                    window.transpose(1, 2, 0),
                    extent=ext,
                    origin="upper",
                    interpolation="bilinear",
                    zorder=0,
                )
        except Exception:
            # 底图叠加失败不阻塞主体渲染
            pass

    @staticmethod
    def _draw_scalebar(ax, layer) -> None:
        """在左下角绘制比例尺条（按图层范围估算地面距离，仅用于可视化）"""
        try:
            bounds = layer.total_bounds  # minx, miny, maxx, maxy
            span_x = bounds[2] - bounds[0]
            # 地理坐标按 1°≈111km 折算为米；投影坐标视为米
            crs_str = str(layer.crs or "")
            is_geo = "4326" in crs_str or crs_str.lower().startswith("epsg:4")
            meters_per_unit = 111320.0 if is_geo else 1.0
            total_m = span_x * meters_per_unit
            if total_m <= 0:
                return
            # 选取合适比例尺长度（1/2/5 系列）
            target = total_m / 4
            import math

            mag = 10 ** math.floor(math.log10(max(target, 1)))
            scale_len = mag * round(target / mag)
            if scale_len < mag:
                scale_len = mag
            x0 = bounds[0] + span_x * 0.06
            y0 = bounds[1] + (bounds[3] - bounds[1]) * 0.06
            # 横向像素宽度按数据坐标折算
            x1 = x0 + scale_len / meters_per_unit
            ax.plot([x0, x1], [y0, y0], color="k", linewidth=2)
            ax.plot([x0, x0], [y0 - span_x * 0.004, y0 + span_x * 0.004], color="k", linewidth=2)
            ax.plot([x1, x1], [y0 - span_x * 0.004, y0 + span_x * 0.004], color="k", linewidth=2)
            label = f"{scale_len / 1000:g} km" if scale_len >= 1000 else f"{scale_len:g} m"
            ax.text((x0 + x1) / 2, y0 - span_x * 0.012, label, ha="center", fontsize=7)
        except Exception:
            pass

    @staticmethod
    def _draw_north_arrow(ax) -> None:
        """在右上角绘制指北针（向上箭头 + N 标注）"""
        try:
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            cx = xlim[1] - (xlim[1] - xlim[0]) * 0.06
            cy = ylim[1] - (ylim[1] - ylim[0]) * 0.1
            r = (xlim[1] - xlim[0]) * 0.03
            ax.annotate(
                "",
                xy=(cx, cy + r * 1.5),
                xytext=(cx, cy - r * 0.5),
                arrowprops=dict(arrowstyle="->", color="k", lw=1.6),
            )
            ax.text(cx, cy + r * 1.9, "N", ha="center", va="center", fontsize=10, fontweight="bold")
        except Exception:
            pass

    def layout_map(
        self,
        title: str = "地图排版",
        legend_column: str | None = None,
        show_legend: bool = True,
        show_scalebar: bool = True,
        show_north_arrow: bool = True,
        output: str = "layout_map.png",
    ) -> dict:
        """地图排版出图：标题 + 图例 + 比例尺 + 指北针（matplotlib 版，QGIS 引擎走 QgsLayout）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        out = self.out_dir / _sanitize_filename(output)
        layer = self._layer
        geom_type = layer.geometry.geom_type.mode().iloc[0] if len(layer) else ""
        fig, ax = plt.subplots(figsize=(12, 9))
        self._draw_basemap(ax)
        try:
            if legend_column:
                if legend_column not in layer.columns:
                    raise GisEngineError(
                        f"图例字段不存在: {legend_column}（可用列: {list(layer.columns)}）"
                    )
                import matplotlib.cm as cm

                cats = sorted({str(v) for v in layer[legend_column].dropna().unique()})
                if not cats:
                    raise GisEngineError(f"字段 {legend_column} 没有有效分类值")
                cat_to_color = {c: cm.tab20(i % 20) for i, c in enumerate(cats)}
                colors = layer[legend_column].astype(str).map(cat_to_color)
                layer.plot(ax=ax, color=colors, edgecolor="#666666", linewidth=0.5, zorder=2)
                if show_legend:
                    handles = [
                        plt.Line2D(
                            [0],
                            [0],
                            marker="s",
                            color="w",
                            markerfacecolor=cat_to_color[c],
                            markersize=8,
                            label=c,
                        )
                        for c in cats
                    ]
                    ax.legend(
                        handles=handles,
                        loc="lower left",
                        fontsize=8,
                        title=legend_column,
                        framealpha=0.9,
                    )
            else:
                if geom_type.startswith("Point"):
                    layer.plot(ax=ax, color="#e6550d", markersize=18, alpha=0.8, zorder=2)
                elif geom_type.startswith("Line"):
                    layer.plot(ax=ax, color="#3182bd", linewidth=1.2, zorder=2)
                else:
                    layer.plot(ax=ax, color="#c6dbef", edgecolor="#3182bd", linewidth=0.5, zorder=2)
            if self._label_field:
                self._draw_labels(ax, layer)
            if show_scalebar:
                self._draw_scalebar(ax, layer)
            if show_north_arrow:
                self._draw_north_arrow(ax)
        except GisEngineError:
            plt.close(fig)
            raise
        except Exception as exc:
            plt.close(fig)
            raise GisEngineError(f"排版出图失败: {exc}") from exc
        ax.set_title(title, fontsize=14)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.outputs.append(output)
        return self._result(f"已保存排版图 {output}", size_bytes=out.stat().st_size)

    def load_basemap(self, source: str = "xyz", url: str = "", name: str = "底图") -> dict:
        """加载底图：local=本地栅格（叠加渲染）/ xyz / wms（记录配置，QGIS 引擎下叠加）"""
        if source == "local":
            resolved = self._check_input(url)
            try:
                import rasterio

                with rasterio.open(resolved) as src:
                    bounds = [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top]
                    crs = str(src.crs) if src.crs else None
            except GisEngineError:
                raise
            except Exception as exc:
                raise GisEngineError(f"加载本地底图失败（需 GeoTIFF）: {exc}") from exc
            self._basemap = {
                "kind": "local",
                "path": str(resolved.resolve()),
                "extent": bounds,
                "crs": crs,
                "name": name or "底图",
            }
            return self._result(
                f"已加载本地底图 {Path(url).name}（范围 {bounds}，CRS {crs}）",
                basemap=self._basemap,
            )
        if source in ("xyz", "wms"):
            if not url:
                raise GisEngineError(f"{source.upper()} 底图需要 url 参数")
            self._basemap = {"kind": source, "url": url, "name": name or "底图"}
            note = "在线底图在 geopandas 引擎下仅记录配置，QGIS 引擎下渲染时自动叠加"
            return self._result(
                f"已记录 {source.upper()} 底图配置「{name or '底图'}」",
                basemap=self._basemap,
                note=note,
            )
        raise GisEngineError(f"未知底图来源: {source}（可选 xyz / wms / local）")

    def categorized(self, column: str, output: str = "categorized.png") -> dict:
        """对分类列做分类设色图（每个类别一种颜色）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if column not in self._layer.columns:
            raise GisEngineError(f"列不存在: {column}（可用列: {list(self._layer.columns)}）")
        out = self.out_dir / _sanitize_filename(output)
        import matplotlib.cm as cm

        layer = self._layer
        cats = sorted({str(v) for v in layer[column].dropna().unique()})
        if not cats:
            raise GisEngineError(f"列 {column} 没有有效分类值")
        cat_to_color = {c: cm.tab20(i % 20) for i, c in enumerate(cats)}
        colors = layer[column].astype(str).map(cat_to_color)
        fig, ax = plt.subplots(figsize=(10, 8))
        try:
            layer.plot(ax=ax, color=colors, edgecolor="#666666", linewidth=0.5)
            handles = [
                plt.Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="w",
                    markerfacecolor=cat_to_color[c],
                    markersize=8,
                    label=c,
                )
                for c in cats
            ]
            ax.legend(handles=handles, loc="lower right", fontsize=8)
        except Exception as exc:
            plt.close(fig)
            raise GisEngineError(f"分类设色失败: {exc}") from exc
        if self._label_field:
            self._draw_labels(ax, layer)
        ax.set_title(f"{column} 分类设色")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.outputs.append(output)
        return self._result(
            f"已保存分类设色图 {output}（{len(cats)} 个类别）",
            size_bytes=out.stat().st_size,
            classes=len(cats),
            stats={
                "output": output,
                "classes": len(cats),
                "class_values": cats[:20],
                "size_bytes": int(out.stat().st_size),
            },
        )

    def set_labeling(self, label_field: str, enabled: bool = True) -> dict:
        """设置当前图层标注字段（出图时显示）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if label_field not in self._layer.columns:
            raise GisEngineError(f"列不存在: {label_field}（可用列: {list(self._layer.columns)}）")
        self._label_field = label_field if enabled else None
        return self._result(f"已{'启用' if enabled else '关闭'}标注（字段 {label_field}）")

    def _draw_labels(self, ax, layer) -> None:
        """在图上绘制标注（点/面质心处显示 label_field 值）"""
        if not self._label_field or self._label_field not in layer.columns:
            return
        geom_type = layer.geometry.geom_type.mode().iloc[0] if len(layer) else ""
        if geom_type.startswith("Point"):
            xs, ys = layer.geometry.x, layer.geometry.y
        else:
            xs, ys = layer.geometry.centroid.x, layer.geometry.centroid.y
        for x, y, label in zip(xs, ys, layer[self._label_field].astype(str), strict=False):
            ax.annotate(label, (x, y), fontsize=6, ha="center", va="center")

    def run_algorithm(self, algorithm: str, params: dict | None = None) -> dict:
        """运行白名单空间算法（结果成为新的当前图层）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        params = params or {}
        layer = self._layer
        if algorithm == "dissolve":
            field = params.get("field")
            if not field or field not in layer.columns:
                raise GisEngineError(
                    f"dissolve 需要有效的 field 参数（可用列: {list(layer.columns)}）"
                )
            result = layer.dissolve(by=field)
            message = f"dissolve（按 {field}）完成，结果 {len(result)} 行"
        elif algorithm == "centroids":
            result = layer.copy()
            result.geometry = layer.geometry.centroid
            message = f"已生成 {len(result)} 个要素质心"
        elif algorithm == "convexhull":
            result = layer.copy()
            result.geometry = layer.geometry.convex_hull
            message = f"已生成 {len(result)} 个要素凸包"
        else:
            raise GisEngineError(f"未知算法: {algorithm}（白名单: dissolve/centroids/convexhull）")
        self._layer = result
        return self._result(message)

    def load_raster(self, path: str) -> dict:
        """加载栅格文件（TIFF / GeoTIFF）为当前栅格，返回元数据"""
        resolved = self._check_input(path)
        try:
            import rasterio

            with rasterio.open(resolved) as src:
                self._raster = str(resolved.resolve())
                return {
                    "status": "ok",
                    "message": f"已加载栅格 {Path(path).name}",
                    "raster": {
                        "width": int(src.width),
                        "height": int(src.height),
                        "bands": int(src.count),
                        "dtype": src.dtypes[0],
                        "crs": str(src.crs) if src.crs else None,
                        "bounds": [
                            src.bounds.left,
                            src.bounds.bottom,
                            src.bounds.right,
                            src.bounds.top,
                        ],
                        "path": str(resolved.resolve()),
                    },
                }
        except GisEngineError:
            raise
        except Exception as exc:
            raise GisEngineError(f"加载栅格失败（需 TIFF/GeoTIFF）: {exc}") from exc

    # ── 编辑会话（Gate 6：HITL 审批联动）──────────────
    def start_editing(self) -> dict:
        """开始编辑会话：复制当前图层到缓冲区"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if self._editing is not None:
            raise GisEngineError("已在编辑会话中，先 commit_edits 或 rollback_edits")
        self._editing = self._layer.copy()
        return self._result(
            "已开始编辑会话（修改在 commit 前不生效）",
            stats={"rows": int(len(self._editing)), "editing": True},
        )

    def _require_editing(self) -> gpd.GeoDataFrame:
        if self._editing is None:
            raise GisEngineError("未开始编辑，请先 start_editing")
        return self._editing

    def add_features(self, geometry: str, attributes: dict | None = None) -> dict:
        """编辑会话中新增要素（WKT 几何 + 可选属性）"""
        editing = self._require_editing()
        try:
            from shapely import wkt as shapely_wkt

            geom = shapely_wkt.loads(geometry)
        except Exception as exc:
            raise GisEngineError(f"无效 WKT 几何: {exc}") from exc
        attrs = dict(attributes or {})
        new_row = gpd.GeoDataFrame([attrs], geometry=[geom], crs=editing.crs)
        self._editing = pd.concat([editing, new_row], ignore_index=True)
        return self._result(
            "已新增 1 个要素（待 commit）",
            stats={"added": 1, "rows": int(len(self._editing))},
        )

    def update_features(self, where: str, attributes: dict) -> dict:
        """编辑会话中按条件更新属性"""
        editing = self._require_editing()
        try:
            mask = editing.eval(where)
        except Exception as exc:
            raise GisEngineError(f"条件表达式无效: {exc}") from exc
        n = int(mask.sum())
        if n == 0:
            return self._result("没有要素满足条件，未做修改", stats={"updated": 0, "rows": int(len(editing))})
        for key, value in (attributes or {}).items():
            if key not in editing.columns:
                raise GisEngineError(f"列不存在: {key}（可用列: {list(editing.columns)}）")
            editing.loc[mask, key] = value
        return self._result(
            f"已更新 {n} 个要素（待 commit）",
            stats={"updated": n, "rows": int(len(editing))},
        )

    def update_geometry(self, feature_id: int, geometry: str) -> dict:
        """编辑会话中修改指定要素几何"""
        editing = self._require_editing()
        try:
            from shapely import wkt as shapely_wkt

            geom = shapely_wkt.loads(geometry)
        except Exception as exc:
            raise GisEngineError(f"无效 WKT 几何: {exc}") from exc
        if feature_id < 0 or feature_id >= len(editing):
            raise GisEngineError(f"要素行号越界: {feature_id}（共 {len(editing)} 行）")
        editing.loc[feature_id, editing.geometry.name] = geom
        return self._result(f"已更新要素 #{feature_id} 几何（待 commit）")

    def delete_features(self, ids: list[int]) -> dict:
        """编辑会话中按行号删除要素"""
        editing = self._require_editing()
        drop = sorted({int(i) for i in ids})
        if not drop:
            raise GisEngineError("ids 不能为空")
        valid = [i for i in drop if 0 <= i < len(editing)]
        if not valid:
            raise GisEngineError("所有行号越界")
        self._editing = editing.drop(index=valid).reset_index(drop=True)
        return self._result(
            f"已删除 {len(valid)} 个要素（待 commit）",
            stats={"deleted": len(valid), "rows": int(len(self._editing))},
        )

    def calculate_field(self, expression: str, field_name: str, where: str | None = None) -> dict:
        """编辑会话中按表达式生成新列，如 'gdp / population'。可选 where 限定范围。"""
        editing = self._require_editing()
        if field_name in editing.columns:
            raise GisEngineError(f"字段已存在: {field_name}（可用列: {list(editing.columns)}）")
        try:
            values = editing.eval(expression)
        except Exception as exc:
            raise GisEngineError(f"计算表达式无效: {exc}") from exc
        if where:
            try:
                mask = editing.eval(where)
            except Exception as exc:
                raise GisEngineError(f"条件表达式无效: {exc}") from exc
            values = values.where(mask)
        self._editing[field_name] = values
        return self._result(
            f"已新增字段 {field_name}（待 commit）",
            stats={"field": field_name, "rows": int(len(self._editing))},
        )

    def commit_edits(self) -> dict:
        """提交编辑：缓冲区生效为当前图层"""
        editing = self._require_editing()
        self._layer = editing
        self._editing = None
        return self._result(
            "已提交编辑，修改已生效",
            stats={"committed": True, "rows": int(len(self._layer))},
        )

    def rollback_edits(self) -> dict:
        """回滚编辑：丢弃所有未提交修改"""
        if self._editing is None:
            raise GisEngineError("当前没有未提交的编辑会话")
        self._editing = None
        return self._result(
            "已回滚编辑，修改已丢弃",
            stats={"rolled_back": True, "rows": int(len(self._layer))},
        )

    def duplicate_layer(self) -> dict:
        """复制当前图层为新的当前图层（编辑前备份）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        self._layer = self._layer.copy()
        return self._result(
            "已复制当前图层",
            stats={"rows": int(len(self._layer))},
        )

    def get_project_info(self) -> dict:
        """获取当前工程信息（引擎状态摘要）"""
        return {
            "status": "ok",
            "engine": "geopandas",
            "layer": self._summary(self._layer) if self._layer is not None else None,
            "raster": self._raster,
            "outputs": list(self.outputs),
            "output_paths": self._output_paths(),
            "out_dir": str(self.out_dir.resolve()),
        }

    def save_project(self, path: str = "gis_project.qgz") -> dict:
        """保存 QGIS 工程文件（仅 QGIS 引擎支持）"""
        raise GisEngineError(
            "geopandas 引擎不支持保存 QGIS 工程，请用 GIS_ENGINE=qgis 或改用 export_geojson"
        )

    def save_layer_snapshot(self, path: str) -> None:
        """???????? GeoJSON????????????????"""
        if self._layer is None:
            return
        self._layer.to_file(path, driver="GeoJSON")

    def finish(self, outputs: list[str] | None = None, summary: str = "") -> dict:
        """任务完成：声明产出文件与结论（以该工具结束对话）"""
        declared = [o for o in (outputs or []) if (self.out_dir / o).is_file()]
        final_outputs = declared or list(self.outputs)
        return {
            "status": "finished",
            "message": "任务完成",
            "outputs": final_outputs,
            "output_paths": [str((self.out_dir / o).resolve()) for o in final_outputs],
            "explanation": summary,
        }

    def dump(self) -> str:
        """当前会话状态（调试用）"""
        return json.dumps(
            {
                "layer": self._summary(self._layer) if self._layer is not None else None,
                "outputs": self.outputs,
                "out_dir": str(self.out_dir),
            },
            ensure_ascii=False,
        )


def create_gis_engine(engine: str | None = None, **kwargs) -> GisEngine:
    """按 GIS_ENGINE 环境变量（geopandas 默认 / qgis / live）创建引擎"""
    name = (engine or os.environ.get("GIS_ENGINE") or "geopandas").strip().lower()
    if name == "qgis":
        from src.gis_toolkit.qgis_engine import QgsEngine  # 延迟导入，无 QGIS 环境不报错

        return QgsEngine(**kwargs)
    if name == "live":
        from src.gis_toolkit.live_engine import LiveEngine  # 延迟导入

        return LiveEngine(**kwargs)
    if name != "geopandas":
        raise GisEngineError(f"未知引擎: {name}（可选 geopandas/qgis/live）")
    return GisEngine(**kwargs)
