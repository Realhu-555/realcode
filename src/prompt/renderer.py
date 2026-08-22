"""Jinja2 模板渲染器

设计理念：
- 模板文件独立于代码：改 prompt 不需要改 Python
- 带文件缓存：同一模板不重复读磁盘
"""

from pathlib import Path

from jinja2 import BaseLoader, Environment


class PromptRenderer:
    """Jinja2 模板渲染器"""

    def __init__(self, template_dir: str | None = None) -> None:
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")
        self.env = Environment(
            loader=BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template_dir = Path(template_dir)
        self._cache: dict[str, str] = {}

    def load_template(self, name: str) -> str:
        """加载模板文件（带缓存）

        Args:
            name: 模板文件名（如 "celve.md"、"gzh.md"）

        Returns:
            模板原始内容
        """
        if name not in self._cache:
            path = self.template_dir / name
            if not path.exists():
                raise FileNotFoundError(f"模板文件不存在: {path}")
            self._cache[name] = path.read_text(encoding="utf-8")
        return self._cache[name]

    def render(self, template_name_or_content: str, variables: dict) -> str:
        """渲染模板

        Args:
            template_name_or_content: 模板文件名（以 .md 结尾）或直接模板内容
            variables: 模板变量（来自 PromptContext.to_template_vars()）

        Returns:
            渲染后的最终 prompt 字符串
        """
        if template_name_or_content.endswith(".md"):
            content = self.load_template(template_name_or_content)
        else:
            content = template_name_or_content

        template = self.env.from_string(content)
        return template.render(**variables)


# 全局单例渲染器
renderer = PromptRenderer()
