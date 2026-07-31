"""State 单元测试 — ContentProjectState + ContentStage"""

import operator
import pytest

from src.orchestrator.state import ContentStage, ContentProjectState, _latest_stage
from src.orchestrator.graph import CONTENT_STAGE_LABELS, CONTENT_STAGE_ORDER


# ========================================================================
# ContentStage
# ========================================================================

class TestContentStage:
    def test_all_stages_exist(self):
        assert ContentStage.STRATEGY == "strategy"
        assert ContentStage.CONFIRMING == "confirming"
        assert ContentStage.GENERATING == "generating"
        assert ContentStage.REVIEW == "review"
        assert ContentStage.DONE == "done"
        assert ContentStage.ERROR == "error"

    def test_is_string_enum(self):
        assert ContentStage.STRATEGY.value == "strategy"
        assert isinstance(ContentStage.DONE, ContentStage)


# ========================================================================
# _latest_stage reducer
# ========================================================================

class TestLatestStageReducer:
    def test_picks_second(self):
        """Reducer 总是取第二个值——用于并行分支冲突解决"""
        assert _latest_stage(ContentStage.STRATEGY, ContentStage.DONE) == ContentStage.DONE

    def test_picks_second_any_order(self):
        assert _latest_stage(ContentStage.DONE, ContentStage.STRATEGY) == ContentStage.STRATEGY
        assert _latest_stage(ContentStage.GENERATING, ContentStage.REVIEW) == ContentStage.REVIEW


# ========================================================================
# ContentProjectState
# ========================================================================

class TestContentProjectState:
    def test_minimal_state(self):
        """最小合法状态"""
        state: ContentProjectState = {
            "input_mode": "form",
            "product_name": "Test",
            "current_stage": ContentStage.STRATEGY,
            "messages": [],
        }
        assert state["product_name"] == "Test"

    def test_full_state(self):
        """完整状态"""
        state: ContentProjectState = {
            "input_mode": "form",
            "product_name": "RAG 系统",
            "product_description": "企业级问答",
            "target_users": "CTO",
            "key_selling_points": ["卖点1", "卖点2"],
            "brand_tone": "专业",
            "competitors": ["竞品A"],
            "user_idea": "",
            "image_urls": [],
            "strategy": "策略内容",
            "gzh_content": "公众号内容",
            "zhihu_content": "知乎内容",
            "xhs_content": "小红书内容",
            "review_report": "审校报告",
            "current_stage": ContentStage.DONE,
            "error_message": None,
            "ask_user": None,
            "messages": [{"from": "test", "type": "output", "content": "done"}],
            "brand_profile_id": "brand-001",
        }
        assert state["strategy"] == "策略内容"
        assert state["current_stage"] == ContentStage.DONE

    def test_ask_user_state(self):
        """追问状态"""
        state: ContentProjectState = {
            "input_mode": "form",
            "product_name": "模糊产品",
            "current_stage": ContentStage.STRATEGY,
            "ask_user": "请问您的产品面向什么用户？",
            "messages": [],
        }
        assert state["ask_user"] is not None

    def test_messages_accumulation(self):
        """messages 使用 operator.add reducer——追加而非替换"""
        state: ContentProjectState = {
            "input_mode": "form",
            "product_name": "Test",
            "current_stage": ContentStage.STRATEGY,
            "messages": [
                {"from": "celve", "type": "question", "content": "Q1"},
                {"from": "user", "to": "celve", "type": "answer", "content": "A1"},
            ],
        }
        assert len(state["messages"]) == 2

    def test_image_urls_field(self):
        """多模态图片字段"""
        state: ContentProjectState = {
            "input_mode": "form",
            "product_name": "Test",
            "image_urls": [
                "data:image/png;base64,abc123",
                "data:image/jpeg;base64,xyz789",
            ],
            "current_stage": ContentStage.STRATEGY,
            "messages": [],
        }
        assert len(state["image_urls"]) == 2


# ========================================================================
# CONTENT_STAGE_LABELS
# ========================================================================

class TestStageLabels:
    def test_all_stages_have_labels(self):
        for stage in CONTENT_STAGE_ORDER:
            assert stage in CONTENT_STAGE_LABELS, f"缺少 {stage} 标签"
        assert CONTENT_STAGE_LABELS["done"] == "完成！"
        assert CONTENT_STAGE_LABELS["error"] == "出错了"


# ========================================================================
# llm_provider 模型映射
# ========================================================================

class TestLLMProviderModelMap:
    def test_all_content_agents_use_deepseek(self):
        from src.llm.provider import LLMProvider

        agents = ["celve", "gongzhonghao", "zhihu", "xiaohongshu", "shenjiao", "export"]
        for name in agents:
            model = LLMProvider.MODEL_MAP.get(name)
            assert model is not None, f"缺少 {name} 模型映射"
            assert "deepseek" in model, f"{name} 应该用 DeepSeek，实际: {model}"

    def test_vision_model_exists(self):
        from src.llm.provider import LLMProvider

        assert "vision" in LLMProvider.MODEL_MAP
        assert "mimo" in LLMProvider.MODEL_MAP["vision"]

    def test_chat_multimodal_signature(self):
        from src.llm.provider import LLMProvider

        llm = LLMProvider()
        assert callable(llm.chat_multimodal)
        assert hasattr(llm, "mimo_client")
