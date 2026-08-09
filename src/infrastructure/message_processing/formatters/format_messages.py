from datetime import datetime
from typing import List, Dict

from ..filters.cq_filter import cq_filter


def format_messages(messages: List[Dict]) -> str:
    """格式化消息为喂给 LLM 的文本（[HH:MM] [user_id]: content）。"""
    formatted = []

    for msg in messages:
        user_id = str(msg.get("user_id", ""))
        if not user_id:
            continue

        msg_time = msg.get("time", 0)
        time_str = datetime.fromtimestamp(msg_time).strftime("%H:%M") \
            if isinstance(msg_time, (int, float)) else ""

        content = cq_filter(msg.get("raw_message", ""))
        if not content or len(content.strip()) < 2 or content.strip().startswith("/"):
            continue

        formatted.append(f"[{time_str}] [{user_id}]: {content}")

    return "\n".join(formatted)
