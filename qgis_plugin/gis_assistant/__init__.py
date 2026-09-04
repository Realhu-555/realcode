"""GIS Assistant Live — QGIS 插件入口。"""


def classFactory(iface):
    """QGIS 加载插件时调用，返回插件实例。"""
    from .plugin import GisAssistantPlugin

    return GisAssistantPlugin(iface)
