from typing import List

from pydantic import BaseModel, Field


class TopicSummary(BaseModel):
    """话题摘要"""

    topic: str = Field(default="", description="话题名称，突出主题内容，尽量简明扼要，控制在10字以内")
    participants: List[str] = Field(default_factory=list, description="主要参与者的用户ID列表，最多5人，按参与度排序")
    detail: str = Field(default="", description="话题详细描述，包含关键信息和结论。在描述中提及用户时，使用 [用户ID] 格式")


class SummaryOutput(BaseModel):
    """结构化摘要输出"""

    topics: List[TopicSummary] = Field(description="话题列表，根据实际聊天内容提取所有最有意义的话题")



