"""SandboxExecutor 单元测试"""

import subprocess
from pathlib import Path

import pytest
from src.sandbox.executor import SandboxExecutor


@pytest.fixture
def sandbox():
    """创建已初始化的沙箱"""
    sb = SandboxExecutor()
    sb.create("test_project")
    yield sb
    sb.cleanup()


def test_create_creates_temp_directory():
    """create() 创建临时目录"""
    sb = SandboxExecutor()
    try:
        work_dir = sb.create("mytest")
        assert work_dir.exists()
        assert work_dir.is_dir()
        assert "mytest" in work_dir.name
    finally:
        sb.cleanup()


def test_write_and_read_file(sandbox):
    """写入文件后能正确读取"""
    sandbox.write_file("hello.txt", "Hello, World!")
    content = sandbox.read_file("hello.txt")
    assert content == "Hello, World!"


def test_write_file_creates_parent_dirs(sandbox):
    """写入嵌套路径时自动创建父目录"""
    sandbox.write_file("a/b/c/deep.txt", "nested")
    assert sandbox.file_exists("a/b/c/deep.txt")
    assert sandbox.read_file("a/b/c/deep.txt") == "nested"


def test_write_file_raises_when_not_created():
    """未调用 create() 时写文件抛异常"""
    sb = SandboxExecutor()
    with pytest.raises(RuntimeError, match="沙箱未初始化"):
        sb.write_file("test.txt", "content")


def test_read_file_raises_when_not_created():
    """未调用 create() 时读文件抛异常"""
    sb = SandboxExecutor()
    with pytest.raises(RuntimeError, match="沙箱未初始化"):
        sb.read_file("test.txt")


def test_run_command_returns_output_and_returncode(sandbox):
    """执行命令返回输出和退出码"""
    sandbox.write_file("script.py", "print('hello')")
    output, code = sandbox.run_command("python script.py")
    assert code == 0
    assert "hello" in output


def test_run_command_captures_stderr(sandbox):
    """捕获 stderr 输出"""
    output, code = sandbox.run_command("python -c \"import sys; sys.stderr.write('err_msg')\"")
    assert "err_msg" in output


def test_run_command_nonzero_exit(sandbox):
    """非零退出码"""
    output, code = sandbox.run_command('python -c "exit(1)"')
    assert code == 1


def test_run_command_timeout(sandbox):
    """超时返回错误信息"""
    output, code = sandbox.run_command('python -c "import time; time.sleep(10)"', timeout=1)
    assert code == -1
    assert "超时" in output


def test_file_exists(sandbox):
    """file_exists 正确判断"""
    assert not sandbox.file_exists("nope.txt")
    sandbox.write_file("yes.txt", "")
    assert sandbox.file_exists("yes.txt")


def test_file_exists_when_not_created():
    """未初始化时 file_exists 返回 False"""
    sb = SandboxExecutor()
    assert sb.file_exists("any.txt") is False


def test_list_files(sandbox):
    """列出所有文件"""
    sandbox.write_file("a.py", "")
    sandbox.write_file("sub/b.py", "")
    files = sandbox.list_files()
    assert set(files) == {"a.py", "sub/b.py"}


def test_list_files_when_not_created():
    """未初始化时 list_files 返回空列表"""
    sb = SandboxExecutor()
    assert sb.list_files() == []


def test_cleanup_removes_directory(sandbox):
    """cleanup() 删除临时目录"""
    work_dir = sandbox.work_dir
    assert work_dir.exists()
    sandbox.cleanup()
    assert not work_dir.exists()
    assert sandbox.work_dir is None


def test_cleanup_is_idempotent():
    """多次 cleanup 不抛异常"""
    sb = SandboxExecutor()
    sb.create("idempotent_test")
    sb.cleanup()
    sb.cleanup()  # 不会报错


def test_pack_zip(sandbox):
    """打包为 zip 文件"""
    sandbox.write_file("index.html", "<h1>Hello</h1>")
    sandbox.write_file("app.js", "console.log(1)")

    zip_path = sandbox.pack_zip("/tmp/test_output")
    zip_file = Path(zip_path)

    assert zip_file.exists()
    assert zip_file.suffix == ".zip"
    assert zip_file.stat().st_size > 0

    # 清理 zip
    zip_file.unlink(missing_ok=True)
