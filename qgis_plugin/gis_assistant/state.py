"""只读工程状态快照 — 由 GUI 主线程定时刷新，HTTP 线程只读。"""

from __future__ import annotations

import copy
import threading

from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes


def _vector_info(layer: QgsVectorLayer) -> dict:
    """收集单个矢量图层的主线程安全摘要（纯 dict）。"""
    geometry = QgsWkbTypes.displayString(layer.wkbType())
    return {
        "id": layer.id(),
        "name": layer.name(),
        "type": "Vector",
        "geometry": geometry,
        "features": int(layer.featureCount()),
        "selected": int(layer.selectedFeatureCount()),
        "editing": bool(layer.isEditable()),
    }


class ProjectSnapshot:
    """定时在主线程 refresh()，供任何线程 get() 读取。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict = {
            "project": "",
            "crs": "",
            "layers": [],
        }

    def refresh(self) -> None:
        """主线程调用：读取当前工程并更新快照。"""
        project = QgsProject.instance()
        layers = []
        for layer in project.mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                layers.append(_vector_info(layer))
            else:
                layers.append(
                    {
                        "id": layer.id(),
                        "name": layer.name(),
                        "type": layer.type().name,
                        "geometry": "",
                        "features": -1,
                        "selected": 0,
                        "editing": False,
                    }
                )
        snapshot = {
            "project": project.fileName() or "",
            "crs": project.crs().authid() if project.crs().isValid() else "",
            "layers": layers,
        }
        with self._lock:
            self._data = snapshot

    def get(self) -> dict:
        """任意线程调用：返回当前快照副本。"""
        with self._lock:
            return copy.deepcopy(self._data)
