"""GIS 引擎 — 基于 GeoPandas 的实现（工具接口面向未来 PyQGIS 对接抽象）

每个工具返回可 JSON 序列化的摘要 dict；产物（图/CSV/GeoJSON）写入引擎输出目录。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

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
        if data_file:
            self.load_data(data_file)

    # ── 内部工具 ──
    def _check_input(self, path: str) -> Path:
        """校验输入路径：必须在白名单内、存在、且 ≤10MB"""
        p = Path(path)
        resolved = p.resolve()
        if not any(resolved == root or root in resolved.parents for root in self._roots):
            raise GisEngineError(f"拒绝访问白名单外的文件: {path}")
        if not resolved.is_file():
            raise GisEngineError(f"文件不存在: {path}")
        if resolved.stat().st_size > MAX_FILE_BYTES:
            raise GisEngineError(f"文件超过 {MAX_FILE_BYTES // 1024 // 1024}MB 限制: {path}")
        return resolved

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
        data.update(extra)
        return data

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
        """对数值列做分级设色图并保存 PNG（scheme: NaturalBreaks/Quantiles/EqualInterval）"""
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        if column not in self._layer.columns:
            raise GisEngineError(f"列不存在: {column}（可用列: {list(self._layer.columns)}）")
        out = self.out_dir / _sanitize_filename(output)
        fig, ax = plt.subplots(figsize=(10, 8))
        try:
            self._layer.plot(
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
        ax.set_title(f"{column} ({scheme}, k={k})")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.outputs.append(output)
        return self._result(f"已保存分级设色图 {output}", size_bytes=out.stat().st_size)

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
    ) -> dict:
        """对数值列聚合统计（可选按 groupby 列分组），导出 CSV（utf-8-sig 便于 Excel）"""
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

    def finish(self, outputs: list[str] | None = None, summary: str = "") -> dict:
        """任务完成：声明产出文件与结论（以该工具结束对话）"""
        declared = [o for o in (outputs or []) if (self.out_dir / o).is_file()]
        return {
            "status": "finished",
            "message": "任务完成",
            "outputs": declared or list(self.outputs),
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
