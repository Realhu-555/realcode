"""GIS 引擎 — 基于 GeoPandas 的实现（工具接口面向未来 PyQGIS 对接抽象）

每个工具返回可 JSON 序列化的摘要 dict；产物（图/CSV/GeoJSON）写入引擎输出目录。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import geopandas as gpd
import matplotlib

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
        raise GisEngineError(
            f"非法产物文件名: {name!r}（只允许字母/数字/._-，禁止路径）"
        )
    return name


def _jsonable(obj):
    """????? JSON ??????shapely?WKT?numpy ???????????str"""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if hasattr(obj, "wkt"):  # shapely ??
        return obj.wkt
    if hasattr(obj, "item"):  # numpy ??
        return obj.item()
    if hasattr(obj, "tolist"):  # numpy ??
        return obj.tolist()
    return str(obj)



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
        self._editing: gpd.GeoDataFrame | None = None  # 编辑会话缓冲区
        self._raster: str | None = None  # 当前栅格文件路径（栅格状态与矢量状态并存）
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
        return self._result(f"已加载 {Path(path).name}，{len(gdf)} 行")

    def inspect_data(self) -> dict:
        """查看当前图层：字段、行数、CRS、范围、样例行"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        gdf = self._layer
        info = self._summary(gdf)
        bounds = gdf.total_bounds.tolist() if len(gdf) else None
        non_geom = gdf.drop(columns=[gdf.geometry.name]) if gdf.geometry.name in gdf.columns else gdf
        sample = _jsonable(non_geom.head(5).to_dict(orient="records"))
        return {
            "status": "ok",
            "message": f"???? {len(gdf)} ??CRS: {gdf.crs}",
            **info,
            "bounds": bounds,
            "sample_rows": sample,
        }

    def buffer(self, distance: float) -> dict:
        """对当前图层所有要素做缓冲区（distance 单位以当前 CRS 为准）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        gdf = self._layer.copy()
        gdf.geometry = gdf.geometry.buffer(distance)
        self._layer = gdf
        return self._result(
            f"已生成 {distance} 单位缓冲区（CRS: {self._layer.crs}，单位以坐标系为准）"
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
                note = f"（按省份聚合省界底图，{len(missing)} 个无数据省份）"
            elif is_points and self._base_map is not None:
                # 底图 + 点叠加着色
                self._base_map.plot(
                    ax=ax, color="#f0e9dd", edgecolor="#9a9082", linewidth=0.5
                )
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
        return self._result(f"已保存分级设色图 {output}{note}", size_bytes=out.stat().st_size)

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
        return self._result(f"已保存散点图 {output}", size_bytes=out.stat().st_size)

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
        if groupby:
            if groupby not in df.columns:
                raise GisEngineError(f"分组列不存在: {groupby}（可用列: {list(df.columns)}）")
            out_df = df.groupby(groupby)[column].agg(agg).reset_index()
        else:
            out_df = pd.DataFrame({column: [getattr(df[column], agg)()]})
        sort_col = sort_by or groupby or column
        if sort_col in out_df.columns:
            out_df = out_df.sort_values(sort_col, ascending=not desc)
        out = self.out_dir / _sanitize_filename(output)
        out_df.to_csv(out, index=False, encoding="utf-8-sig")
        self.outputs.append(output)
        return self._result(
            f"已保存统计结果 {output}（{len(out_df)} 行，agg={agg}）", summary_rows=int(len(out_df))
        )

    def export_geojson(self, output: str = "layer.geojson") -> dict:
        """把当前图层导出为 GeoJSON"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        out = self.out_dir / _sanitize_filename(output)
        self._layer.to_file(out, driver="GeoJSON")
        self.outputs.append(output)
        return self._result(f"已导出 {output}", size_bytes=out.stat().st_size)

    def join_by_location(self, other_path: str, predicate: str = "intersects") -> dict:
        """把另一图层按空间关系并入当前图层（结果成为新的当前图层）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if predicate not in {"intersects", "within", "contains"}:
            raise GisEngineError(
                f"predicate 必须是 intersects/within/contains，收到: {predicate}"
            )
        other = self._load_any(other_path)
        if self._layer.crs != other.crs:
            raise GisEngineError(
                f"两个图层 CRS 不一致（{self._layer.crs} vs {other.crs}），先统一坐标系"
            )
        result = gpd.sjoin(self._layer, other, how="inner", predicate=predicate)
        self._layer = result
        return self._result(
            f"空间连接完成（predicate={predicate}），结果 {len(result)} 行"
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
            result = gpd.GeoDataFrame(
                geometry=list(polys.geoms), crs=layer.crs
            )
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
            raise GisEngineError(
                f"无效坐标系: {crs!r}（示例 EPSG:4326 / EPSG:3857）"
            ) from exc
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
        ax.set_title("当前图层")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.outputs.append(output)
        return self._result(f"已保存地图 {output}", size_bytes=out.stat().st_size)

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
            raise GisEngineError(
                f"未知算法: {algorithm}（白名单: dissolve/centroids/convexhull）"
            )
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
        return self._result("已开始编辑会话（修改在 commit 前不生效）")

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
        return self._result("已新增 1 个要素（待 commit）")

    def update_features(self, where: str, attributes: dict) -> dict:
        """编辑会话中按条件更新属性"""
        editing = self._require_editing()
        try:
            mask = editing.eval(where)
        except Exception as exc:
            raise GisEngineError(f"条件表达式无效: {exc}") from exc
        n = int(mask.sum())
        if n == 0:
            return self._result("没有要素满足条件，未做修改")
        for key, value in (attributes or {}).items():
            if key not in editing.columns:
                raise GisEngineError(f"列不存在: {key}（可用列: {list(editing.columns)}）")
            editing.loc[mask, key] = value
        return self._result(f"已更新 {n} 个要素（待 commit）")

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
        return self._result(f"已删除 {len(valid)} 个要素（待 commit）")

    def commit_edits(self) -> dict:
        """提交编辑：缓冲区生效为当前图层"""
        editing = self._require_editing()
        self._layer = editing
        self._editing = None
        return self._result("已提交编辑，修改已生效")

    def rollback_edits(self) -> dict:
        """回滚编辑：丢弃所有未提交修改"""
        if self._editing is None:
            raise GisEngineError("当前没有未提交的编辑会话")
        self._editing = None
        return self._result("已回滚编辑，修改已丢弃")

    def duplicate_layer(self) -> dict:
        """复制当前图层为新的当前图层（编辑前备份）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        self._layer = self._layer.copy()
        return self._result("已复制当前图层")

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
    """按 GIS_ENGINE 环境变量（geopandas 默认 / qgis）创建引擎"""
    name = (engine or os.environ.get("GIS_ENGINE") or "geopandas").strip().lower()
    if name == "qgis":
        from src.gis_toolkit.qgis_engine import QgsEngine  # 延迟导入，无 QGIS 环境不报错

        return QgsEngine(**kwargs)
    if name != "geopandas":
        raise GisEngineError(f"未知引擎: {name}（可选 geopandas/qgis）")
    return GisEngine(**kwargs)
