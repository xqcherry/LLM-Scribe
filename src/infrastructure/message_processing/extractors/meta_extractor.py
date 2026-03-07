from typing import List, Dict, Any

from src.infrastructure.common.utils.time_utils import unix_to_shanghai


def compute_message_meta(msgs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    基于清洗后的消息列表提取元数据统计信息。
    """
    if not msgs:
        return {
            "time_span": "-",
            "user_count": 0,
            "msg_count": 0,
            "duration": "-",
            "total_characters": 0,
            "hourly_distribution": [0] * 24,
        }

    # 1. 时间维度统计
    timestamps = [m["time"] for m in msgs]
    min_ts, max_ts = min(timestamps), max(timestamps)
    dt_start = unix_to_shanghai(min_ts)
    dt_end = unix_to_shanghai(max_ts)

    duration_seconds = int((dt_end - dt_start).total_seconds())
    if duration_seconds < 3600:
        duration = f"约{duration_seconds // 60}分钟"
    else:
        duration = f"约{duration_seconds // 3600}小时"

    # 2. 内容维度统计
    # 直接计算清洗后的 raw_message 长度
    total_characters = sum(len(str(m.get("raw_message", ""))) for m in msgs)

    # 3. 活跃度分布 (0~23 点)
    hourly = [0] * 24
    user_ids = set()

    for m in msgs:
        # 统计独立用户
        user_ids.add(m["user_id"])
        # 统计小时分布
        dt = unix_to_shanghai(m["time"])
        hourly[dt.hour] += 1

    return {
        "time_span": f"{dt_start:%Y-%m-%d %H:%M} ~ {dt_end:%H:%M}",
        "user_count": len(user_ids),
        "msg_count": len(msgs),
        "duration": duration,
        "total_characters": total_characters,
        "hourly_distribution": hourly,
    }