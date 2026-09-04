# QGIS 插件（M2b：GIS Assistant Live）

把「GIS 智能操作助手」的执行端接到**用户当前打开的 QGIS 工程**。

> 设计见 `docs/GIS-QGIS插件嵌入方案.md`；验收任务见 `docs/GIS-智能助手-数据生产员任务清单.md`。

## M2b 提供什么

- QGIS 停靠面板：实时显示当前工程路径、CRS、图层列表（类型/要素数/选中数/是否编辑中）；
- 本地服务（带 `X-GIS-Token` 头，仅 127.0.0.1）：
  - `GET /v1/health`、`GET /v1/state`：只读状态；
  - `POST /v1/tools/invoke`：在 GUI 主线程执行工具，结果图层真实加入当前工程。
- 首批 17 个工具：`load_data / inspect_data / buffer / start_editing / add_features /
  update_features / delete_features / calculate_field / commit_edits / rollback_edits /
  export_geojson / duplicate_layer / rename_layer / remove_layer / get_crs /
  field_statistics / unique_values`。

## 部署（本机）

```powershell
# 把插件同步到 QGIS 默认 profile 的插件目录
$dst = "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\gis_assistant"
Copy-Item -Recurse -Force .\qgis_plugin\gis_assistant $dst
```

每次改完插件代码后重复上面的 Copy-Item，然后**重启 QGIS 使新插件生效**。

然后在 QGIS 里：

1. 打开 QGIS → 菜单「插件 → 管理并安装插件」→ 勾选 **GIS Assistant Live**；
2. 菜单「GIS 智能助手 → 打开 GIS 助手面板」；
3. 面板会显示本地服务地址；点「复制」拿 Token，主进程 `.env` 配置 `LIVE_QGIS_URL` 与 `LIVE_QGIS_TOKEN` 指向它；
4. 后端冒烟：`venv\Scripts\python.exe scripts\smoke_live_engine.py`（只读状态）；
   web 里对话加载/编辑真实工程图层的闭环验证见插件方案文档 M2b。

## 校验语法（无 GUI 环境）

```powershell
& 'D:\QGIS\bin\python-qgis-ltr.bat' -m py_compile `
  qgis_plugin/gis_assistant/__init__.py qgis_plugin/gis_assistant/plugin.py `
  qgis_plugin/gis_assistant/state.py qgis_plugin/gis_assistant/config.py `
  qgis_plugin/gis_assistant/control_server.py qgis_plugin/gis_assistant/live_tools.py
```

headless 冒烟（真实 QGIS 进程执行首批工具链）：

```powershell
& 'D:\QGIS\bin\python-qgis-ltr.bat' qgis_plugin/smoke_headless.py
```
