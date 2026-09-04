"""GIS Assistant Live 插件主类 — 停靠面板 + 本地状态服务。"""

from __future__ import annotations

import queue
import threading

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qgis.core import Qgis, QgsMessageLog

from . import live_tools
from .config import get_server_port, get_token
from .control_server import ControlServer
from .state import ProjectSnapshot

_MENU_NAME = "GIS 智能助手"
_PLUGIN_TAG = "GISAssistantLive"
_INVOKE_TIMEOUT_SECONDS = 300


def _log(message: str) -> None:
    QgsMessageLog.logMessage(message, _PLUGIN_TAG, Qgis.Info)


class GisAssistantPlugin:
    """M1：停靠面板展示当前工程图层状态；本地回环暴露只读状态端点。"""

    def __init__(self, iface) -> None:
        self.iface = iface
        self.snapshot = ProjectSnapshot()
        self._timer: QTimer | None = None
        self._server: ControlServer | None = None
        self._dock: QDockWidget | None = None
        self._action: QAction | None = None
        self._server_error = ""
        self._job_queue: queue.Queue = queue.Queue()
        self._invoke_timer: QTimer | None = None

        self.port = get_server_port()
        self.token = get_token()
        self._start_server()
        self.snapshot.refresh()

    # ── 控制服务 ──
    def _start_server(self) -> None:
        try:
            self._server = ControlServer(
                self.snapshot.get,
                self.token,
                self.port,
                invoker=self._submit_job,
            )
            self._server.start()
        except OSError as exc:
            self._server_error = f"本地服务启动失败(端口 {self.port}): {exc}"
            _log(self._server_error)

    # ── 工具调用桥（HTTP 线程 → GUI 主线程）──
    def _submit_job(self, payload: dict) -> dict:
        """HTTP 线程调用：把工具请求排队，等待主线程执行结果。"""
        job = {"payload": payload, "event": threading.Event(), "result": None, "cancelled": False}
        self._job_queue.put(job)
        if not job["event"].wait(_INVOKE_TIMEOUT_SECONDS):
            job["cancelled"] = True
            return {"ok": False, "error": "工具执行超时（请检查 QGIS 是否卡住）"}
        return job["result"] or {"ok": False, "error": "工具无返回"}

    def _drain_jobs(self) -> None:
        """GUI 主线程（QTimer）执行排队工具，QGIS 对象只能在这里操作。"""
        while True:
            try:
                job = self._job_queue.get_nowait()
            except queue.Empty:
                break
            if job.get("cancelled"):
                continue
            tool = (job["payload"] or {}).get("tool", "")
            try:
                result = live_tools.invoke(job["payload"])
                job["result"] = {"ok": True, "result": result}
                self._after_invoke(tool, ok=True)
            except Exception as exc:  # 工具异常回传主进程，不让插件崩溃
                job["result"] = {"ok": False, "error": str(exc)}
                self._after_invoke(tool, ok=False)
            job["event"].set()

    @staticmethod
    def _after_invoke(tool: str, ok: bool) -> None:
        """工具执行后刷新画布：新增图层全幅显示，其余仅刷新。"""
        if not ok:
            return
        try:
            from qgis.utils import iface

            if iface is None:
                return
            canvas = iface.mapCanvas()
            if canvas is None:
                return
            if tool in ("load_data", "buffer", "duplicate_layer"):
                canvas.zoomToFullExtent()
            else:
                canvas.refresh()
        except Exception:  # 画布刷新失败不影响工具结果
            return

    # ── 面板 ──
    def initGui(self) -> None:
        """创建停靠面板与菜单动作（QGIS 加载插件时调用）。"""
        self._build_dock()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self._dock)
        self._action = QAction("打开 GIS 助手面板", self.iface.mainWindow())
        self._action.setCheckable(True)
        self._action.setChecked(True)
        self._action.toggled.connect(self._dock.setVisible)
        self._dock.visibilityChanged.connect(self._action.setChecked)
        self.iface.addPluginToMenu(_MENU_NAME, self._action)

        self._invoke_timer = QTimer(self.iface.mainWindow())
        self._invoke_timer.setInterval(50)
        self._invoke_timer.timeout.connect(self._drain_jobs)
        self._invoke_timer.start()

        self._timer = QTimer(self.iface.mainWindow())
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(1500)

    def unload(self) -> None:
        if self._invoke_timer is not None:
            self._invoke_timer.stop()
        if self._timer is not None:
            self._timer.stop()
        if self._server is not None:
            self._server.stop()
        if self._dock is not None:
            self.iface.removeDockWidget(self._dock)
            self._dock.deleteLater()
        if self._action is not None:
            self.iface.removePluginMenu(_MENU_NAME, self._action)

    def _build_dock(self) -> None:
        self._dock = QDockWidget("GIS 助手 · Live", self.iface.mainWindow())
        self._dock.setObjectName("gisAssistantLiveDock")

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(6, 6, 6, 6)

        self.lbl_project = QLabel("工程: (未打开)")
        self.lbl_crs = QLabel("CRS: -")
        self.lbl_status = QLabel(self._status_text())
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_project)
        layout.addWidget(self.lbl_crs)
        layout.addWidget(self.lbl_status)

        token_row = QHBoxLayout()
        self.edit_token = QLineEdit(self.token)
        self.edit_token.setReadOnly(True)
        self.edit_token.setEchoMode(QLineEdit.Password)
        btn_copy = QPushButton("复制")
        btn_copy.setFixedWidth(48)
        btn_copy.clicked.connect(self._copy_token)
        token_row.addWidget(QLabel("Token:"))
        token_row.addWidget(self.edit_token, 1)
        token_row.addWidget(btn_copy)
        layout.addLayout(token_row)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["图层", "类型", "要素", "选中", "编辑"])
        self.tree.setRootIsDecorated(False)
        layout.addWidget(self.tree, 1)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._refresh_view)
        layout.addWidget(btn_refresh)

        self._dock.setWidget(root)

    def _status_text(self) -> str:
        if self._server_error:
            return self._server_error
        return f"本地服务: http://127.0.0.1:{self.port}/v1/state（运行中）"

    def _copy_token(self) -> None:
        QApplication.clipboard().setText(self.token)

    # ── 刷新 ──
    def _on_tick(self) -> None:
        if self._dock is None or not self._dock.isVisible():
            return
        self.snapshot.refresh()
        self._refresh_view()

    def _refresh_view(self) -> None:
        state = self.snapshot.get()
        project = state["project"]
        self.lbl_project.setText(f"工程: {project or '(未打开)'}")
        self.lbl_crs.setText(f"CRS: {state['crs'] or '-'}")

        self.tree.clear()
        for layer in state["layers"]:
            editing = "是" if layer["editing"] else ""
            selected = layer["selected"] or ""
            features = layer["features"] if layer["features"] >= 0 else ""
            item = QTreeWidgetItem(
                [
                    layer["name"],
                    f"{layer['type']}{('·' + layer['geometry']) if layer['geometry'] else ''}",
                    str(features),
                    str(selected),
                    editing,
                ]
            )
            self.tree.addTopLevelItem(item)
        for index in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(index)
