# GIS 3D 城市可视化 — 最小演示方案

> 状态：方案待评审（2026-08-24）
> 目标：用「城市建筑轮廓 + 高度」在 Web 端做出可旋转/倾斜的 3D 城市视角，
> 作为 GIS 助手从「2D 分析出图」走向「操作/可视化」能力的第一个演示。

## 1. 结论先行

- **可行**：建筑轮廓数据可从 OpenStreetMap（Overpass API）免费按 bbox 下载，
  已实测北京中关村-五道口范围（约 4km×4km）拿到 **2766 栋建筑 / 2MB** GeoJSON。
- **3D 渲染用 MapLibre GL JS 的 `fill-extrusion`** 最轻量：直接把 GeoJSON 按高度字段
  拉伸成体块，支持相机倾斜/旋转，单个 HTML 页面即可跑通。
- **关键约束**：OSM 中国区建筑高度字段覆盖很低（实测 2766 栋中仅 191 栋带
  `building:levels`、18 栋带 `height`），所以必须做**高度估算**（见 §3.3）。

## 2. 演示数据

### 2.1 区域选择：中关村-五道口（含清华/北大周边）

- bbox：`south=39.97, west=116.30, north=40.01, east=116.34`
- 特征：高校、科研、商圈密集（搜狐网络大厦、五道口购物中心、清华/北大园区等），
  3D 体块层次感强，适合演示。
- 产出文件：`data/gis_3d/zhongguancun_buildings.geojson`

### 2.2 数据来源（按优先级）

| 来源 | 说明 | 高度字段 | 适用 |
|---|---|---|---|
| Overpass API（首选） | OSM 镜像，按 bbox/tag 查询 | 稀疏（需估算） | 单城区小范围演示 |
| Overture Maps | 全球建筑轮廓（GeoParquet/GeoJSON） | 无，需另配高度 | 整城市轮廓 |
| Geofabrik 导出 | 整省/整国 OSM 原始数据 | 稀疏 | 离线/大范围 |

### 2.3 Overpass 查询（已验证）

```text
[out:json][timeout:60];
(
  way["building"](39.97,116.30,40.01,116.34);
);
out geom;
```

- 端点：`https://overpass-api.de/api/interpreter`（备选 `overpass.kumi.systems` 等）
- 实测：2766 个要素，响应约 2.1MB，单次查询 1 分钟内完成。

## 3. 3D 渲染方案

### 3.1 首选：MapLibre GL JS `fill-extrusion`

- 数据直接加载本地 GeoJSON，无需切片、无需服务端。
- 图层属性：`fill-extrusion-height` ← 高度字段，`fill-extrusion-color` ← 按高度渐变。
- 相机：`pitch` 倾斜 + `bearing` 旋转 + 飞行动画（`flyTo`），实现"城市 3D 视角"。
- 底图：OSM 栅格瓦片或 天地图 底图，方便对照街道。
- 优点：单 HTML + CDN 依赖即可跑，最符合"最小演示"。

### 3.2 备选（后续演进）

| 方案 | 能力 | 成本 |
|---|---|---|
| CesiumJS | 真 3D 地球、3D Tiles、倾斜摄影 | 重，需数据生产 |
| QGIS 3D Map View | 桌面端 3D，与 QGIS 引擎路线一致 | 依赖 QGIS 环境 |
| deck.gl / ArcGIS Scene | 大规模可视化 | 中/重 |

### 3.3 高度估算策略（必做）

OSM 高度字段覆盖低，导出脚本统一生成 `height_m` 字段：

1. `height` 标签存在 → 直接使用（米）；
2. 否则 `building:levels` × **3.0 米/层**；
3. 都没有 → 默认 **10 米**（可按 `building` 类型细分，如 `building=garage` 用 4m）。

页面/README 必须标注：**建筑高度为估算值，仅用于可视化演示，非测绘数据**。

## 4. 最小演示结构

```text
scripts/download_osm_buildings.py     # Overpass 查询 → GeoJSON + height_m 估算字段
data/gis_3d/zhongguancun_buildings.geojson   # 下载产物（入库，约 2MB）
frontend/3d-demo/index.html           # 独立演示页（MapLibre CDN + 本地 GeoJSON）
```

演示页功能：
- 加载 `zhongguancun_buildings.geojson`，按 `height_m` 拉伸；
- 默认视角：`pitch=60`、`bearing` 旋转、自动 `flyTo` 到区域中心；
- 控件：高度颜色图例 + 数据来源标注（OpenStreetMap © OSM contributors）。

## 5. 与现有助手的集成路径

| 阶段 | 内容 | 验收 |
|---|---|---|
| 0 最小演示 | 下载脚本 + 独立 HTML，浏览器直接打开 | 能看到 3D 建筑体块，可倾斜/旋转 |
| 1 挂载到后端 | 演示页放到 `src/web/static/3d-demo/`，访问 `http://localhost:8080/3d-demo/` | 后端一键启动即可访问 |
| 2 接入助手 | 新增工具（如 `download_osm_buildings` + `render_3d`）或前端地图画布，让 agent 能"按城市/范围出 3D 预览" | 自然语言可触发 3D 预览 |

阶段 2 属于"操作类能力"方向（区别于当前 2D 读数据分析），与 QGIS 引擎/前端地图
规划一致，可作为 Gate 8 候选。

## 6. 合规与风险

- **许可**：OSM 数据为 **ODbL** 许可，展示需署名 `© OpenStreetMap contributors`；
  Overture Maps 另有自己的许可条款，商用前需确认。
- **Overpass 限流**：单次 bbox 控制在几 MB 内；大范围下载改走 Geofabrik/Overture。
- **高度为估算**：不能用于测量/工程，仅可视化演示。
- **体积**：整座城市的建筑轮廓可达百 MB 级，演示固定用中关村小范围，避免入库膨胀。

## 7. 验收标准（阶段 0）

- [ ] `scripts/download_osm_buildings.py` 可复现下载（网络可用时）；
- [ ] 打开演示页可见 3D 建筑体块，相机可倾斜/旋转，街道走向可辨认；
- [ ] 页面标注数据来源与"高度为估算值"说明；
- [ ] 数据文件入库、脚本入库，`ruff check` 通过。
