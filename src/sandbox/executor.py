"""本地沙箱执行器（MVP 阶段代替 Docker）"""

import shutil
import subprocess
import tempfile
from pathlib import Path


class SandboxExecutor:
    """在临时目录中执行代码，支持文件读写、命令执行和 zip 打包"""

    def __init__(self):
        self.work_dir: Path | None = None

    def create(self, project_name: str) -> Path:
        """创建临时工作目录"""
        self.work_dir = Path(tempfile.mkdtemp(prefix=f"{project_name}_"))
        return self.work_dir

    def write_file(self, relative_path: str, content: str):
        """在沙箱中写文件"""
        if not self.work_dir:
            raise RuntimeError("沙箱未初始化，请先调用 create()")
        file_path = self.work_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def read_file(self, relative_path: str) -> str:
        """读取沙箱中的文件"""
        if not self.work_dir:
            raise RuntimeError("沙箱未初始化，请先调用 create()")
        return (self.work_dir / relative_path).read_text(encoding="utf-8")

    def run_command(self, command: str, timeout: int = 60) -> tuple[str, int]:
        """在沙箱中执行命令，返回 (输出, 退出码)"""
        if not self.work_dir:
            raise RuntimeError("沙箱未初始化，请先调用 create()")
        result = subprocess.run(
            command,
            shell=True,
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout + result.stderr, result.returncode

    def file_exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        if not self.work_dir:
            return False
        return (self.work_dir / relative_path).exists()

    def list_files(self) -> list[str]:
        """列出沙箱中所有文件（相对路径）"""
        if not self.work_dir:
            return []
        return [
            p.relative_to(self.work_dir).as_posix() for p in self.work_dir.rglob("*") if p.is_file()
        ]

    def pack_zip(self, output_path: str) -> str:
        """打包沙箱内容为 zip"""
        if not self.work_dir:
            raise RuntimeError("沙箱未初始化，请先调用 create()")
        zip_base = str(Path(output_path).with_suffix(""))
        return shutil.make_archive(zip_base, "zip", self.work_dir)

    def cleanup(self):
        """清理临时目录"""
        if self.work_dir and self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)
        self.work_dir = None
