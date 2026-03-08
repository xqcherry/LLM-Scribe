from __future__ import annotations

from ....application.ports.prompt_provider_port import PromptProviderPort
from ..templates.compression_prompt import CompressionPromptTemplate
from ..templates.extraction_prompt import ExtractionPromptTemplate
from ..templates.summary_prompt import SummaryPromptTemplate


class PromptProviderImpl(PromptProviderPort):
    """Prompt 提供器实现：统一管理各类提示词模板。"""

    def get_summary_prompt(self, max_topics: int = 5) -> SummaryPromptTemplate:
        return SummaryPromptTemplate(max_topics=max_topics)

    def get_extraction_prompt(self) -> ExtractionPromptTemplate:
        return ExtractionPromptTemplate()

    def get_compression_prompt(self) -> CompressionPromptTemplate:
        return CompressionPromptTemplate()
