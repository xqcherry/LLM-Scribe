from datetime import datetime
from typing import List, Dict, Any

from src.infrastructure.pipeline.detail.cq_filter import cq_filter


def format_messages(messages: List[Dict]) -> tuple[str, dict[Any, Any]]:
    """
    格式化消息并构建 ID -> 昵称映射
    返回: (格式化后的文本, 昵称映射表)
    """
    formatted = []
    id2name = {}

    for msg in messages:
        user_id = str(msg.get("user_id", ""))
        if not user_id:
            continue

        # 1. 记录昵称映射
        nickname = str(msg.get("sender_nickname") or user_id).strip()
        id2name[user_id] = nickname

        # 2. 时间处理
        msg_time = msg.get("time", 0)
        time_str = datetime.fromtimestamp(msg_time).strftime("%H:%M")\
            if isinstance(msg_time, (int, float)) else ""

        # 3. 内容处理
        content = cq_filter(msg.get("raw_message", ""))
        if not content or len(content.strip()) < 2 or content.strip().startswith("/"):
            continue

        formatted.append(f"[{time_str}] [{user_id}]: {content}")

    return "\n".join(formatted), id2name