"""新 Agent 单元测试 — celve / gongzhonghao / zhihu / xiaohongshu / shenjiao / export"""

from unittest.mock import MagicMock, patch

import pytest


# ========================================================================
# CelveAgent（策略 Agent）
# ========================================================================

class TestCelveAgent:
    @patch("src.agents.celve.LLMProvider")
    def test_run_returns_strategy(self, mock_llm_cls: MagicMock, base_content_state):
        """正常产出策略"""
        from src.agents.celve import CelveAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 内容策略\n\n### 目标用户画像\n技术团队负责人\n\n### 各渠道策略\n- 公众号：深度长文\n- 知乎：专业回答\n- 小红书：种草笔记"

        agent = CelveAgent()
        result = agent.run(base_content_state)

        assert result["strategy"] is not None
        assert result["ask_user"] is None
        assert result["current_stage"] == "confirming"

    @patch("src.agents.celve.LLMProvider")
    def test_run_returns_ask_user(self, mock_llm_cls: MagicMock, base_content_state):
        """信息不足时追问"""
        from src.agents.celve import CelveAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "请问您的产品具体面向哪些用户群体？"

        agent = CelveAgent()
        result = agent.run(base_content_state)

        assert result["strategy"] is None
        assert result["ask_user"] is not None
        assert result["current_stage"] == "strategy"

    @patch("src.agents.celve.LLMProvider")
    def test_run_ask_user_tag_format(self, mock_llm_cls: MagicMock, base_content_state):
        """解析 [ASK_USER] 标签"""
        from src.agents.celve import CelveAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "[ASK_USER]请问您的产品定价策略是什么？[/ASK_USER]"

        agent = CelveAgent()
        result = agent.run(base_content_state)

        assert result["ask_user"] == "请问您的产品定价策略是什么？"

    @patch("src.agents.celve.LLMProvider")
    def test_run_forces_strategy_after_round(self, mock_llm_cls: MagicMock, base_content_state):
        """追问一轮后强制产出策略"""
        from src.agents.celve import CelveAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 内容策略\n\n强制产出。"

        agent = CelveAgent()
        state = {
            **base_content_state,
            "messages": [
                {"from": "celve", "type": "question", "content": "请问您是什么产品？"},
                {"to": "celve", "type": "answer", "content": "RAG 问答系统"},
            ],
        }
        result = agent.run(state)

        assert result["strategy"] is not None
        assert result["ask_user"] is None

    @patch("src.agents.celve.LLMProvider")
    def test_run_with_free_mode(self, mock_llm_cls: MagicMock, base_content_state):
        """自由模式输入"""
        from src.agents.celve import CelveAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 策略\n\n自由模式的策略。"

        agent = CelveAgent()
        state = {
            **base_content_state,
            "input_mode": "free",
            "user_idea": "我要推广一个开源 RAG 项目",
        }
        result = agent.run(state)

        assert result["strategy"] is not None

    @patch("src.agents.celve.LLMProvider")
    def test_run_detects_short_question_as_ask(self, mock_llm_cls: MagicMock, base_content_state):
        """短文本+问号 → 判为追问"""
        from src.agents.celve import CelveAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "请问您想要推广到哪些平台呢？"

        agent = CelveAgent()
        result = agent.run(base_content_state)

        assert result["ask_user"] is not None

    @patch("src.agents.celve.LLMProvider")
    def test_run_with_image_urls(self, mock_llm_cls: MagicMock, base_content_state):
        """带图片上传"""
        from src.agents.celve import CelveAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 策略\n\n基于文字信息。"

        agent = CelveAgent()
        state = {
            **base_content_state,
            "image_urls": [],  # 空列表，不触发视觉调用
        }
        result = agent.run(state)

        assert result["strategy"] is not None


# ========================================================================
# GongzhonghaoAgent（公众号 Agent）
# ========================================================================

class TestGongzhonghaoAgent:
    @patch("src.agents.gongzhonghao.LLMProvider")
    def test_run_generates_content(self, mock_llm_cls: MagicMock, base_state_after_strategy):
        """正常生成公众号长文"""
        from src.agents.gongzhonghao import GongzhonghaoAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## RAG 技术选型指南\n\n### 为什么企业需要自己的知识库\n\n这是内容..."

        agent = GongzhonghaoAgent()
        result = agent.run(base_state_after_strategy)

        assert result["gzh_content"] is not None
        assert len(result["gzh_content"]) > 10
        assert any(msg["from"] == "gongzhonghao" for msg in result.get("messages", []))

    @patch("src.agents.gongzhonghao.LLMProvider")
    def test_run_without_strategy(self, mock_llm_cls: MagicMock, base_content_state):
        """策略为空也能生成（模板中 strategy 为空字符串）"""
        from src.agents.gongzhonghao import GongzhonghaoAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "# 产品介绍\n\n大概内容。"

        agent = GongzhonghaoAgent()
        result = agent.run(base_content_state)

        assert result["gzh_content"] is not None

    @patch("src.agents.gongzhonghao.LLMProvider")
    def test_run_output_length(self, mock_llm_cls: MagicMock, base_state_after_strategy):
        """生成内容应有一定长度"""
        from src.agents.gongzhonghao import GongzhonghaoAgent

        long_content = "# " + "标题\n\n" + "正文段落。\n\n" * 30
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = long_content

        agent = GongzhonghaoAgent()
        result = agent.run(base_state_after_strategy)

        assert len(result["gzh_content"]) > 50


# ========================================================================
# ZhihuAgent（知乎 Agent）
# ========================================================================

class TestZhihuAgent:
    @patch("src.agents.zhihu.LLMProvider")
    def test_run_generates_content(self, mock_llm_cls: MagicMock, base_state_after_strategy):
        """正常生成知乎回答"""
        from src.agents.zhihu import ZhihuAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 问：自建 RAG 和开源方案怎么选？\n\n**一句话回答**：差在数据安全和定制化上。"

        agent = ZhihuAgent()
        result = agent.run(base_state_after_strategy)

        assert result["zhihu_content"] is not None
        assert any(msg["from"] == "zhihu" for msg in result.get("messages", []))

    @patch("src.agents.zhihu.LLMProvider")
    def test_run_has_question_format(self, mock_llm_cls: MagicMock, base_state_after_strategy):
        """知乎回答应包含问答风格"""
        from src.agents.zhihu import ZhihuAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 问：如何选择？\n\n这是一个好问题。回答内容..."

        agent = ZhihuAgent()
        result = agent.run(base_state_after_strategy)

        assert result["zhihu_content"] is not None


# ========================================================================
# XiaohongshuAgent（小红书 Agent）
# ========================================================================

class TestXiaohongshuAgent:
    @patch("src.agents.xiaohongshu.LLMProvider")
    def test_run_generates_content(self, mock_llm_cls: MagicMock, base_state_after_strategy):
        """正常生成小红书笔记"""
        from src.agents.xiaohongshu import XiaohongshuAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "# 💡 打工人的第二个大脑！\n\n姐妹们，今天分享一个团队效率工具。"

        agent = XiaohongshuAgent()
        result = agent.run(base_state_after_strategy)

        assert result["xhs_content"] is not None
        assert any(msg["from"] == "xiaohongshu" for msg in result.get("messages", []))

    @patch("src.agents.xiaohongshu.LLMProvider")
    def test_run_with_light_tone(self, mock_llm_cls: MagicMock):
        """轻松品牌调性"""
        from src.agents.xiaohongshu import XiaohongshuAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "# 😍 发现了好东西\n\n太喜欢了！"

        state = {
            "product_name": "可爱产品",
            "product_description": "一个有趣的东西",
            "target_users": "年轻人",
            "key_selling_points": ["颜值高", "好用"],
            "brand_tone": "轻松",
            "strategy": "种草方向",
            "messages": [],
            "gzh_content": None,
            "zhihu_content": None,
            "xhs_content": None,
        }
        agent = XiaohongshuAgent()
        result = agent.run(state)

        assert result["xhs_content"] is not None


# ========================================================================
# ShenjiaoAgent（审校 Agent）
# ========================================================================

class TestShenjiaoAgent:
    @patch("src.agents.shenjiao.LLMProvider")
    def test_run_generates_report(self, mock_llm_cls: MagicMock, base_state_after_generation):
        """正常生成审校报告"""
        from src.agents.shenjiao import ShenjiaoAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = (
            "## 审校报告\n\n### 1. 品牌调性一致 ✅ 通过\n\n"
            "### 2. 核心卖点覆盖 ✅ 通过\n\n"
            "## 整体评级：良好"
        )

        agent = ShenjiaoAgent()
        result = agent.run(base_state_after_generation)

        assert result["review_report"] is not None
        assert result["current_stage"] == "done"
        assert any(msg["from"] == "shenjiao" for msg in result.get("messages", []))

    @patch("src.agents.shenjiao.LLMProvider")
    def test_run_with_partial_content(self, mock_llm_cls: MagicMock, base_state_after_strategy):
        """只有部分渠道内容时审校"""
        from src.agents.shenjiao import ShenjiaoAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 审校报告\n\n只有一篇内容，无法全面对比。"

        state = {
            **base_state_after_strategy,
            "gzh_content": "一篇内容",
            "zhihu_content": None,
            "xhs_content": None,
        }
        agent = ShenjiaoAgent()
        result = agent.run(state)

        assert result["review_report"] is not None

    @patch("src.agents.shenjiao.LLMProvider")
    def test_run_review_includes_all_checks(self, mock_llm_cls: MagicMock, base_state_after_generation):
        """审校报告应包含五项检查"""
        from src.agents.shenjiao import ShenjiaoAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = (
            "### 1. 品牌调性一致 ✅\n"
            "### 2. 核心卖点覆盖 ✅\n"
            "### 3. 目标用户匹配 ✅\n"
            "### 4. 事实准确性 ✅\n"
            "### 5. 渠道适配性 ✅\n"
            "## 整体评级：优秀"
        )

        agent = ShenjiaoAgent()
        result = agent.run(base_state_after_generation)

        assert result["current_stage"] == "done"


# ========================================================================
# ExportAgent（导出 Agent）
# ========================================================================

class TestExportAgent:
    def test_run_exports_markdown(self, base_state_after_generation):
        """导出完整 Markdown"""
        from src.agents.export import ExportAgent

        state = {
            **base_state_after_generation,
            "review_report": "## 审校报告\n\n所有内容合格。",
        }

        agent = ExportAgent()
        result = agent.run(state)

        messages = result.get("messages", [])
        export_msg = [m for m in messages if m.get("from") == "export"]
        assert len(export_msg) == 1

        content = export_msg[0]["content"]
        assert "RAG 智能问答系统" in content
        assert "公众号" in content
        assert "知乎" in content
        assert "小红书" in content
        assert "审校报告" in content
        assert "素宣" in content

    def test_run_with_missing_content(self, base_state_after_strategy):
        """部分内容缺失时不报错"""
        from src.agents.export import ExportAgent

        agent = ExportAgent()
        result = agent.run(base_state_after_strategy)

        messages = result.get("messages", [])
        export_msg = [m for m in messages if m.get("from") == "export"]
        assert len(export_msg) == 1

        # 缺失的内容不应出现在导出中
        content = export_msg[0]["content"]
        assert "审校报告" not in content  # 没有 review_report

    def test_run_empty_state(self, base_content_state):
        """空状态也能导出"""
        from src.agents.export import ExportAgent

        agent = ExportAgent()
        result = agent.run(base_content_state)

        messages = result.get("messages", [])
        export_msg = [m for m in messages if m.get("from") == "export"]
        assert len(export_msg) == 1
        assert len(export_msg[0]["content"]) > 0

    def test_run_export_is_idempotent(self, base_state_after_generation):
        """导出不修改原始内容"""
        from src.agents.export import ExportAgent

        agent = ExportAgent()
        result = agent.run(base_state_after_generation)

        assert result["gzh_content"] == base_state_after_generation["gzh_content"]
        assert result["zhihu_content"] == base_state_after_generation["zhihu_content"]
        assert result["xhs_content"] == base_state_after_generation["xhs_content"]
