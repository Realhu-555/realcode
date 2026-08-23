"""GIS 助手工具 schema — OpenAI/DeepSeek function calling 格式

工具描述对照 GeoPandas API 编写（设计文档 4 节）；引擎换 PyQGIS 时 schema 不变。
"""

from __future__ import annotations

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "load_data",
            "description": (
                "加载数据文件为当前图层。CSV 需含经纬度列（lon/lat 或 longitude/latitude），"
                "自动转为点要素（EPSG:4326）；GeoJSON / zip（含 shp）直接读取。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "数据文件路径（必须来自用户提供或已存在的项目 data 目录）",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_data",
            "description": (
                "查看当前图层：字段列表、行数、CRS、坐标范围、前 5 行样例。"
                "决定后续操作前应调用一次。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buffer",
            "description": "对当前图层所有要素做缓冲区。distance 单位以当前 CRS 为准（EPSG:4326 为度）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "number",
                        "description": "缓冲区距离（单位随 CRS：度 / 米）",
                    }
                },
                "required": ["distance"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "overlay",
            "description": "把当前图层与另一图层做空间叠加，结果成为新的当前图层。两个图层 CRS 必须一致。",
            "parameters": {
                "type": "object",
                "properties": {
                    "other_path": {
                        "type": "string",
                        "description": "第二个数据文件路径（CSV / GeoJSON / zip）",
                    },
                    "how": {
                        "type": "string",
                        "enum": ["intersection", "union", "difference", "symmetric_difference"],
                        "description": "叠加方式",
                    },
                },
                "required": ["other_path", "how"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "choropleth",
            "description": "对当前图层的数值列做分级设色图并保存 PNG。数值列会自动转数字，非数值列会失败。若当前为点数据且引擎内置中国省界底图，将按省份聚合输出省面地图（点数据含 province 列时）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "用于分级的数值列名"},
                    "scheme": {
                        "type": "string",
                        "enum": ["NaturalBreaks", "Quantiles", "EqualInterval"],
                        "description": "分级方法",
                    },
                    "k": {"type": "integer", "description": "分级数量（默认 5）"},
                    "output": {"type": "string", "description": "产物文件名，如 choropleth.png"},
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scatter_plot",
            "description": "对当前图层两个数值列画散点图并保存 PNG。",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "string", "description": "X 轴列名"},
                    "y": {"type": "string", "description": "Y 轴列名"},
                    "output": {"type": "string", "description": "产物文件名，如 scatter.png"},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize",
              "description": (
                  "对当前图层数值列做聚合统计（可选按分组列分组），结果导出 CSV（utf-8-sig）。"
                  "可按结果列排序（sort_by + desc），便于产出 Top 名单。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "column": {"type": "string", "description": "被统计的数值列名"},
                      "groupby": {"type": "string", "description": "分组列名（可选）"},
                    "agg": {
                        "type": "string",
                        "enum": ["sum", "mean", "count", "min", "max"],
                        "description": "聚合方式",
                      },
                      "output": {"type": "string", "description": "产物文件名，如 summary.csv"},
                      "sort_by": {
                          "type": "string",
                          "description": "排序依据列（默认分组列或统计列）",
                      },
                      "desc": {
                          "type": "boolean",
                          "description": "降序排序（默认 false 升序；取 Top 名单时传 true）",
                      },
                  },
                  "required": ["column"],
              },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_geojson",
            "description": "把当前图层导出为 GeoJSON 文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "output": {"type": "string", "description": "产物文件名，如 layer.geojson"},
                },
                "required": ["output"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": (
                "任务完成时调用，声明产出文件清单与结论，结束对话。"
                "outputs 只能列真实生成的文件；引擎会核对存在性。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "outputs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "本次任务产出的文件名列表",
                    },
                    "summary": {"type": "string", "description": "任务结论说明"},
                },
                "required": ["outputs", "summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "join_by_location",
            "description": (
                "把当前图层与另一图层做空间连接：按空间关系（intersects/within/contains）"
                "把另一图层的属性并入当前图层，结果成为新的当前图层。"
                "常用于把 POI 归属到行政区、统计设施影响范围。两个图层 CRS 必须一致。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "other_path": {
                        "type": "string",
                        "description": "第二个数据文件路径（CSV / GeoJSON / zip），须在 data 白名单内",
                    },
                    "predicate": {
                        "type": "string",
                        "enum": ["intersects", "within", "contains"],
                        "description": "空间关系：intersects 相交 / within 要素在另一图层要素内 / contains 包含另一图层要素",
                    },
                },
                "required": ["other_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "voronoi",
            "description": (
                "对当前点图层生成泰森多边形（Voronoi），结果成为新的当前图层。"
                "用于服务范围 / 商圈 / 站点覆盖划分。只支持点图层。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_crs",
            "description": (
                "查看当前图层的坐标系（CRS）：返回 authid（如 EPSG:4326）与描述。"
                "空间叠加/连接前建议确认坐标系一致。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_crs",
            "description": (
                "重设当前图层坐标系（只改声明、不改坐标值，重投影另见工具）。"
                "两个图层 CRS 不一致时，先统一坐标系再做叠加 / 连接。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "crs": {
                        "type": "string",
                        "description": "坐标系，如 EPSG:4326（WGS84 经纬度）或 EPSG:3857（Web 墨卡托）",
                    }
                },
                "required": ["crs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_layers",
            "description": (
                "查看当前会话状态：是否有图层、图层摘要（行数/字段/CRS/几何类型）、"
                "已生成产物、产物路径、输出目录。任务开始时建议先确认状态。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "field_statistics",
            "description": (
                "对当前图层的数值列做字段统计：行数、均值、标准差、最小/最大值、缺失值数。"
                "用于了解数据分布，决定是否适合分级/聚合。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "数值列名"}
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unique_values",
            "description": (
                "查看某列的唯一取值（最多返回 50 个）。用于了解分类列/枚举列的取值，"
                "或确认某列是否适合作为分组列。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "列名"}
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transform_coords",
            "description": (
                "把当前图层重投影到目标坐标系（变换坐标值，如 EPSG:4326 经纬度 → EPSG:3857 米制）。"
                "结果成为新的当前图层。需要与其他图层做叠加/连接但 CRS 不一致时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_crs": {
                        "type": "string",
                        "description": "目标坐标系，如 EPSG:3857 / EPSG:32650",
                    }
                },
                "required": ["target_crs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_map",
            "description": (
                "把当前图层渲染成一张地图 PNG（默认样式：面淡色填充、点/线着色），"
                "保存到输出目录。用于快速查看当前图层全貌。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "output": {"type": "string", "description": "产物文件名，如 map.png"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_algorithm",
            "description": (
                "运行白名单内的 Processing 空间算法，结果成为新的当前图层。"
                "当前支持：dissolve（按字段融合要素）、centroids（生成要素质心点）、"
                "convexhull（每要素凸包）。只开放白名单算法，不执行任意脚本。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "algorithm": {
                        "type": "string",
                        "enum": ["dissolve", "centroids", "convexhull"],
                        "description": "算法名",
                    },
                    "params": {
                        "type": "object",
                        "description": "算法参数：dissolve 传 {\"field\": \"字段名\"}；centroids/convexhull 可省略",
                        "properties": {
                            "field": {"type": "string", "description": "dissolve 的分组字段名"}
                        },
                    },
                },
                "required": ["algorithm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_raster",
            "description": (
                "加载栅格文件（TIFF / GeoTIFF / IMG）为当前栅格图层，返回元数据"
                "（宽高、波段数、数据类型、CRS、范围）。地形 / 影像分析前先加载。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "栅格文件路径（TIFF / GeoTIFF），须在 data 白名单内",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_editing",
            "description": (
                "开始编辑会话：复制当前图层到编辑缓冲区。之后的增/改/删操作只在缓冲区内，"
                "commit_edits 提交生效、rollback_edits 回滚。所有编辑必须在会话内进行。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_features",
            "description": (
                "在当前编辑会话中新增要素。geometry 为 WKT（如 POINT(116 39) / LINESTRING(...) / "
                "POLYGON((...))）；attributes 为可选属性键值。危险操作，需人工审批。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "geometry": {"type": "string", "description": "新要素几何（WKT 格式）"},
                    "attributes": {
                        "type": "object",
                        "description": "属性键值（可选），如 {\"name\": \"站点A\"}",
                    },
                },
                "required": ["geometry"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_features",
            "description": (
                "在编辑会话中按条件更新要素属性。where 为条件表达式，如 id == 1 或 "
                "province == '北京'。危险操作，需人工审批。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "where": {"type": "string", "description": "筛选条件表达式"},
                    "attributes": {
                        "type": "object",
                        "description": "要更新的属性键值，如 {\"gdp\": 50000}",
                    },
                },
                "required": ["where", "attributes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_geometry",
            "description": "在编辑会话中修改指定要素的几何。feature_id 为要素行号（0 起）。危险操作，需人工审批。",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_id": {"type": "integer", "description": "要素行号（0 起）"},
                    "geometry": {"type": "string", "description": "新几何（WKT 格式）"},
                },
                "required": ["feature_id", "geometry"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_features",
            "description": (
                "在编辑会话中按要素行号列表删除要素（如 [0, 3]）。危险操作，需人工审批。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要删除的要素行号列表",
                    }
                },
                "required": ["ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "commit_edits",
            "description": "提交编辑会话：缓冲区改动生效为当前图层，结束编辑。危险操作，需人工审批。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rollback_edits",
            "description": "回滚编辑会话：丢弃缓冲区所有未提交修改，结束编辑。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "duplicate_layer",
            "description": "复制当前图层为新的当前图层（编辑/修改前的安全备份）。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
