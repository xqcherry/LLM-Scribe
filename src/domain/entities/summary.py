from typing import List

from pydantic import BaseModel, Field


class TopicSummary(BaseModel):
    """话题摘要。"""

    topic: str = Field(description="话题名称")
    summary: str = Field(description="话题摘要")
    participants: List[str] = Field(description="参与者列表")
    key_points: List[str] = Field(description="关键要点")


class SummaryOutput(BaseModel):
    """结构化摘要输出（供链路与应用层使用）。"""

    overall_summary: str = Field(description="整体摘要")
    topics: List[TopicSummary] = Field(description="话题列表")
    key_quotes: List[str] = Field(description="关键引用")
    participants: List[str] = Field(description="所有参与者")
    sentiment: str = Field(description="整体情感倾向：positive/neutral/negative")


class Topic(TopicSummary):
    """话题聚合视图（"""
    pass


class Summary(SummaryOutput):
    """群聊摘要的聚合根实体。"""
    pass

