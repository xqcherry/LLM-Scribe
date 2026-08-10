import asyncio
import os
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

DEFAULT_TEMPLATE = "default"


class HTMLTemplates:
    """HTML模板管理类：负责加载与数据注入"""

    def __init__(self, template_name: str = DEFAULT_TEMPLATE):
        self.template_name = template_name

        # 1. 获取基础路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_templates_path = os.path.join(current_dir, "templates")

        # 2. 确定最终使用的模板目录，缺失则回退到 default
        target_path = os.path.join(self.base_templates_path, template_name)
        if not os.path.exists(target_path):
            logger.warning(f"指定模板 '{template_name}' 不存在，回退至 {DEFAULT_TEMPLATE}")
            self.template_dir = os.path.join(self.base_templates_path, DEFAULT_TEMPLATE)
        else:
            self.template_dir = target_path

        # 3. 配置 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        logger.debug(f"HTMLTemplates 初始化成功，当前模板目录: {self.template_dir}")

    async def render_async(self, template_file: str, **kwargs: Any) -> str:
        """异步渲染包装"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                self._render_sync,
                template_file,
                kwargs
            )
        except Exception as e:
            logger.error(f"渲染失败: {e}")
            return ""

    def _render_sync(self, template_file: str, data: Dict[str, Any]) -> str:
        """同步渲染核心"""
        template = self.env.get_template(template_file)
        return template.render(**data)

    def get_template_path(self, filename: str) -> str:
        """获取模板内文件的绝对路径"""
        if isinstance(self.env.loader, FileSystemLoader):
            return os.path.join(self.env.loader.searchpath[0], filename)
        return os.path.join(self.template_dir, filename)
