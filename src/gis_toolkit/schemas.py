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
            "description": "对当前图层数值列做聚合统计（可选按分组列分组），结果导出 CSV（utf-8-sig）。",
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
]
