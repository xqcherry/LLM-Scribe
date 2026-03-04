from typing import List, Dict, Any

from src.infrastructure.common.time_utils import unix_to_shanghai
from src.infrastructure.pipeline import cq_filter


def compute_message_meta(msgs: List[Dict[str, Any]]) -> Dict[str, Any]:

    if not msgs:
        return {
            "time_span": "-",
            "user_count": 0,
            "msg_count": 0,
            "duration": "-",
            "total_characters": 0,
            "hourly_distribution": [0] * 24,
        }

    timestamps = [m["time"] for m in msgs]
    dt_start = unix_to_shanghai(min(timestamps))
    dt_end = unix_to_shanghai(max(timestamps))

    duration_minutes = int((dt_end - dt_start).total_seconds() / 60)
    duration = (
        f"约{duration_minutes}分钟"
        if duration_minutes < 60
        else f"约{duration_minutes // 60}小时"
    )

    # 总字符数
    total_characters = sum(len(str(cq_filter(m.get("raw_message", "")))) for m in msgs)

    # 0~23 点分布
    hourly = [0] * 24
    for m in msgs:
        dt = unix_to_shanghai(m["time"])
        hourly[dt.hour] += 1

    return {
        "time_span": f"{dt_start:%Y-%m-%d %H:%M}~{dt_end:%Y-%m-%d %H:%M}",
        "user_count": len(set(m["user_id"] for m in msgs)),
        "msg_count": len(msgs),
        "duration": duration,
        "total_characters": total_characters,
        "hourly_distribution": hourly,
    }
