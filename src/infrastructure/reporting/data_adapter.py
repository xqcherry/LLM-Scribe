from typing import Any, Dict

from src.domain.entities.summary_result import SummaryResult


def data_adapter(summary_result: SummaryResult) -> Dict[str, Any]:
    """将统一的 SummaryResult 转换为渲染器格式。"""

    stats = summary_result.analysis.statistics
    usage = summary_result.analysis.token_usage

    hourly_activity = stats.activity.hourly_distribution or [0] * 24
    most_active_period = "未知"
    if any(hourly_activity):
        max_hour = hourly_activity.index(max(hourly_activity))
        next_hour = (max_hour + 1) % 24
        most_active_period = f"{max_hour:02d}:00 - {next_hour:02d}:00"

    adapted_topics = [
        {
            "topic": topic.topic,
            "detail": topic.detail,
            "participants": topic.participants,
        }
        for topic in summary_result.topics
    ]

    return {
        "header": {
            "group_id": str(summary_result.context.group_id),
            "title": "群聊简报",
            "time_range": stats.time_span or f"最近 {summary_result.context.hours} 小时",
        },
        "statistics": {
            "message_count": stats.message_count,
            "participant_count": stats.participant_count,
            "most_active_period": most_active_period,
            "activity_visualization": {
                "hourly_activity": hourly_activity,
            },
        },
        "topics": adapted_topics,
        "metadata": {
            "model": "unknown",
            "total_tokens": usage.total_tokens,
            "cost": usage.estimated_cost,
        },
    }
