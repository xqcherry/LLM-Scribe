from datetime import datetime
from typing import List, Dict

from src.infrastructure.pipeline.detail.cq_filter import cq_filter


def format_messages(messages: List[Dict]) -> str:
    """格式化消息为 [HH:MM] [用户ID]: 消息内容"""
    formatted = []
    for msg in messages:
        user_id = str(msg.get("user_id", ""))
        if not user_id:
            continue

        msg_time = msg.get("time", 0)
        if isinstance(msg_time, (int, float)):
            time_str = datetime.fromtimestamp(msg_time).strftime("%H:%M")
        elif hasattr(msg_time, "strftime"):
            time_str = msg_time.strftime("%H:%M")
        else:
            time_str = ""

        content = cq_filter(msg.get("raw_message", ""))
        if not content or len(content.strip()) < 2:
            continue

        if content.strip().startswith("/"):
            continue

        formatted.append(f"[{time_str}] [{user_id}]: {content}")

    return "\n".join(formatted)