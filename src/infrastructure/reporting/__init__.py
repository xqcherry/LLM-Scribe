"""报告基础设施模块。"""

from .data_adapter import data_adapter
from .generators import ReportGenerator
from .html_render import HTMLRenderer
from .templates import HTMLTemplates

__all__ = ["ReportGenerator", "HTMLRenderer", "HTMLTemplates", "data_adapter"]
