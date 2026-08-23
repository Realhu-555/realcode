"""QGIS 引擎 — 通过常驻 worker 子进程调用 PyQGIS，接口与 GisEngine 对齐。

- 主进程（项目 venv）不依赖 QGIS，安全校验（路径白名单/文件名净化）留在主进程；
- worker（QGIS 自带 Python）只做 GIS 运算，stdin/stdout JSON-lines 通信；
- 9 个工具 schema / Agent / 前端零改动，GIS_ENGINE=qgis 时切换到此引擎。
"""

from __future__ import annotations

import contextlib
import glob
import json
import os
import subprocess
from pathlib import Path

from src.gis_toolkit.engine import (
    GisEngineError,
    _check_input_path,
    _sanitize_filename,
)

_WORKER_SCRIPT = Path(__file__).resolve().parent / "qgis_worker.py"


def _find_qgis_prefix() -> str:
    """定位 QGIS 前缀目录（含 python/qgis/core 的 apps/qgis-ltr）"""
    candidates: list[str] = []
    env = os.environ.get("QGIS_PREFIX_PATH")
    if env:
        candidates.append(env)
    candidates += [
        r"D:\QGIS\apps\qgis-ltr",
        r"C:\Program Files\QGIS 3.40.10\apps\qgis-ltr",
    ]
    candidates += sorted(glob.glob(r"C:\Program Files\QGIS*\apps\qgis-ltr"))
    for c in candidates:
        if c and os.path.isdir(os.path.join(c, "python", "qgis", "core")):
            return c
    raise GisEngineError(
        "未找到 QGIS 安装（设置 QGIS_PREFIX_PATH 指向 apps/qgis-ltr 目录）"
    )


class QgsEngine:
    """单会话 QGIS 引擎：主进程持有安全校验与产物清单，worker 持有当前图层"""

    def __init__(
        self,
        data_file: str | None = None,
        out_dir: str = "data/gis_toolkit_out",
        allowed_roots: list[str] | None = None,
    ) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._roots = [Path(r).resolve() for r in (allowed_roots or ["data"])]
        self.outputs: list[str] = []
        self._layer: dict | None = None  # worker 侧图层摘要（与 GisEngine._layer 语义对齐）
        self._proc: subprocess.Popen | None = None
        self._start_worker()
        if data_file:
            self.load_data(data_file)

    # ── worker 生命周期 ──
    def _start_worker(self) -> None:
        prefix = _find_qgis_prefix()
        bin_dir = Path(prefix).parent.parent / "bin"
        bat = bin_dir / "python-qgis-ltr.bat"
        if not bat.is_file():
            bat = bin_dir / "python-qgis.bat"
        if not bat.is_file():
            raise GisEngineError(f"未找到 QGIS python 启动脚本: {bat}")
        env = dict(os.environ)
        env.setdefault("QGIS_PREFIX_PATH", str(prefix))
        cmd = ["cmd", "/c", str(bat), str(_WORKER_SCRIPT), str(self.out_dir.resolve())]
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            env=env,
        )
        # 握手：worker 未就绪时启动失败
        self._proc.stdin.write(json.dumps({"op": "ping"}) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        if not line or not json.loads(line).get("ok"):
            raise GisEngineError("QGIS worker 启动失败")

    def _call(self, tool: str, args: dict | None = None) -> dict:
        if self._proc is None or self._proc.poll() is not None:
            raise GisEngineError("QGIS worker 进程已退出，请重建会话")
        req = {"op": "call", "tool": tool, "args": args or {}}
        self._proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        if not line:
            raise GisEngineError("QGIS worker 无响应（进程可能已崩溃）")
        try:
            resp = json.loads(line)
        except json.JSONDecodeError:
            raise GisEngineError(f"QGIS worker 返回非法 JSON: {line[:200]}") from None
        if not resp.get("ok"):
            raise GisEngineError(resp.get("error", "worker 执行失败"))
        return resp.get("result") or {}

    def close(self) -> None:
        """优雅关闭 worker 进程"""
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.stdin.write(json.dumps({"op": "exit"}) + "\n")
                self._proc.stdin.flush()
                self._proc.wait(timeout=10)
            except Exception:
                self._proc.kill()
        self._proc = None

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()

    # ── 结果组装 ──
    def _merge(self, result: dict) -> dict:
        """worker 结果补 outputs；同步当前图层摘要"""
        if result.get("layer") is not None:
            self._layer = result["layer"]
        result["outputs"] = list(self.outputs)
        result["output_paths"] = [
            str((self.out_dir / o).resolve()) for o in self.outputs
        ]
        return result

    # ── 工具实现（签名与 GisEngine 完全一致）──
    def load_data(self, path: str) -> dict:
        resolved = _check_input_path(path, self._roots)
        return self._merge(self._call("load_data", {"path": str(resolved)}))

    def inspect_data(self) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._call("inspect_data")

    def buffer(self, distance: float) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("buffer", {"distance": float(distance)}))

    def overlay(self, other_path: str, how: str = "intersection") -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        resolved = _check_input_path(other_path, self._roots)
        return self._merge(
            self._call("overlay", {"other_path": str(resolved), "how": how})
        )

    def choropleth(
        self,
        column: str,
        scheme: str = "NaturalBreaks",
        k: int = 5,
        output: str = "choropleth.png",
    ) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        name = _sanitize_filename(output)
        result = self._call(
            "choropleth",
            {"column": column, "scheme": scheme, "k": int(k), "output": name},
        )
        self.outputs.append(name)
        return self._merge(result)

    def scatter_plot(self, x: str, y: str, output: str = "scatter.png") -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        name = _sanitize_filename(output)
        result = self._call("scatter_plot", {"x": x, "y": y, "output": name})
        self.outputs.append(name)
        return self._merge(result)

    def summarize(
        self,
        column: str,
        groupby: str | None = None,
        agg: str = "sum",
        output: str = "summary.csv",
        sort_by: str | None = None,
        desc: bool = False,
    ) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        name = _sanitize_filename(output)
        result = self._call(
            "summarize",
            {
                "column": column,
                "groupby": groupby,
                "agg": agg,
                "output": name,
                "sort_by": sort_by,
                "desc": desc,
            },
        )
        self.outputs.append(name)
        return self._merge(result)

    def export_geojson(self, output: str = "layer.geojson") -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        name = _sanitize_filename(output)
        result = self._call("export_geojson", {"output": name})
        self.outputs.append(name)
        return self._merge(result)

    def join_by_location(self, other_path: str, predicate: str = "intersects") -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        resolved = _check_input_path(other_path, self._roots)
        return self._merge(
            self._call(
                "join_by_location",
                {"other_path": str(resolved), "predicate": predicate},
            )
        )

    def voronoi(self) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("voronoi"))

    def get_crs(self) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._call("get_crs")

    def set_crs(self, crs: str) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("set_crs", {"crs": crs}))

    def list_layers(self) -> dict:
        return self._merge(self._call("list_layers"))

    def field_statistics(self, column: str) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._call("field_statistics", {"column": column})

    def unique_values(self, column: str) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._call("unique_values", {"column": column})

    def transform_coords(self, target_crs: str) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(
            self._call("transform_coords", {"target_crs": target_crs})
        )

    def render_map(self, output: str = "map.png") -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        name = _sanitize_filename(output)
        result = self._call("render_map", {"output": name})
        self.outputs.append(name)
        return self._merge(result)

    def run_algorithm(self, algorithm: str, params: dict | None = None) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(
            self._call("run_algorithm", {"algorithm": algorithm, "params": params or {}})
        )

    def load_raster(self, path: str) -> dict:
        resolved = _check_input_path(path, self._roots)
        return self._call("load_raster", {"path": str(resolved)})

    def start_editing(self) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("start_editing"))

    def add_features(self, geometry: str, attributes: dict | None = None) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(
            self._call(
                "add_features",
                {"geometry": geometry, "attributes": attributes or {}},
            )
        )

    def update_features(self, where: str, attributes: dict) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(
            self._call(
                "update_features",
                {"where": where, "attributes": attributes},
            )
        )

    def update_geometry(self, feature_id: int, geometry: str) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(
            self._call(
                "update_geometry",
                {"feature_id": int(feature_id), "geometry": geometry},
            )
        )

    def delete_features(self, ids: list[int]) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("delete_features", {"ids": list(ids)}))

    def commit_edits(self) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("commit_edits"))

    def rollback_edits(self) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("rollback_edits"))

    def duplicate_layer(self) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(self._call("duplicate_layer"))

    def categorized(self, column: str, output: str = "categorized.png") -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        name = _sanitize_filename(output)
        result = self._call("categorized", {"column": column, "output": name})
        self.outputs.append(name)
        return self._merge(result)

    def set_labeling(self, label_field: str, enabled: bool = True) -> dict:
        if self._layer is None:
            raise GisEngineError("当前没有图层，请先 load_data")
        return self._merge(
            self._call("set_labeling", {"label_field": label_field, "enabled": enabled})
        )

    def finish(self, outputs: list[str] | None = None, summary: str = "") -> dict:
        """任务完成：声明产出文件与结论（与 GisEngine 同逻辑）"""
        declared = [o for o in (outputs or []) if (self.out_dir / o).is_file()]
        final_outputs = declared or list(self.outputs)
        return {
            "status": "finished",
            "message": "任务完成",
            "outputs": final_outputs,
            "output_paths": [str((self.out_dir / o).resolve()) for o in final_outputs],
            "explanation": summary,
        }

    def save_layer_snapshot(self, path: str) -> None:
        """把当前图层快照为 GeoJSON（会话恢复用）"""
        if self._layer is None:
            return
        self._call("save_layer", {"path": str(Path(path).resolve())})

    def dump(self) -> str:
        return json.dumps(
            {
                "layer": self._layer,
                "outputs": self.outputs,
                "out_dir": str(self.out_dir),
            },
            ensure_ascii=False,
        )
