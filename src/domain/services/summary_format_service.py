from typing import Any, List


class SummaryFormatService:
    """负责将结构化摘要结果格式化为群消息可读的文本"""

    @staticmethod
    def format(result: Any) -> str:
        # 逻辑与 `SummaryGraph._format_summary` 保持完全一致
        lines: List[str] = [
            "📊 【群聊摘要】",
            f"🔍 核心摘要：\n{result.overall_summary}\n",
        ]

        if getattr(result, "topics", None):
            lines.append("💡 话题回顾：")
            lines.extend([f"• {t.topic}" for t in result.topics[:5]])

        if getattr(result, "key_quotes", None):
            if result.key_quotes:
                lines.append(f"\n💬 精彩瞬间：\n“{result.key_quotes[0]}”")

        return "\n".join(lines)

