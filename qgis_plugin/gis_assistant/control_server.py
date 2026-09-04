"""本地控制服务 — 只读端点 + 工具调用桥。

GET  /v1/health /v1/state：读主线程预生成的纯数据快照；
POST /v1/tools/invoke：工具调用经 invoker（plugin.py 任务队列）回到 GUI 主线程执行。

HTTP 线程本身不直接触碰 QGIS 对象，避免跨线程崩溃。
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "0.1.0"


class _RequestHandler(BaseHTTPRequestHandler):
    server_version = "GISAssistantLive/0.1"
    snapshot_getter: Callable[[], dict] = staticmethod(lambda: {})
    invoker: Callable[[dict], dict] | None = None
    token: str = ""

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return self.headers.get("X-GIS-Token", "") == self.token

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"非法 JSON 请求: {raw[:100]!r}") from exc
        return payload if isinstance(payload, dict) else {}

    def do_GET(self) -> None:
        if not self._authorized():
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        path = self.path.rstrip("/")
        if path == "/v1/health":
            self._json(200, {"ok": True, "name": "gis_assistant_live", "version": VERSION})
        elif path == "/v1/state":
            self._json(200, {"ok": True, "state": self.snapshot_getter()})
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if not self._authorized():
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        path = self.path.rstrip("/")
        if path != "/v1/tools/invoke":
            self._json(404, {"ok": False, "error": "not found"})
            return
        if self.invoker is None:
            self._json(503, {"ok": False, "error": "invoker 未就绪"})
            return
        try:
            payload = self._read_body()
        except ValueError as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        try:
            result = self.invoker(payload)
            self._json(200, result)
        except Exception as exc:  # 桥接层异常不应让服务崩溃
            self._json(500, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args) -> None:  # 静默访问日志
        pass


class ControlServer:
    """本地回环 HTTP 服务（默认 127.0.0.1:8756）。"""

    def __init__(
        self,
        snapshot_getter: Callable[[], dict],
        token: str,
        port: int,
        invoker: Callable[[dict], dict] | None = None,
    ) -> None:
        self._snapshot_getter = snapshot_getter
        self._token = token
        self._port = port
        self._invoker = invoker
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return self._port

    def start(self) -> None:
        """启动后台服务线程；端口被占用或绑定失败时抛出异常。"""
        handler = _RequestHandler
        handler.snapshot_getter = self._snapshot_getter
        handler.invoker = self._invoker
        handler.token = self._token
        self._httpd = ThreadingHTTPServer(("127.0.0.1", self._port), handler)
        if self._port == 0:
            self._port = int(self._httpd.server_address[1])
        self._httpd.daemon_threads = True
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="gis-assistant-control",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
        self._httpd = None
        self._thread = None
