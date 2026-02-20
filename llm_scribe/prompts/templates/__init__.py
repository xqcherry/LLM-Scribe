"""提示词模板模块"""
from .summary_prompt import SummaryPromptTemplate
from .extraction_prompt import ExtractionPromptTemplate
from .compression_prompt import CompressionPromptTemplate

__all__ = ["SummaryPromptTemplate", "ExtractionPromptTemplate", "CompressionPromptTemplate"]
