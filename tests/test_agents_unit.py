"""Agent 单元测试 - Mock LLM 调用，覆盖所有分支"""

from unittest.mock import MagicMock, patch

from src.orchestrator.state import create_output_artifact

# ========================================================================
# RequirementAgent 测试
# ========================================================================


class TestRequirementAgent:
    """需求分析 Agent 单元测试"""

    @patch("src.agents.requirement.LLMProvider")
    def test_run_returns_prd_when_clear_input(self, mock_llm_cls: MagicMock) -> None:
        """清晰输入直接产出 PRD"""
        from src.agents.requirement import RequirementAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = (
            "---PRD_START---\n## 产品概述\n个人博客系统\n## 核心功能\n- 文章管理\n---PRD_END---"
        )

        agent = RequirementAgent()
        state = {
            "user_idea": "做一个个人博客",
            "prd": None,
            "ask_user": None,
            "current_stage": "requirement",
            "messages": [],
        }

        result = agent.run(state)

        assert result["prd"] is not None
        assert result["ask_user"] is None
        assert result["current_stage"] == "architecture"

    @patch("src.agents.requirement.LLMProvider")
    def test_run_returns_ask_user_when_vague(self, mock_llm_cls: MagicMock) -> None:
        """模糊输入返回追问"""
        from src.agents.requirement import RequirementAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "请问您希望支持哪些功能？比如用户登录、数据导出等？"

        agent = RequirementAgent()
        state = {
            "user_idea": "做一个系统",
            "prd": None,
            "ask_user": None,
            "current_stage": "requirement",
            "messages": [],
        }

        result = agent.run(state)

        assert result["prd"] is None
        assert result["ask_user"] is not None
        assert result["current_stage"] == "requirement"

    @patch("src.agents.requirement.LLMProvider")
    def test_run_forces_prd_after_first_round(self, mock_llm_cls: MagicMock) -> None:
        """第一轮追问后强制产出 PRD"""
        from src.agents.requirement import RequirementAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "---PRD_START---\n## 产品概述\n任务管理工具\n---PRD_END---"

        agent = RequirementAgent()
        state = {
            "user_idea": "做一个任务管理工具",
            "prd": None,
            "ask_user": None,
            "current_stage": "requirement",
            "messages": [
                {
                    "from": "requirement",
                    "type": "question",
                    "content": "请问是团队用还是个人用？",
                },
                {
                    "to": "requirement",
                    "type": "answer",
                    "content": "团队用",
                },
            ],
        }

        result = agent.run(state)

        assert result["prd"] is not None
        assert result["current_stage"] == "architecture"

    @patch("src.agents.requirement.LLMProvider")
    def test_run_with_ask_user_tag_format(self, mock_llm_cls: MagicMock) -> None:
        """解析 [ASK_USER]...[/ASK_USER] 格式"""
        from src.agents.requirement import RequirementAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = (
            "请问您希望使用什么技术栈？[ASK_USER]请问您希望使用什么技术栈？[/ASK_USER]"
        )

        agent = RequirementAgent()
        state = {
            "user_idea": "做一个博客",
            "prd": None,
            "ask_user": None,
            "current_stage": "requirement",
            "messages": [],
        }

        result = agent.run(state)

        assert result["ask_user"] is not None

    @patch("src.agents.requirement.LLMProvider")
    def test_run_strips_thinking_blocks(self, mock_llm_cls: MagicMock) -> None:
        """移除 <think> 推理块"""
        from src.agents.requirement import RequirementAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "<think>这是推理过程</think>最终答案是博客系统"

        agent = RequirementAgent()
        state = {
            "user_idea": "做一个博客",
            "prd": None,
            "ask_user": None,
            "current_stage": "requirement",
            "messages": [],
        }

        result = agent.run(state)

        assert result["prd"] is not None


# ========================================================================
# ArchitectAgent 测试
# ========================================================================


class TestArchitectAgent:
    """架构师 Agent 单元测试"""

    @patch("src.agents.architect.LLMProvider")
    def test_run_returns_error_when_no_prd(self, mock_llm_cls: MagicMock) -> None:
        """缺少 PRD 时返回错误"""
        from src.agents.architect import ArchitectAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        agent = ArchitectAgent()
        state = {
            "prd": None,
            "current_stage": "architecture",
            "messages": [],
        }

        result = agent.run(state)

        assert result["error_message"] == "缺少 PRD 文档，无法进行架构设计"
        assert result["current_stage"] == "error"

    @patch("src.agents.architect.LLMProvider")
    def test_run_generates_tech_plan(self, mock_llm_cls: MagicMock) -> None:
        """正常生成技术方案"""
        from src.agents.architect import ArchitectAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "## 技术架构\n使用 FastAPI + React"

        agent = ArchitectAgent()
        state = {
            "prd": create_output_artifact(content="PRD 内容"),
            "current_stage": "architecture",
            "messages": [],
        }

        result = agent.run(state)

        assert result["tech_plan"] is not None
        assert result["current_stage"] == "backend"
        assert "tech_plan" in result


# ========================================================================
# BackendAgent 测试
# ========================================================================


class TestBackendAgent:
    """后端开发 Agent 单元测试"""

    @patch("src.agents.backend.LLMProvider")
    def test_run_returns_error_when_no_tech_plan(self, mock_llm_cls: MagicMock) -> None:
        """缺少技术方案时返回错误"""
        from src.agents.backend import BackendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        agent = BackendAgent()
        state = {
            "tech_plan": None,
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["error_message"] == "缺少技术方案，无法生成后端代码"
        assert result["current_stage"] == "error"

    @patch("src.agents.backend.LLMProvider")
    def test_run_generates_new_code(self, mock_llm_cls: MagicMock) -> None:
        """正常生成新代码"""
        from src.agents.backend import BackendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "def main():\n    return 'hello'"

        agent = BackendAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "backend_code": None,
            "bugs": None,
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["backend_code"] is not None
        assert result["backend_code"]["status"] == "draft"
        assert result["current_stage"] == "testing"

    @patch("src.agents.backend.LLMProvider")
    def test_run_fixes_bugs(self, mock_llm_cls: MagicMock) -> None:
        """修复 bug 模式"""
        from src.agents.backend import BackendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "def main():\n    return 'fixed'"

        agent = BackendAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "backend_code": create_output_artifact(content="旧代码", version=1),
            "bugs": [
                {
                    "id": "bug-1",
                    "target": "backend",
                    "test_case": "测试用例1",
                    "error": "错误信息",
                    "expected": "期望行为",
                    "root_cause": "原因",
                }
            ],
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["backend_code"]["status"] == "revised"
        assert result["backend_code"]["version"] == 2
        assert len(result["bugs"]) == 0  # bug 已移除

    @patch("src.agents.backend.LLMProvider")
    def test_run_preserves_frontend_bugs(self, mock_llm_cls: MagicMock) -> None:
        """保留非 backend 的 bug"""
        from src.agents.backend import BackendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "code"

        agent = BackendAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "backend_code": None,
            "bugs": [
                {
                    "id": "bug-frontend",
                    "target": "frontend",
                    "test_case": "前端测试",
                    "error": "错误",
                    "expected": "期望",
                    "root_cause": "原因",
                }
            ],
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state)

        assert len(result["bugs"]) == 1
        assert result["bugs"][0]["target"] == "frontend"


# ========================================================================
# FrontendAgent 测试
# ========================================================================


class TestFrontendAgent:
    """前端开发 Agent 单元测试"""

    @patch("src.agents.frontend.LLMProvider")
    def test_run_returns_error_when_no_tech_plan(self, mock_llm_cls: MagicMock) -> None:
        """缺少技术方案时返回错误"""
        from src.agents.frontend import FrontendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        agent = FrontendAgent()
        state = {
            "tech_plan": None,
            "current_stage": "frontend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["error_message"] == "缺少技术方案，无法生成前端代码"
        assert result["current_stage"] == "error"

    @patch("src.agents.frontend.LLMProvider")
    def test_run_generates_new_code(self, mock_llm_cls: MagicMock) -> None:
        """正常生成新代码"""
        from src.agents.frontend import FrontendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "export default function App() { return <div/> }"

        agent = FrontendAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "frontend_code": None,
            "bugs": None,
            "current_stage": "frontend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["frontend_code"] is not None
        assert result["frontend_code"]["status"] == "draft"
        assert result["current_stage"] == "testing"

    @patch("src.agents.frontend.LLMProvider")
    def test_run_fixes_bugs(self, mock_llm_cls: MagicMock) -> None:
        """修复 bug 模式"""
        from src.agents.frontend import FrontendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "<div>fixed</div>"

        agent = FrontendAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "frontend_code": create_output_artifact(content="旧代码", version=1),
            "bugs": [
                {
                    "id": "bug-1",
                    "target": "frontend",
                    "test_case": "测试用例1",
                    "error": "错误信息",
                    "expected": "期望行为",
                    "root_cause": "原因",
                }
            ],
            "current_stage": "frontend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["frontend_code"]["status"] == "revised"
        assert result["frontend_code"]["version"] == 2

    @patch("src.agents.frontend.LLMProvider")
    def test_run_preserves_backend_bugs(self, mock_llm_cls: MagicMock) -> None:
        """保留非 frontend 的 bug"""
        from src.agents.frontend import FrontendAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "code"

        agent = FrontendAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "frontend_code": None,
            "bugs": [
                {
                    "id": "bug-backend",
                    "target": "backend",
                    "test_case": "后端测试",
                    "error": "错误",
                    "expected": "期望",
                    "root_cause": "原因",
                }
            ],
            "current_stage": "frontend",
            "messages": [],
        }

        result = agent.run(state)

        assert len(result["bugs"]) == 1
        assert result["bugs"][0]["target"] == "backend"


# ========================================================================
# TesterAgent 测试
# ========================================================================


class TestTesterAgent:
    """测试 Agent 单元测试"""

    @patch("src.agents.tester.LLMProvider")
    def test_run_returns_error_when_no_code(self, mock_llm_cls: MagicMock) -> None:
        """没有代码时返回错误"""
        from src.agents.tester import TesterAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        agent = TesterAgent()
        state = {
            "backend_code": None,
            "frontend_code": None,
            "current_stage": "testing",
            "messages": [],
        }

        result = agent.run(state)

        assert result["error_message"] == "没有代码可供测试"
        assert result["current_stage"] == "error"

    @patch("src.agents.tester.LLMProvider")
    def test_run_with_only_backend(self, mock_llm_cls: MagicMock) -> None:
        """只有后端代码"""
        from src.agents.tester import TesterAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "测试报告：代码质量良好"

        agent = TesterAgent()
        state = {
            "backend_code": create_output_artifact(content="print('hello')"),
            "frontend_code": None,
            "tech_plan": None,
            "current_stage": "testing",
            "messages": [],
        }

        result = agent.run(state)

        assert result["test_report"] is not None
        assert result["current_stage"] == "deployment"

    @patch("src.agents.tester.LLMProvider")
    def test_run_with_both_codes(self, mock_llm_cls: MagicMock) -> None:
        """前后端代码都有"""
        from src.agents.tester import TesterAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "测试通过"

        agent = TesterAgent()
        state = {
            "backend_code": create_output_artifact(content="backend code"),
            "frontend_code": create_output_artifact(content="frontend code"),
            "tech_plan": create_output_artifact(content="tech plan"),
            "current_stage": "testing",
            "messages": [],
        }

        result = agent.run(state)

        assert result["test_report"] is not None

    @patch("src.agents.tester.LLMProvider")
    def test_run_parses_bugs_from_report(self, mock_llm_cls: MagicMock) -> None:
        """从测试报告中解析 bug"""
        from src.agents.tester import TesterAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = """
测试报告：
---BUG_START---
**target**: backend
**test_case**: 用户登录失败
**error**: 返回 500
**expected**: 返回 200
**root_cause**: 数据库连接异常
---BUG_END---
"""

        agent = TesterAgent()
        state = {
            "backend_code": create_output_artifact(content="code"),
            "frontend_code": None,
            "current_stage": "testing",
            "messages": [],
        }

        result = agent.run(state)

        assert len(result["bugs"]) == 1
        assert result["bugs"][0]["target"] == "backend"
        assert result["current_stage"] == "testing"  # 有 bug 时回到 testing

    @patch("src.agents.tester.LLMProvider")
    def test_parse_bugs_deduplicates(self, mock_llm_cls: MagicMock) -> None:
        """bug 去重"""
        from src.agents.tester import TesterAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        agent = TesterAgent()
        response = """
---BUG_START---
**target**: backend
**test_case**: 测试用例1
**error**: 错误
**expected**: 期望
**root_cause**: 原因
---BUG_END---
---BUG_START---
**target**: backend
**test_case**: 测试用例1
**error**: 错误2
**expected**: 期望2
**root_cause**: 原因2
---BUG_END---
"""

        existing_bugs = []
        result = agent._parse_bugs(response, existing_bugs)

        assert len(result) == 1  # 相同 test_case 只保留一个


# ========================================================================
# DeployerAgent 测试
# ========================================================================


class TestDeployerAgent:
    """部署 Agent 单元测试"""

    @patch("src.agents.deployer.SandboxExecutor")
    @patch("src.agents.deployer.LLMProvider")
    @patch("src.agents.deployer.shutil")
    @patch("src.agents.deployer._DOWNLOADS_DIR")
    def test_run_creates_project(
        self,
        mock_downloads: MagicMock,
        mock_shutil: MagicMock,
        mock_llm_cls: MagicMock,
        mock_sandbox_cls: MagicMock,
    ) -> None:
        """正常部署项目"""
        from src.agents.deployer import DeployerAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.chat.return_value = "# 部署说明\n1. 安装依赖\n2. 启动服务"

        mock_sandbox = MagicMock()
        mock_sandbox_cls.return_value = mock_sandbox
        mock_sandbox.pack_zip.return_value = "/tmp/project.zip"

        mock_downloads.__truediv__ = MagicMock(return_value=MagicMock())

        agent = DeployerAgent()
        state = {
            "user_idea": "做一个博客系统",
            "prd": create_output_artifact(content="PRD"),
            "tech_plan": create_output_artifact(content="技术方案"),
            "backend_code": create_output_artifact(content="backend code"),
            "frontend_code": create_output_artifact(content="frontend code"),
            "test_report": None,
            "current_stage": "deployment",
            "messages": [],
        }

        result = agent.run(state)

        assert result["current_stage"] == "done"
        assert result["zip_path"] is not None


def test_parse_files() -> None:
    """测试 _parse_files 函数"""
    from src.agents.deployer import _parse_files

    output = """
### main.py
```python
def main():
    pass
```

### utils.py
```python
def helper():
    pass
```

### requirements.txt
```
fastapi
uvicorn
```
"""

    files = _parse_files(output)

    assert "main.py" in files
    assert "utils.py" in files
    assert "requirements.txt" not in files  # 应该被跳过


def test_parse_files_skips_empty() -> None:
    """跳过空文件"""
    from src.agents.deployer import _parse_files

    output = """
### empty.py
```

```

### valid.py
```python
x = 1
```
"""

    files = _parse_files(output)

    assert "valid.py" in files
