from typing import Any, List


class SummaryFormatService:
    """负责将结构化摘要结果格式化为群消息可读的文本"""

    @staticmethod
    def format(result: Any) -> str:
        """格式化话题摘要为文本（适配新的TopicSummary结构）"""

        lines: List[str] = ["📊 【今日群聊话题回顾】", ""]
        topics = getattr(result, "topics", [])

        if not topics:
            return "📊 今日群聊内容平淡，未提取到显著话题"

        for i, t in enumerate(topics[:8], 1):
            topic_title = getattr(t, "topic", f"话题 {i}")
            topic_detail = getattr(t, "detail", "（无详细内容）")
            participants = getattr(t, "participants", [])

            # 格式：数字编号 + 加粗标题
            lines.append(f"{i}. #**{topic_title}**#")

            # 参与者信息（如果有）
            if participants:
                participants_str = "、".join(participants[:5])
                lines.append(f"   👥 参与者: {participants_str}")
            
            # 话题详情
            lines.append(f"   └ {topic_detail}")
            lines.append("")

        return "\n".join(lines).strip()

