from __future__ import annotations

from typing import List, Union
from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """token使用统计"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0


class ActivityStatistics(BaseModel):
    """活动可视化相关统计"""

    # 0~23 点消息分布
    hourly_distribution: List[int] = Field(
        default_factory=lambda: [0] * 24,
        description="按小时统计的消息条数（0~23）",
    )


class ConversationStatistics(BaseModel):
    """会话基础统计"""

    message_count: int = 0
    participant_count: int = 0
    total_characters: int = 0
    time_span: str = ""
    duration: str = ""
    activity: ActivityStatistics = Field(default_factory=ActivityStatistics)


class ConversationAnalysisResult(BaseModel):
    """会话分析结果聚合实体"""

    group_id: Union[int, str] = 0
    trace_id: str = ""

    statistics: ConversationStatistics = Field(default_factory=ConversationStatistics)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

