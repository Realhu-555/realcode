"""GIS 沙箱脚本安全扫描 — AST 静态分析

执行前用 ast 解析脚本，命中黑名单直接拒绝，防止 LLM 生成的脚本
删除文件、访问网络、执行任意代码或读写沙箱外路径。

注意：这是防「脚本层面的常见危险模式」，不是容器级隔离。
生产环境应叠加 Docker（见 docs/GIS-引擎选型与分阶段演进.md）。
"""

import ast
import re

# import 黑名单（含 from x import y 的根模块）
FORBIDDEN_IMPORTS: frozenset[str] = frozenset({
    "os", "shutil", "subprocess", "socket", "requests", "urllib",
    "importlib", "ctypes", "multiprocessing", "threading",
    "builtins", "pickle", "marshal",
})

# 模块属性调用黑名单：base.attr
FORBIDDEN_ATTRS: dict[str, frozenset[str]] = {
    "os": frozenset({
        "remove", "unlink", "rmdir", "removedirs", "rename", "replace",
        "system", "popen", "spawn", "startfile", "kill", "chmod", "chown",
        "makedirs", "symlink", "link", "listdir", "scandir", "walk",
        "getenv", "putenv", "setenv", "unsetenv",
    }),
    "shutil": frozenset({
        "rmtree", "move", "copy", "copy2", "copytree", "remove",
        "make_archive", "unpack_archive", "disk_usage",
    }),
}

# 直接调用黑名单
FORBIDDEN_CALLS: frozenset[str] = frozenset({
    "eval", "exec", "compile", "input", "exit", "quit",
    "__import__", "breakpoint", "globals", "locals", "vars", "getattr",
})

# 绝对路径字面量（Windows 盘符 / UNC / POSIX 根路径）
_ABS_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|/|\\\\)")


def scan_script(source: str) -> list[str]:
    """扫描脚本源码，返回违规描述列表；空列表表示通过。

    Args:
        source: 待执行的 Python 脚本源码

    Returns:
        违规列表；脚本有语法错误时返回包含语法错误的单元素列表
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"脚本语法错误: {exc.msg} (line {exc.lineno})"]

    violations: list[str] = []
    for node in ast.walk(tree):
        _check_import(node, violations)
        _check_call(node, violations)
    return violations


def _check_import(node: ast.AST, violations: list[str]) -> None:
    """检查 import / from import 语句"""
    if isinstance(node, ast.Import):
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in FORBIDDEN_IMPORTS:
                violations.append(f"禁止导入模块: {alias.name}")
    elif isinstance(node, ast.ImportFrom):
        root = (node.module or "").split(".")[0]
        if root in FORBIDDEN_IMPORTS:
            violations.append(f"禁止导入模块: {node.module}")


def _check_call(node: ast.AST, violations: list[str]) -> None:
    """检查危险函数 / 属性调用、open 写模式、绝对路径字面量"""
    if not isinstance(node, ast.Call):
        return
    fn = node.func

    if isinstance(fn, ast.Name):
        if fn.id in FORBIDDEN_CALLS:
            violations.append(f"禁止调用: {fn.id}()")
        if fn.id == "open":
            mode = _call_open_mode(node)
            if mode is not None and set(mode) & {"w", "a", "x", "+"}:
                violations.append(f"禁止以写模式打开文件: open(mode={mode!r})")
            _check_abs_path_args(node, violations)
    elif isinstance(fn, ast.Attribute):
        base = _attr_base_name(fn.value)
        if base in FORBIDDEN_ATTRS and fn.attr in FORBIDDEN_ATTRS[base]:
            violations.append(f"禁止调用: {base}.{fn.attr}()")


def _call_open_mode(node: ast.Call) -> str | None:
    """提取 open() 的 mode 参数（位置或关键字），无则返回 None（默认只读）"""
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
        return node.args[1].value
    return None


def _check_abs_path_args(node: ast.Call, violations: list[str]) -> None:
    """检查 open() 的路径参数是否为绝对路径字面量"""
    for kw in node.keywords:
        if (
            kw.arg in ("file", "path", "filename")
            and isinstance(kw.value, ast.Constant)
            and isinstance(kw.value.value, str)
            and _ABS_PATH_RE.match(kw.value.value)
        ):
            violations.append(f"禁止使用绝对路径: {kw.value.value!r}")
    if (
        node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
        and _ABS_PATH_RE.match(node.args[0].value)
    ):
        violations.append(f"禁止使用绝对路径: {node.args[0].value!r}")


def _attr_base_name(value: ast.AST) -> str:
    """解析属性调用的根名字：os.remove → 'os'；a.b.remove → 'a'（非黑名单则返回 'a'）"""
    if isinstance(value, ast.Name):
        return value.id
    return ""
