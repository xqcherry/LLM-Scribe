"""提示词基础设施模块。"""

from src.infrastructure.prompts.providers.prompt_provider_impl import PromptProviderImpl
from src.infrastructure.prompts.templates.compression_prompt import CompressionPromptTemplate
from src.infrastructure.prompts.templates.extraction_prompt import ExtractionPromptTemplate
from src.infrastructure.prompts.templates.summary_prompt import SummaryPromptTemplate

__all__ = [
    "CompressionPromptTemplate",
    "ExtractionPromptTemplate",
    "SummaryPromptTemplate",
    "PromptProviderImpl",
]
