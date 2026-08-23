# GIS 测试数据清单

本目录存放 GIS 智能操作助手的本地测试/演示数据。边界数据来自
[DataV.GeoAtlas](https://datav.aliyun.com/portal/school/atlas/area_selector)
（公开行政区划服务），派生数据由 `scripts/generate_test_data.py` 生成。

> ⚠️ 统计字段（`gdp_2023` / `pop_2023` 等）为**近似演示值**，仅用于功能测试，
> 不用于正式业务；水系为示意线，非精确测绘数据。

## 目录结构

```text
data/
├── gis_base/            # 行政区划边界 + 派生测试图层
├── gis_demo/            # 演示 CSV（带经纬度，load_data 可直接读取）
├── gis_bench_data/      # 基准评测固定数据
├── gis_exports/         # 运行产物（gitignore，不入库）
├── gis_toolkit_out/     # 引擎输出（gitignore，不入库）
├── gis_traces/          # 会话轨迹（gitignore，不入库）
└── gis_uploads/         # 上传文件（gitignore，不入库）
```

## 行政区划边界（`data/gis_base/`）

来自 DataV.GeoAtlas，字段：`name` / `adcode` / `center` / `centroid` / `level`。

| 文件 | 级别 | 要素数 | 覆盖范围 |
|---|---|---:|---|
| `china_provinces_full.geojson` | 省级 | 35 | 全国（含港澳台） |
| `china_province.geojson` | 省级 | 34 | 全国（旧版，仅 name/adcode） |
| `beijing_districts.geojson` | 区县级 | 16 | 北京市 |
| `shanghai_districts.geojson` | 区县级 | 16 | 上海市 |
| `chongqing_districts.geojson` | 区县级 | 38 | 重庆市 |
| `hongkong_districts.geojson` | 区县级 | 18 | 香港特别行政区 |
| `macau_districts.geojson` | 区县级 | 8 | 澳门特别行政区 |
| `guangdong_cities.geojson` | 市级 | 21 | 广东省 |
| `sichuan_cities.geojson` | 市级 | 21 | 四川省 |
| `zhejiang_cities.geojson` | 市级 | 11 | 浙江省 |
| `jiangsu_cities.geojson` | 市级 | 13 | 江苏省 |
| `henan_cities.geojson` | 市级 | 18 | 河南省 |
| `shandong_cities.geojson` | 市级 | 16 | 山东省 |
| `hubei_cities.geojson` | 市级 | 17 | 湖北省 |
| `shaanxi_cities.geojson` | 市级 | 10 | 陕西省 |
| `guangzhou_districts.geojson` | 区县级 | 11 | 广州市 |
| `chengdu_districts.geojson` | 区县级 | 20 | 成都市 |

## 派生测试图层（`data/gis_base/`）

由边界 `center` 派生的政府驻地示意点，可直接用于 buffer / voronoi / 空间连接 /
散点图测试：

| 文件 | 要素数 | 说明 |
|---|---:|---|
| `china_capitals_points.geojson` | 34 | 全国省级驻地点 |
| `guangdong_cities_points.geojson` | 21 | 广东市级驻地点 |
| `sichuan_cities_points.geojson` | 21 | 四川市级驻地点 |
| `zhejiang_cities_points.geojson` | 11 | 浙江市级驻地点 |
| `beijing_districts_points.geojson` | 16 | 北京区级驻地点 |

带演示统计字段的面图层（边界 + `gdp_2023` / `pop_2023`），可直接做面分级设色：

| 文件 | 要素数 | 说明 |
|---|---:|---|
| `china_province_stats.geojson` | 35 | 省级 GDP/人口 |
| `guangdong_cities_stats.geojson` | 21 | 广东各市 GDP/人口 |
| `sichuan_cities_stats.geojson` | 21 | 四川各市 GDP/人口 |
| `zhejiang_cities_stats.geojson` | 11 | 浙江各市 GDP/人口 |
| `beijing_districts_stats.geojson` | 16 | 北京各区 GDP/人口 |
| `guangzhou_districts_stats.geojson` | 11 | 广州各区 GDP/人口 |

其他：

| 文件 | 类型 | 说明 |
|---|---|---|
| `major_rivers.geojson` | 线 | 长江/黄河/珠江/淮河/海河/松花江 示意线（buffer/相交测试） |
| `dem_demo.tif` | 栅格 | 北京范围 100×100 演示 DEM（`load_raster` 测试） |
| `basemap_demo.qgs` | 工程 | 底图演示 QGIS 工程 |

## 演示 CSV（`data/gis_demo/`）

均为 UTF-8、含经纬度列，`load_data` 可直接转点：

| 文件 | 行数 | 字段 | 用途 |
|---|---:|---|---|
| `gdp_demo.csv` | 31 | province,gdp,lon,lat | 省级 GDP 分级设色（经典冒烟） |
| `china_population.csv` | 34 | province,gdp,pop,lon,lat | 省级人口/GDP 分级设色、散点图 |
| `storm_demo.csv` | 93 | id,province,lon,lat,phase,damage,facility | 灾害点位分析、汇总、缓冲 |
| `poi_demo.csv` | 40 | id,name,type,city,lon,lat | 合成 POI（空间连接/最近邻/分类） |

## 基准数据（`data/gis_bench_data/`）

| 文件 | 说明 |
|---|---|
| `cities.geojson` | 3 个城市点（北京/上海/广州），基准评测固定数据 |

## 数据工具脚本

```bash
# 下载 DataV 行政区划边界（需联网）
python scripts/download_test_data.py

# 生成派生点/统计面/CSV/水系/栅格，并修复基准数据
venv\Scripts\python.exe scripts\generate_test_data.py
```
