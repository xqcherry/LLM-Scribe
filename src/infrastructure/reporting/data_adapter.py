from typing import Dict, Any


def data_adapter(
        summary_result: Dict[str,Any],
        group_id: str,
) -> Dict[str,Any]:
    """数据适配器：将 LLM-Scribe 的数据结构转换为渲染器格式
    Args:
        summary_result: {
            "summary_text": str,
            "topics": List[TopicSummary],
            "analysis": ConversationAnalysisResult,
            "metadata": Dict
        }
        group_id : 目标群组的唯一识别 ID
    """
    metadata = summary_result.get("metadata", {})
    analysis = summary_result.get("analysis")

    # 适配话题格式
    raw_topics = summary_result.get("topics", [])
    adapted_topics = []
    for t in raw_topics:
        adapted_topics.append({
            "topic": t.get("event", "未命名话题"),
            "detail": t.get("summary", ""),
            "contributors": t.get("participants", []),
            "contributor_ids": t.get("participants", []),
        })

    # 统计适配
    stats = getattr(analysis, "statistics", None)
    usage = getattr(analysis, "token_usage", None)

    # 24h分布适配
    hourly_activity = [0] * 24
    most_active_period = "未知"

    if stats and stats.activity:
        dist = stats.activity.hourly_distribution
        if isinstance(dist, list):
            hourly_activity = dist
            if any(hourly_activity):
                max_hour = hourly_activity.index(max(hourly_activity))
                next_hour = (max_hour + 1) % 24
                most_active_period = f"{max_hour:02d}:00 - {next_hour:02d}:00"

    # 构建渲染数据
    render_data = {
        "header": {
            "group_id": str(group_id),
            "title": "群聊简报",
            "time_range": getattr(stats, "time_span", "24小时内")
        },
        "statistics": {
            "message_count": getattr(stats, "message_count", 0),
            "participant_count": getattr(stats, "participant_count", 0),
            "most_active_period": most_active_period,
            "activity_visualization": {
                "hourly_activity": hourly_activity
            }
        },
        "topics": adapted_topics,
        "metadata": {
            "model": metadata.get("model", "unknown"),
            "total_tokens": getattr(usage, "total_tokens", 0),
            "cost": getattr(usage, "estimated_cost", 0.0)
        }
    }

    return render_data
