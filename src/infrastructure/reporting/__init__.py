"""报告基础设施模块。"""

from src.infrastructure.reporting.data_adapter import data_adapter
from src.infrastructure.reporting.generators import ReportGenerator
from src.infrastructure.reporting.html_render import HTMLRenderer
from src.infrastructure.reporting.templates import HTMLTemplates

__all__ = ["ReportGenerator", "HTMLRenderer", "HTMLTemplates", "data_adapter"]
