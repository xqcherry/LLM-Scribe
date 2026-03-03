"""
摘要相关领域实体。

在领域层直接定义摘要结构，避免依赖 core 层实现。
"""

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
    """话题聚合视图（语义别名）。"""

    pass


class Summary(SummaryOutput):
    """群聊摘要的聚合根实体（语义别名）。"""

    pass

