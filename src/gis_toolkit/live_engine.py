"""Live 引擎 — 操作「用户当前打开的 QGIS 工程」（经本地插件通道）。

与 GisEngine / QgsEngine 保持同名方法与 JSON 摘要返回协议：
- M2a：`get_project_info` / `list_layers` 返回用户 QGIS 里**真实打开的工程**；
- M2b：首批写工具经 POST /v1/tools/invoke 转发给插件，在 GUI 主线程执行，
  结果图层真实加入当前工程（用户在 QGIS 图层树可见）。

未支持的工具调用会抛 GisEngineError，由 Agent 正常兜底并向用户说明。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from src.gis_toolkit.engine import GisEngineError, _check_input_path, _sanitize_filename
from src.utils.config import settings

_CONNECT_TIMEOUT = 5
_INVOKE_TIMEOUT = 120


class LiveEngine:
    """单会话 Live 引擎：主进程侧 HTTP 客户端，状态来自 QGIS 插件快照。"""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        out_dir: str = "data/gis_toolkit_out",
        allowed_roots: list[str] | None = None,
    ) -> None:
        self.url = (url or settings.live_qgis_url or "http://127.0.0.1:8756").rstrip("/")
        self.token = token if token is not None else settings.live_qgis_token
        if not self.token:
            raise GisEngineError(
                "live 引擎缺少 Token：请在 .env 配置 LIVE_QGIS_TOKEN（从 QGIS 插件面板复制）"
            )
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._roots = [Path(root).resolve() for root in (allowed_roots or ["data"])]
        self.outputs: list[str] = []
        self._state: dict = {}
        # live 模式下「当前图层」由 QGIS 插件持有，引擎侧不维护本地快照；
        # _layer 置 None 以满足会话/Agent 对 geopandas 引擎接口的判空。
        self._layer: dict | None = None
        self._fetch_state()  # 构造即探活，失败抛错让上层明确回退

    # ── 通道 ──
    def _request(
        self, path: str, payload: dict | None = None, timeout: int = _CONNECT_TIMEOUT
    ) -> dict:
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.url}{path}",
            data=data,
            method="POST" if payload is not None else "GET",
        )
        request.add_header("X-GIS-Token", self.token)
        if data is not None:
            request.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GisEngineError(f"QGIS 插件返回 {exc.code}: {body[:200]}") from None
        except (urllib.error.URLError, OSError) as exc:
            raise GisEngineError(
                f"无法连接 QGIS 插件（{self.url}）：{exc}。"
                "请确认 QGIS 已打开「GIS Assistant Live」插件面板"
            ) from None

    def _fetch_state(self) -> dict:
        resp = self._request("/v1/state")
        if not resp.get("ok"):
            raise GisEngineError(f"QGIS 插件状态获取失败: {resp.get('error')}")
        self._state = resp.get("state") or {}
        return self._state

    def _invoke(self, tool: str, args: dict) -> dict:
        """POST 一个工具调用到插件，返回插件侧执行结果。"""
        resp = self._request(
            "/v1/tools/invoke",
            payload={"tool": tool, "args": args, "out_dir": str(self.out_dir.resolve())},
            timeout=_INVOKE_TIMEOUT,
        )
        if not resp.get("ok"):
            raise GisEngineError(resp.get("error") or f"{tool} 执行失败")
        return resp.get("result") or {}

    def _finish_result(self, result: dict) -> dict:
        """给工具结果补产物清单（与 QgsEngine._merge 语义一致）。"""
        result["outputs"] = list(self.outputs)
        result["output_paths"] = [str((self.out_dir / name).resolve()) for name in self.outputs]
        return result

    # ── 只读工具（M2a：真实工程状态）──
    def get_project_info(self) -> dict:
        """获取用户当前 QGIS 工程信息（工程路径 / CRS / 图层清单）。"""
        self._fetch_state()
        return {
            "status": "ok",
            "engine": "qgis-live",
            "project": self._state.get("project") or "(未打开工程)",
            "crs": self._state.get("crs") or "",
            "layer_count": len(self._state.get("layers") or []),
            "layers": self._state.get("layers") or [],
            "out_dir": str(self.out_dir.resolve()),
        }

    def list_layers(self) -> dict:
        """列出用户 QGIS 当前工程里的所有图层。"""
        self._fetch_state()
        layers = self._state.get("layers") or []
        return {
            "status": "ok",
            "engine": "qgis-live",
            "count": len(layers),
            "layers": layers,
        }

    # ── M2b 首批工具（转发到插件执行，作用于真实工程图层）──
    def load_data(self, path: str) -> dict:
        """把外部数据文件加载为用户 QGIS 当前工程里的新图层。"""
        resolved = _check_input_path(path, self._roots)
        return self._invoke("load_data", {"path": str(resolved)})

    def inspect_data(self) -> dict:
        return self._invoke("inspect_data", {})

    def buffer(self, distance: float) -> dict:
        return self._invoke("buffer", {"distance": float(distance)})

    def start_editing(self) -> dict:
        return self._invoke("start_editing", {})

    def add_features(self, geometry: str, attributes: dict | None = None) -> dict:
        return self._invoke("add_features", {"geometry": geometry, "attributes": attributes or {}})

    def update_features(self, where: str, attributes: dict) -> dict:
        return self._invoke("update_features", {"where": where, "attributes": attributes})

    def delete_features(self, ids: list) -> dict:
        return self._invoke("delete_features", {"ids": list(ids)})

    def calculate_field(self, expression: str, field_name: str, where: str | None = None) -> dict:
        return self._invoke(
            "calculate_field",
            {"expression": expression, "field_name": field_name, "where": where},
        )

    def commit_edits(self) -> dict:
        return self._invoke("commit_edits", {})

    def rollback_edits(self) -> dict:
        return self._invoke("rollback_edits", {})

    def duplicate_layer(self) -> dict:
        return self._invoke("duplicate_layer", {})

    def rename_layer(self, new_name: str) -> dict:
        return self._invoke("rename_layer", {"new_name": new_name})

    def remove_layer(self) -> dict:
        return self._invoke("remove_layer", {})

    def get_crs(self) -> dict:
        return self._invoke("get_crs", {})

    def field_statistics(self, column: str) -> dict:
        return self._invoke("field_statistics", {"column": column})

    def unique_values(self, column: str) -> dict:
        return self._invoke("unique_values", {"column": column})

    def export_geojson(self, output: str = "layer.geojson") -> dict:
        """把当前图层导出为 GeoJSON 到引擎输出目录。"""
        name = _sanitize_filename(output)
        result = self._invoke("export_geojson", {"output": name})
        self.outputs.append(name)
        return self._finish_result(result)

    def finish(self, outputs: list[str] | None = None, summary: str = "") -> dict:
        """任务完成：声明产物文件与结论。"""
        declared = [name for name in (outputs or []) if (self.out_dir / name).is_file()]
        final_outputs = declared or list(self.outputs)
        return {
            "status": "finished",
            "message": "任务完成",
            "outputs": final_outputs,
            "output_paths": [str((self.out_dir / name).resolve()) for name in final_outputs],
            "explanation": summary,
        }

    def save_layer_snapshot(self, path: str) -> None:
        """live 模式的图层活在用户 QGIS 工程里，不需要落盘快照（接口占位）。"""
        return None

    def __getattr__(self, name: str):
        """未支持的工具给出明确提示（避免 Agent 收到 AttributeError 噪音）。"""
        if name.startswith("_"):
            raise AttributeError(name)
        raise GisEngineError(
            f"live 引擎尚未支持工具 {name}：插件 M2b 首批见 qgis_plugin/gis_assistant/live_tools.py"
        )
