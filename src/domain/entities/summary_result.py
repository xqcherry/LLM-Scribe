from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from .analysis import ConversationAnalysisResult
from .summary import TopicSummary


class SummaryContext(BaseModel):
    """摘要请求上下文。"""

    group_id: int
    hours: int


class SummaryResult(BaseModel):
    """应用层统一摘要结果，避免重复字段与胶水式结构。"""

    context: SummaryContext
    summary_text: str = ""
    topics: List[TopicSummary] = Field(default_factory=list)
    analysis: ConversationAnalysisResult = Field(default_factory=ConversationAnalysisResult)
    nickname_map: Dict[str, str] = Field(default_factory=dict)
