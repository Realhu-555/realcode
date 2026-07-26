"""重构后补充的测试 —— 覆盖 deployer、architect、graph、template manager 的缺失分支"""

from unittest.mock import MagicMock, patch

from src.orchestrator.state import create_output_artifact

# ========================================================================
# _write_code_files 测试
# ========================================================================


class TestWriteCodeFiles:
    """_write_code_files 辅助函数的分支覆盖"""

    def test_with_file_markers(self) -> None:
        """代码包含文件标记时按文件拆分写入"""
        from src.agents.deployer import _write_code_files

        sandbox = MagicMock()
        code = (
            "### main.py\n```python\ndef main(): pass\n```\n"
            "### util.py\n```python\ndef helper(): pass\n```\n"
        )

        _write_code_files(sandbox, code, "backend", "main.py", "# placeholder\n")

        assert sandbox.write_file.call_count == 2
        sandbox.write_file.assert_any_call("backend/main.py", "def main(): pass")
        sandbox.write_file.assert_any_call("backend/util.py", "def helper(): pass")

    def test_without_file_markers(self) -> None:
        """代码无文件标记时回退为单文件写入"""
        from src.agents.deployer import _write_code_files

        sandbox = MagicMock()
        code = "print('hello')"

        _write_code_files(sandbox, code, "backend", "main.py", "# placeholder\n")

        sandbox.write_file.assert_called_once_with("backend/main.py", "print('hello')")

    def test_empty_code(self) -> None:
        """无代码时写入占位内容"""
        from src.agents.deployer import _write_code_files

        sandbox = MagicMock()

        _write_code_files(sandbox, "", "backend", "main.py", "# 后端代码暂未生成\n")

        sandbox.write_file.assert_called_once_with("backend/main.py", "# 后端代码暂未生成\n")

    def test_none_code(self) -> None:
        """None 代码时写入占位内容"""
        from src.agents.deployer import _write_code_files

        sandbox = MagicMock()

        _write_code_files(sandbox, None, "frontend", "src/App.tsx", "// 前端代码暂未生成\n")

        sandbox.write_file.assert_called_once_with(
            "frontend/src/App.tsx", "// 前端代码暂未生成\n"
        )

    def test_with_output_artifact(self) -> None:
        """传入 OutputArtifact 时正确提取内容"""
        from src.agents.deployer import _write_code_files

        sandbox = MagicMock()
        artifact = create_output_artifact(content="print('artifact')")

        _write_code_files(sandbox, artifact, "backend", "main.py", "# placeholder\n")

        sandbox.write_file.assert_called_once_with("backend/main.py", "print('artifact')")


# ========================================================================
# _write_doc_files 测试
# ========================================================================


class TestWriteDocFiles:
    """_write_doc_files 辅助函数覆盖"""

    def test_writes_all_docs(self) -> None:
        """有 PRD、tech_plan、test_report 时全部写入"""
        from src.agents.deployer import _write_doc_files

        sandbox = MagicMock()
        state = {
            "prd": create_output_artifact(content="PRD content"),
            "tech_plan": create_output_artifact(content="Tech plan content"),
            "test_report": create_output_artifact(content="Test report content"),
        }

        _write_doc_files(sandbox, state)

        assert sandbox.write_file.call_count == 3
        sandbox.write_file.assert_any_call("PRD.md", "PRD content")
        sandbox.write_file.assert_any_call("TECH_PLAN.md", "Tech plan content")
        sandbox.write_file.assert_any_call("TEST_REPORT.md", "Test report content")

    def test_skips_none_docs(self) -> None:
        """值为 None 时不写入"""
        from src.agents.deployer import _write_doc_files

        sandbox = MagicMock()
        state = {
            "prd": None,
            "tech_plan": create_output_artifact(content="plan"),
            "test_report": None,
        }

        _write_doc_files(sandbox, state)

        assert sandbox.write_file.call_count == 1
        sandbox.write_file.assert_called_once_with("TECH_PLAN.md", "plan")

    def test_skips_empty_state(self) -> None:
        """空 state 不写入任何文件"""
        from src.agents.deployer import _write_doc_files

        sandbox = MagicMock()
        state = {}

        _write_doc_files(sandbox, state)

        sandbox.write_file.assert_not_called()


# ========================================================================
# DeployerAgent 完整分支测试
# ========================================================================


class TestDeployerAgentBranches:
    """DeployerAgent 各分支覆盖"""

    @patch("src.agents.deployer.SandboxExecutor")
    @patch("src.agents.deployer.LLMProvider")
    @patch("src.agents.deployer.shutil")
    @patch("src.agents.deployer._DOWNLOADS_DIR")
    def test_run_with_no_code(
        self,
        mock_downloads: MagicMock,
        mock_shutil: MagicMock,
        mock_llm_cls: MagicMock,
        mock_sandbox_cls: MagicMock,
    ) -> None:
        """无前后端代码时仍能正常部署"""
        from src.agents.deployer import DeployerAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "# 部署说明"

        mock_sandbox = MagicMock()
        mock_sandbox_cls.return_value = mock_sandbox
        mock_sandbox.pack_zip.return_value = "/tmp/out.zip"

        mock_downloads.__truediv__ = MagicMock(return_value=MagicMock())

        agent = DeployerAgent()
        state = {
            "user_idea": "空项目",
            "prd": None,
            "tech_plan": None,
            "backend_code": None,
            "frontend_code": None,
            "test_report": None,
            "current_stage": "deployment",
            "messages": [],
        }

        result = agent.run(state)

        assert result["current_stage"] == "done"
        assert result["zip_path"] is not None

    @patch("src.agents.deployer.SandboxExecutor")
    @patch("src.agents.deployer.LLMProvider")
    @patch("src.agents.deployer.shutil")
    @patch("src.agents.deployer._DOWNLOADS_DIR")
    def test_run_with_multi_file_code(
        self,
        mock_downloads: MagicMock,
        mock_shutil: MagicMock,
        mock_llm_cls: MagicMock,
        mock_sandbox_cls: MagicMock,
    ) -> None:
        """代码包含多文件标记时按文件拆分"""
        from src.agents.deployer import DeployerAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "# 部署说明"

        mock_sandbox = MagicMock()
        mock_sandbox_cls.return_value = mock_sandbox
        mock_sandbox.pack_zip.return_value = "/tmp/out.zip"

        mock_downloads.__truediv__ = MagicMock(return_value=MagicMock())

        backend_code = (
            "### main.py\n```python\napp = {}\n```\n"
            "### routes.py\n```python\nroutes = []\n```\n"
        )
        frontend_code = (
            "### src/App.tsx\n```tsx\nexport default () => <div/>\n```\n"
            "### src/api.ts\n```ts\nexport const api = {};\n```\n"
        )

        agent = DeployerAgent()
        state = {
            "user_idea": "多文件项目",
            "prd": create_output_artifact(content="PRD"),
            "tech_plan": create_output_artifact(content="plan"),
            "backend_code": create_output_artifact(content=backend_code),
            "frontend_code": create_output_artifact(content=frontend_code),
            "test_report": create_output_artifact(content="report"),
            "current_stage": "deployment",
            "messages": [],
        }

        result = agent.run(state)

        assert result["current_stage"] == "done"
        # 验证多文件拆分写入（backend 2 files + frontend 2 files + 3 docs + deploy doc = 8）
        assert mock_sandbox.write_file.call_count == 8


# ========================================================================
# ArchitectAgent 页面结构提取测试
# ========================================================================


class TestArchitectPageExtraction:
    """ArchitectAgent 从 PRD 提取页面结构的分支覆盖"""

    @patch("src.agents.architect.LLMProvider")
    @patch("src.agents.architect.get_memory_context", return_value="")
    def test_pages_extracted_from_prd(
        self,
        mock_memory_ctx: MagicMock,
        mock_llm_cls: MagicMock,
    ) -> None:
        """PRD 含页面结构时正确提取 pages"""
        from src.agents.architect import ArchitectAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 技术架构\n后端 FastAPI"

        prd_content = (
            "---PRD_START---\n"
            "## 产品概述\n博客系统\n"
            "## 页面结构\n"
            "- **首页**\n"
            "  - 文章列表\n"
            "  - 搜索框\n"
            "- **文章详情页**\n"
            "  - 文章内容\n"
            "  - 评论区\n"
            "---PRD_END---"
        )

        agent = ArchitectAgent()
        state = {
            "prd": create_output_artifact(content=prd_content),
            "current_stage": "architecture",
            "messages": [],
        }

        result = agent.run(state)

        assert "pages" in result
        pages = result["pages"]
        assert len(pages) == 2
        assert pages[0]["name"] == "首页"
        assert "文章列表" in pages[0]["items"]
        assert pages[1]["name"] == "文章详情页"

    @patch("src.agents.architect.LLMProvider")
    @patch("src.agents.architect.get_memory_context", return_value="已有记忆上下文")
    def test_memory_context_injected(
        self,
        mock_memory_ctx: MagicMock,
        mock_llm_cls: MagicMock,
    ) -> None:
        """有记忆上下文时注入到 system_prompt"""
        from src.agents.architect import ArchitectAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "技术方案"

        agent = ArchitectAgent()
        state = {
            "prd": create_output_artifact(content="PRD"),
            "current_stage": "architecture",
            "messages": [],
        }

        agent.run(state)

        # 验证 LLM 被调用，且 system_prompt 包含记忆上下文
        call_args = mock_llm.chat.call_args
        messages = call_args[0][0]
        system_msg = messages[0]["content"]
        assert "已有记忆上下文" in system_msg

    @patch("src.agents.architect.LLMProvider")
    @patch("src.agents.architect.get_memory_context", return_value="")
    def test_no_pages_in_prd(
        self,
        mock_memory_ctx: MagicMock,
        mock_llm_cls: MagicMock,
    ) -> None:
        """PRD 无页面结构时 pages 为空列表"""
        from src.agents.architect import ArchitectAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "技术方案"

        prd_content = "---PRD_START---\n## 产品概述\n博客系统\n---PRD_END---"

        agent = ArchitectAgent()
        state = {
            "prd": create_output_artifact(content=prd_content),
            "current_stage": "architecture",
            "messages": [],
        }

        result = agent.run(state)

        assert result["pages"] == []


# ========================================================================
# _route_after_tester 测试
# ========================================================================


class TestRouteAfterTester:
    """graph._route_after_tester 各分支覆盖"""

    def test_no_bugs_continue(self) -> None:
        """无 bug 时继续"""
        from src.orchestrator.graph import _route_after_tester

        state = {"bugs": None}
        assert _route_after_tester(state) == "continue"

    def test_empty_bugs_continue(self) -> None:
        """空 bug 列表继续"""
        from src.orchestrator.graph import _route_after_tester

        state = {"bugs": []}
        assert _route_after_tester(state) == "continue"

    def test_max_rounds_exceeded(self) -> None:
        """超过最大轮次返回 error"""
        from src.orchestrator.graph import _route_after_tester

        state = {"bugs": [{"round": 5, "target": "backend"}]}
        assert _route_after_tester(state) == "error"

    def test_rollback_backend(self) -> None:
        """backend bug 回退到 backend"""
        from src.orchestrator.graph import _route_after_tester

        state = {"bugs": [{"round": 1, "target": "backend"}]}
        assert _route_after_tester(state) == "rollback_backend"

    def test_rollback_frontend(self) -> None:
        """frontend bug 回退到 frontend"""
        from src.orchestrator.graph import _route_after_tester

        state = {"bugs": [{"round": 1, "target": "frontend"}]}
        assert _route_after_tester(state) == "rollback_frontend"

    def test_both_targets_prefers_backend(self) -> None:
        """同时有 backend 和 frontend bug 时优先回退 backend"""
        from src.orchestrator.graph import _route_after_tester

        state = {
            "bugs": [
                {"round": 1, "target": "backend"},
                {"round": 1, "target": "frontend"},
            ]
        }
        assert _route_after_tester(state) == "rollback_backend"

    def test_unknown_target_skipped(self) -> None:
        """未知 target 被跳过，有效 target 为空时继续"""
        from src.orchestrator.graph import _route_after_tester

        state = {"bugs": [{"round": 1, "target": "unknown"}]}
        assert _route_after_tester(state) == "continue"

    def test_missing_target_key(self) -> None:
        """缺少 target key 时跳过该 bug"""
        from src.orchestrator.graph import _route_after_tester

        state = {"bugs": [{"round": 1}]}
        assert _route_after_tester(state) == "continue"


# ========================================================================
# PrdTemplate 渲染分支测试
# ========================================================================


class TestPrdTemplateRendering:
    """PrdTemplate.render() 各分支覆盖"""

    def test_render_with_intro_and_rules_and_postscript(self) -> None:
        """包含 intro、rules、postscript 的完整渲染"""
        from src.llm.templates.manager import PrdSection, PrdTemplate

        template = PrdTemplate(
            name="test",
            description="测试模板",
            sections=[PrdSection(name="功能", description="功能描述", format_hint="- 列表")],
            intro="这是开头说明",
            rules=["规则一", "规则二"],
            postscript="这是结尾补充",
        )

        result = template.render()

        assert "这是开头说明" in result
        assert "## 功能" in result
        assert "功能描述" in result
        assert "- 列表" in result
        assert "---PRD_START---" in result
        assert "---PRD_END---" in result
        assert "规则一" in result
        assert "规则二" in result
        assert "这是结尾补充" in result

    def test_render_minimal_template(self) -> None:
        """无 intro、rules、postscript 的最小模板"""
        from src.llm.templates.manager import PrdSection, PrdTemplate

        template = PrdTemplate(
            name="minimal",
            description="最小模板",
            sections=[PrdSection(name="概述", description="")],
        )

        result = template.render()

        assert "## 概述" in result
        assert "---PRD_START---" in result
        assert "---PRD_END---" in result
        # 不应包含 intro/rules/postscript
        assert "铁律" not in result

    def test_render_section_without_format_hint(self) -> None:
        """章节无 format_hint 时不输出格式提示"""
        from src.llm.templates.manager import PrdSection, PrdTemplate

        template = PrdTemplate(
            name="no-hint",
            description="无提示模板",
            sections=[PrdSection(name="概述", description="一句话描述", format_hint="")],
        )

        result = template.render()

        assert "## 概述" in result
        assert "一句话描述" in result

    def test_list_templates(self) -> None:
        """list_templates 返回所有内置模板信息"""
        from src.llm.templates.manager import list_templates

        templates = list_templates()
        names = [t["name"] for t in templates]

        assert "default" in names
        assert "ecommerce" in names
        assert "tool" in names

    def test_get_template_default(self) -> None:
        """获取不存在的模板时返回默认模板"""
        from src.llm.templates.manager import get_template

        template = get_template("nonexistent")
        assert template.name == "default"

    def test_get_template_by_name(self) -> None:
        """按名称获取模板"""
        from src.llm.templates.manager import get_template

        template = get_template("ecommerce")
        assert template.name == "ecommerce"
        assert template.description == "电商类应用 PRD 模板"
