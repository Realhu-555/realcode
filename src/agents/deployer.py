"""部署 Agent"""
import os
import re
import shutil
from pathlib import Path
from src.agents.base import BaseAgent
from src.llm.provider import LLMProvider
from src.llm.prompts.deployer import DEPLOYER_PROMPT
from src.sandbox.executor import SandboxExecutor


def _parse_backend_files(backend_output: str) -> dict[str, str]:
    """解析后端 Agent 的多文件输出，拆分为 {文件路径: 内容}。

    格式同前端：### path/file\n```language\ncode\n```
    """
    files: dict[str, str] = {}
    pattern = re.compile(
        r'###\s+([^\n]+?)\s*\n+```(?:[^\n]*?)\n(.*?)```',
        re.DOTALL,
    )
    matches = pattern.findall(backend_output)
    for filepath, code in matches:
        filepath = filepath.strip().lstrip('`').strip()
        code = code.strip()
        if not code or not filepath:
            continue
        if filepath in ('requirements.txt',):
            continue  # 不单独生成 requirements.txt
        files[filepath] = code
    return files


def _parse_frontend_files(frontend_output: str) -> dict[str, str]:
    """解析前端 Agent 的多文件输出，拆分为 {文件路径: 内容} 字典。

    支持两种格式：
    1. ### src/components/Foo.tsx\\n```tsx\\n...\\n```
    2. ### path/to/file.ext\\n```language\\n...\\n```

    会跳过 package.json / tsconfig.json 等根目录文件（暂不生成）。
    如果没有解析到任何文件（比如 Agent 把所有代码塞 app.tsx），返回空字典。
    """
    files: dict[str, str] = {}

    # 匹配: ### 可选路径的 文件名\n```可选语言\n代码\n```
    pattern = re.compile(
        r'###\s+([^\n]+?)\s*\n+```(?:[^\n]*?)\n(.*?)```',
        re.DOTALL,
    )

    matches = pattern.findall(frontend_output)
    for filepath, code in matches:
        filepath = filepath.strip().lstrip('`').strip()
        code = code.strip()
        if not code or not filepath:
            continue
        files[filepath] = code

    return files


# 持久化输出目录（Web 可访问）
_DOWNLOADS_DIR = Path(__file__).parent.parent / "web" / "static" / "downloads"


class DeployerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="deployer", system_prompt=DEPLOYER_PROMPT)
        self.llm = LLMProvider()

    def run(self, state: dict) -> dict:
        project_name = state.get("user_idea", "project")[:20].replace(" ", "_")
        sandbox = SandboxExecutor()
        work_dir = sandbox.create(project_name)

        try:
            # 写入后端代码 —— 按文件标记拆分
            backend_code = state.get("backend_code", "")
            if backend_code:
                files = _parse_backend_files(backend_code)
                if not files:
                    sandbox.write_file("backend/main.py", backend_code)
                else:
                    for filepath, content in files.items():
                        sandbox.write_file(f"backend/{filepath}", content)
            else:
                sandbox.write_file("backend/main.py", "# 后端代码暂未生成\n")

            # 写入前端代码 —— 按文件标记拆分，不再全塞 App.tsx
            frontend_code = state.get("frontend_code", "")
            if frontend_code:
                files = _parse_frontend_files(frontend_code)
                if not files:
                    # 解析失败时回退到旧行为（全当 App.tsx）
                    sandbox.write_file("frontend/src/App.tsx", frontend_code)
                else:
                    for filepath, content in files.items():
                        full_path = f"frontend/{filepath}"
                        sandbox.write_file(full_path, content)
            else:
                sandbox.write_file("frontend/src/App.tsx", "// 前端代码暂未生成\n")

            # 写入 PRD 和技术方案
            if state.get("prd"):
                sandbox.write_file("PRD.md", state["prd"])
            if state.get("tech_plan"):
                sandbox.write_file("TECH_PLAN.md", state["tech_plan"])
            if state.get("test_report"):
                sandbox.write_file("TEST_REPORT.md", state["test_report"])

            # 生成部署文档
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"项目名：{project_name}\n请生成部署说明。"},
            ]
            deploy_doc = self.llm.chat(messages, agent_type="deployer")
            sandbox.write_file("DEPLOY.md", deploy_doc)

            # 打包 zip 到持久化目录
            _DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
            safe_name = project_name.replace("\\", "_").replace("/", "_")
            zip_name = f"{safe_name}.zip"
            dest_path = _DOWNLOADS_DIR / zip_name

            # 先用沙箱打包，再复制到持久化目录
            tmp_zip = sandbox.pack_zip(
                os.path.join(str(work_dir.parent), f"{project_name}_output")
            )
            shutil.copy2(tmp_zip, dest_path)

            return {
                **state,
                "deploy_doc": deploy_doc,
                "zip_path": zip_name,
                "current_stage": "done",
                "messages": state.get("messages", []) + [{
                    "from": "deployer",
                    "type": "output",
                    "content": f"项目已打包: {zip_name}",
                }],
            }
        finally:
            sandbox.cleanup()
