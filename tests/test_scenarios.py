"""营销内容生成能力评测 — 8 场景跑测脚本

用法:
  cd H:/ai-dev-platform
  python tests/test_scenarios.py              # 跑全部 8 个场景
  python tests/test_scenarios.py 1 3 5        # 只跑场景 1, 3, 5
  python tests/test_scenarios.py --mode free  # 只用自由模式

结果保存在 tests/output/<时间戳>/ 目录下，每个场景生成:
  - scenario_N_<名称>_form.md    # 表单模式完整输出
  - scenario_N_<名称>_free.md    # 自由模式完整输出
  - summary.json                 # 汇总信息

⚠️ 需要有效的 DEEPSEEK_API_KEY 在 .env 中配置。
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch


# ========================================================================
# 场景定义
# ========================================================================

SCENARIOS = [
    {
        "id": 1,
        "name": "DevGate API 网关",
        "slug": "devgate",
        "tone": "极客",
        "form": {
            "mode": "form",
            "product_name": "DevGate API 网关",
            "product_description": "面向微服务架构的统一 API 网关，支持限流、鉴权、协议转换和实时监控",
            "target_users": "后端开发工程师、架构师、DevOps 团队",
            "key_selling_points": [
                "零停机热更新路由规则",
                "内置 JWT/OAuth2.0 鉴权",
                "10万QPS 单节点吞吐",
                "Prometheus + Grafana 开箱监控",
            ],
            "brand_tone": "极客",
            "competitors": ["Kong", "APISIX", "Tyk"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "我要推广一款开源的 API 网关产品叫 DevGate，目标是替代 Kong 和 APISIX "
                "在中小团队中的使用。它的核心优势是：不需要重启就能更新路由规则、"
                "内置了 OAuth2.0 鉴权、单节点能跑 10万 QPS、自带 Grafana 监控面板。"
                "目标用户是后端工程师和架构师，品牌调性偏极客硬核，技术社区驱动。"
            ),
        },
    },
    {
        "id": 2,
        "name": "眠眠 — 睡眠管理 App",
        "slug": "mianmian",
        "tone": "轻松",
        "form": {
            "mode": "form",
            "product_name": "眠眠",
            "product_description": "通过白噪音、呼吸引导和睡眠数据分析，帮助都市白领改善睡眠质量",
            "target_users": "25-40岁都市白领，入睡困难、睡眠浅的人群",
            "key_selling_points": [
                "AI 个性化睡眠方案",
                "300+ 原创白噪音曲库",
                "智能唤醒浅睡眠阶段",
                "睡眠报告可视化",
            ],
            "brand_tone": "轻松",
            "competitors": ["潮汐", "小睡眠", "Calm"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "我们做了一款叫'眠眠'的助眠 App，面向睡不好觉的都市白领。"
                "它有 AI 定制的睡眠计划、300 多种白噪音（很多是我们自己录的）、"
                "会在你睡得最浅的时候叫醒你，还会生成每周睡眠报告。"
                "风格是温暖治愈挂的，竞品有潮汐、Calm 这些。"
            ),
        },
    },
    {
        "id": 3,
        "name": "账策 — 财税自动化",
        "slug": "zhangce",
        "tone": "专业",
        "form": {
            "mode": "form",
            "product_name": "账策",
            "product_description": "面向中小企业的智能财税平台，自动完成发票识别、税务申报、财务报表生成",
            "target_users": "中小企业财务人员、代账公司、个体经营者",
            "key_selling_points": [
                "拍照自动识别发票并分类",
                "金税四期合规规则实时更新",
                "多企业切换一键报税",
                "财务报表自动生成 Word/PDF",
            ],
            "brand_tone": "专业",
            "competitors": ["慧算账", "云帐房", "用友好会计"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "我们做的是中小企业财税 SaaS，产品叫'账策'。核心功能：手机拍发票就能自动识别分类、"
                "金税四期的规则我们实时跟进更新不会报错、代账公司可以在一个账号里切换多家企业一键申报、"
                "利润表/现金流量表这些自动生成。目标用户是代账会计和中小企业财务，竞品是慧算账和云帐房。"
                "品牌调性偏专业严谨。"
            ),
        },
    },
    {
        "id": 4,
        "name": "蜂巢 NAS — 家用智能存储",
        "slug": "fengchao",
        "tone": "极客",
        "form": {
            "mode": "form",
            "product_name": "蜂巢 NAS FH-4",
            "product_description": "四盘位家用智能 NAS，支持自动备份、AI 相册分类、远程访问和家庭影音中心",
            "target_users": "数码爱好者、摄影师、小型工作室、有家庭数据管理需求的科技用户",
            "key_selling_points": [
                "四盘位最高 88TB 支持 RAID 5",
                "本地 AI 芯片相册人脸/场景识别",
                "外网穿透免公网 IP",
                "支持 Docker 和 Plex 硬解",
            ],
            "brand_tone": "极客",
            "competitors": ["群晖 DS423+", "极空间 Z4", "绿联 DX4600"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "我们的产品是'蜂巢 NAS FH-4'，四盘位家用 NAS。跟群晖不同，我们内置了一颗 AI 芯片"
                "做本地相册识别（人脸、场景、宠物）完全不上云。支持 RAID 5 最高 88TB。"
                "外网访问不用配公网 IP，我们做了内网穿透。还能跑 Docker 和 Plex 4K 硬解。"
                "目标是数码玩家和家庭用户，品牌偏极客风格。"
            ),
        },
    },
    {
        "id": 5,
        "name": "码趣 — 少儿编程平台",
        "slug": "codefun",
        "tone": "轻松",
        "form": {
            "mode": "form",
            "product_name": "码趣 CodeFun",
            "product_description": "面向 7-14 岁儿童的在线编程学习平台，通过游戏化关卡和 AI 助教引导孩子学习 Python",
            "target_users": "7-14 岁孩子的家长（25-40 岁），关注孩子 STEM 教育的中产家庭",
            "key_selling_points": [
                "游戏化闯关式学习路径",
                "AI 助教实时纠错提示",
                "完全不需家长陪同",
                "对标信奥赛大纲",
            ],
            "brand_tone": "轻松",
            "competitors": ["核桃编程", "编程猫", "小码王"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "我们在做一款叫'码趣 CodeFun'的少儿编程平台，面向 7-14 岁的小朋友学 Python。"
                "最大的不同：学习过程完全是游戏化闯关（像打游戏一样写代码），内置了 AI 助教能实时指出"
                "代码哪里错了并给出提示（家长完全不用管），课程内容对标信息学奥赛大纲。"
                "竞争对手是核桃编程、编程猫这些，品牌调性是轻松、有趣、孩子喜欢的风格。"
            ),
        },
    },
    {
        "id": 6,
        "name": "爪爪到家 — 宠物上门护理",
        "slug": "zhuazhua",
        "tone": "轻松",
        "form": {
            "mode": "form",
            "product_name": "爪爪到家",
            "product_description": "预约专业宠护师上门为宠物提供洗澡、剪甲、基础体检服务",
            "target_users": "养宠物的都市白领（25-35岁），工作忙没时间带宠物去店里的铲屎官",
            "key_selling_points": [
                "宠护师持证上岗+全程录像",
                "自带专业洗护设备",
                "服务后出具宠物健康简报",
                "迟到免单",
            ],
            "brand_tone": "轻松",
            "competitors": ["宠物家", "小佩宠物", "波奇服务"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "'爪爪到家'是一个宠物上门洗护服务平台。用户可以预约专业的宠护师到家里给猫狗"
                "洗澡、剪指甲、做基础体检。所有宠护师都有兽医助理或宠物美容师证书，服务全程录视频。"
                "自带专业设备（烘干箱、宠物专用浴液），做完还会出一份宠物健康简报。迟到直接免单。"
                "目标是养宠物的都市白领，主打方便和安心，调性轻松温暖。"
            ),
        },
    },
    {
        "id": 7,
        "name": "汇桥 — 跨境支付平台",
        "slug": "globalbridge",
        "tone": "专业",
        "form": {
            "mode": "form",
            "product_name": "汇桥 GlobalBridge",
            "product_description": "面向跨境电商和外贸企业的全球收款与多币种结算平台，支持 30+ 币种实时汇率兑换",
            "target_users": "跨境电商运营者、外贸企业财务、独立站创业者",
            "key_selling_points": [
                "30+ 币种 T+0 到账",
                "汇率比银行低 60%",
                "PCI DSS Level 1 认证",
                "API 一键接入 Shopify/WooCommerce",
            ],
            "brand_tone": "专业",
            "competitors": ["Payoneer", "万里汇 WorldFirst", "连连国际"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "我们的产品是'汇桥 GlobalBridge'，一个面向跨境电商卖家的跨境支付和收款平台。"
                "核心优势：支持 30 多种货币实时兑换，到账速度 T+0（当天到），汇率比传统银行便宜 60%，"
                "通过了 PCI DSS Level 1 最高级别的安全认证，可以 API 一键接入 Shopify 和 WooCommerce。"
                "目标用户是做跨境电商的卖家和外贸企业财务，竞品是 Payoneer 和万里汇。"
                "品牌调性专业严谨（因为涉及钱，必须可信）。"
            ),
        },
    },
    {
        "id": 8,
        "name": "BoardX — 在线协作白板",
        "slug": "boardx",
        "tone": "极客",
        "form": {
            "mode": "form",
            "product_name": "BoardX",
            "product_description": "面向远程团队的在线协作白板，支持无限画布、实时同步、Markdown 卡片和图表绘制",
            "target_users": "产品经理、设计师、远程办公团队、技术架构讨论参与者",
            "key_selling_points": [
                "无限画布支持 1000+ 元素不卡顿",
                "Markdown 卡片直接渲染为脑图",
                "内置 Mermaid/PlantUML 图表引擎",
                "WebSocket 实时协作延迟 <50ms",
            ],
            "brand_tone": "极客",
            "competitors": ["Miro", "FigJam", "Excalidraw"],
        },
        "free": {
            "mode": "free",
            "user_idea": (
                "我们做了个在线白板工具叫 BoardX，用来替代 Miro 和 FigJam。主要卖点："
                "无限画布放 1000 多个元素也不卡（WebGL 渲染），支持用 Markdown 写卡片然后一键转成脑图，"
                "内置了 Mermaid 和 PlantUML 图表引擎（画架构图超爽），WebSocket 驱动的实时协作延迟不到 50ms。"
                "目标用户是产品经理、设计师、技术团队。调性偏极客，强调效率和开放性。"
            ),
        },
    },
]


# ========================================================================
# 测试执行器
# ========================================================================

def _check_env():
    """检查 API Key 是否配置"""
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        print("⚠️  未检测到 DEEPSEEK_API_KEY")
        print("   将使用模拟模式（不会真实调用 LLM）")
        print("   配置 .env 后重试以获取真实生成结果。\n")
        return False
    return True


def _build_agents(trace=None):
    from src.agents.celve import CelveAgent
    from src.agents.gongzhonghao import GongzhonghaoAgent
    from src.agents.zhihu import ZhihuAgent
    from src.agents.xiaohongshu import XiaohongshuAgent
    from src.agents.shenjiao import ShenjiaoAgent
    from src.agents.export import ExportAgent
    from src.utils.trace import TraceTracker

    celve_trace = trace or TraceTracker()

    return {
        "celve": CelveAgent(trace=celve_trace),
        "gongzhonghao": GongzhonghaoAgent(),
        "zhihu": ZhihuAgent(),
        "xiaohongshu": XiaohongshuAgent(),
        "shenjiao": ShenjiaoAgent(),
        "export": ExportAgent(),
    }


def _run_one_scenario(scenario: dict, mode: str, agents: dict) -> dict:
    """跑单个场景的单个模式 — 真实并行 + 全流程轨迹"""
    import asyncio
    import copy
    from concurrent.futures import ThreadPoolExecutor
    from src.orchestrator.state import ContentStage
    from src.web.server import PipelineTrace, _state_summary, PipelineStage

    payload = scenario[mode]
    base_state: ContentProjectState = {
        "input_mode": payload["mode"],
        "product_name": payload.get("product_name", ""),
        "product_description": payload.get("product_description", ""),
        "target_users": payload.get("target_users", ""),
        "key_selling_points": payload.get("key_selling_points", []),
        "brand_tone": payload.get("brand_tone", "专业"),
        "competitors": payload.get("competitors", []),
        "user_idea": payload.get("user_idea", ""),
        "image_urls": [],
        "strategy": None,
        "gzh_content": None,
        "zhihu_content": None,
        "xhs_content": None,
        "review_report": None,
        "current_stage": ContentStage.STRATEGY,
        "error_message": None,
        "ask_user": None,
        "messages": [],
        "brand_profile_id": None,
    }

    pipeline = PipelineTrace(project_id=f"test-{scenario['id']:02d}-{mode}")
    pool = ThreadPoolExecutor(max_workers=4)

    t_start = time.time()

    # Step 1: 策略
    st = pipeline.add_stage("strategy", status="started", input_summary=_state_summary(base_state))
    state = agents["celve"].run(base_state)
    st.end_ts = time.time()
    st.status = "done"
    st.output_summary = _state_summary(state)
    st.tool_calls = [
        {"tool": s.tool_id, "params": s.tool_params, "result": s.tool_result}
        for s in agents["celve"].trace.steps if s.step_type == "tool_call"
    ]

    if state.get("ask_user"):
        state["messages"] = state.get("messages", []) + [
            {"from": "user", "to": "celve", "type": "answer", "content": "请基于已有信息制定策略，无需追问。"}
        ]
        state["ask_user"] = None
        state = agents["celve"].run(state)

    strategy = state.get("strategy", "")

    # Step 2: 三路真正并行（ThreadPoolExecutor）
    state["current_stage"] = ContentStage.GENERATING

    channels = [
        ("gongzhonghao", agents["gongzhonghao"], "gzh_content"),
        ("zhihu", agents["zhihu"], "zhihu_content"),
        ("xiaohongshu", agents["xiaohongshu"], "xhs_content"),
    ]

    def _run_channel(ch_name, ch_agent, ch_key):
        st = pipeline.add_stage(ch_name, status="started")
        try:
            result = ch_agent.run(copy.deepcopy(state))
            st.end_ts = time.time()
            st.status = "done"
            st.output_summary = {"len": len(str(result.get(ch_key, "")))}
            return result
        except Exception as e:
            st.end_ts = time.time()
            st.status = "error"
            st.error = str(e)
            return state

    futures = [pool.submit(_run_channel, name, agent, key) for name, agent, key in channels]
    results = [f.result() for f in futures]

    # 合并产出
    for (name, _, key), r in zip(channels, results):
        if r.get(key):
            state[key] = r[key]
        else:
            for res in results:
                if res.get(key):
                    state[key] = res[key]
                    break

    gzh = state.get("gzh_content", "")
    zhihu = state.get("zhihu_content", "")
    xhs = state.get("xhs_content", "")

    # Step 3: 审校
    state["current_stage"] = ContentStage.REVIEW
    st = pipeline.add_stage("shenjiao", status="started")
    state = agents["shenjiao"].run(state)
    st.end_ts = time.time()
    st.status = "done"
    st.output_summary = {"len": len(str(state.get("review_report", "")))}
    review = state.get("review_report", "")

    elapsed = time.time() - t_start

    return {
        "scenario": scenario["name"],
        "mode": mode,
        "tone": scenario["tone"],
        "elapsed_sec": round(elapsed, 1),
        "strategy": strategy or "",
        "strategy_len": len(strategy) if strategy else 0,
        "gzh_content": gzh or "",
        "gzh_len": len(gzh) if gzh else 0,
        "zhihu_content": zhihu or "",
        "zhihu_len": len(zhihu) if zhihu else 0,
        "xhs_content": xhs or "",
        "xhs_len": len(xhs) if xhs else 0,
        "review_report": review or "",
        "review_len": len(review) if review else 0,
        "ask_user": state.get("ask_user"),
        "trace": agents["celve"].trace,
        "pipeline": pipeline,
    }


def _format_output(result: dict) -> str:
    """格式化输出为 Markdown"""
    lines = []
    lines.append(f"# {result['scenario']} — {result['mode']} 模式")
    lines.append(f"模式: {result['mode']} | 调性: {result['tone']} | 耗时: {result['elapsed_sec']}s")
    lines.append("")

    if result["ask_user"]:
        lines.append(f"⚠️ 策略 Agent 追问: {result['ask_user']}")
        lines.append("")

    lines.append(f"## 📋 策略 ({result['strategy_len']} 字)")
    lines.append("")
    lines.append(result["strategy"])
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append(f"## 📰 公众号 ({result['gzh_len']} 字)")
    lines.append("")
    lines.append(result["gzh_content"])
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append(f"## 💡 知乎 ({result['zhihu_len']} 字)")
    lines.append("")
    lines.append(result["zhihu_content"])
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append(f"## ✨ 小红书 ({result['xhs_len']} 字)")
    lines.append("")
    lines.append(result["xhs_content"])
    lines.append("")

    lines.append("---")
    lines.append("")

    lines.append(f"## 🔍 审校报告 ({result['review_len']} 字)")
    lines.append("")
    lines.append(result["review_report"])
    lines.append("")

    return "\n".join(lines)


def run_scenarios(indices=None, mode=None):
    """跑所有指定场景"""
    has_key = _check_env()

    scenarios = SCENARIOS
    if indices:
        scenarios = [s for s in SCENARIOS if s["id"] in indices]

    modes = [mode] if mode else ["form", "free"]

    # 输出目录
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = "mock" if not has_key else "live"
    output_dir = Path(__file__).parent / "output" / f"{ts}_{base}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'模拟' if not has_key else '真实'}模式 | {len(scenarios)} 场景 × {len(modes)} 模式")
    print(f"输出: {output_dir}\n")

    agents = _build_agents()
    summary = {"mode": base, "timestamp": ts, "total_elapsed": 0, "results": []}

    for scenario in scenarios:
        for m in modes:
            label = f"[{scenario['id']}/8] {scenario['name']} ({m})"
            print(f"{label:50s} ... ", end="", flush=True)

            try:
                result = _run_one_scenario(scenario, m, agents)
                summary["results"].append({
                    "scenario": result["scenario"],
                    "mode": result["mode"],
                    "elapsed": result["elapsed_sec"],
                    "gzh_len": result["gzh_len"],
                    "zhihu_len": result["zhihu_len"],
                    "xhs_len": result["xhs_len"],
                    "review_len": result["review_len"],
                })
                summary["total_elapsed"] += result["elapsed_sec"]

                # 保存 Markdown
                fname = f"scenario_{scenario['id']:02d}_{scenario['slug']}_{m}.md"
                content = _format_output(result)
                (output_dir / fname).write_text(content, encoding="utf-8")

                # 保存 celve ReAct trace
                if result.get("trace"):
                    tname = f"scenario_{scenario['id']:02d}_{scenario['slug']}_{m}_trace.json"
                    result["trace"].save(output_dir / tname)

                # 保存全流程 pipeline trace
                if result.get("pipeline"):
                    pname = f"scenario_{scenario['id']:02d}_{scenario['slug']}_{m}_pipeline.json"
                    result["pipeline"].save(output_dir / pname)

                # 快速统计
                print(f"OK ({result['elapsed_sec']}s | 公众号{result['gzh_len']}字 知乎{result['zhihu_len']}字 小红书{result['xhs_len']}字)")
            except Exception as e:
                print(f"❌ 失败: {e}")
                summary["results"].append({
                    "scenario": scenario["name"],
                    "mode": m,
                    "error": str(e),
                })

    # 保存汇总
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"完成! 共 {len(summary['results'])} 次生成, 总耗时 {summary['total_elapsed']:.0f}s")
    print(f"结果目录: {output_dir}")

    # 打印简要统计
    print(f"\n{'场景':<20s} {'模式':<6s} {'公众号':<8s} {'知乎':<8s} {'小红书':<8s} {'审校':<8s}")
    print("-" * 60)
    for r in summary["results"]:
        if "error" in r:
            print(f"{r['scenario']:<20s} {r['mode']:<6s} ❌ {r['error'][:30]}")
        else:
            print(f"{r['scenario']:<20s} {r['mode']:<6s} {r['gzh_len']:<8d} {r['zhihu_len']:<8d} {r['xhs_len']:<8d} {r['review_len']:<8d}")

    return summary


# ========================================================================
# 入口
# ========================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="营销内容生成能力评测")
    parser.add_argument("indices", nargs="*", type=int, help="要跑的场景编号（默认全部）")
    parser.add_argument("--mode", choices=["form", "free"], help="只跑一种模式")
    args = parser.parse_args()

    indices = args.indices if args.indices else None
    run_scenarios(indices=indices, mode=args.mode)
