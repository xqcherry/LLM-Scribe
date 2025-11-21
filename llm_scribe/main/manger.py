from ..DB.chat_loader import get_group_msg
from ..memory.memory_short import load_memory_short
from ..memory.cache import load_chat_cache, get_group_msg_after
from ..memory.memory_refresh import high_refresh, low_refresh, high_refresh_chunk
from ..utils.filter import filter_msgs

IGNORE_QQ = {3674697536, 2303866129}

def run(group_id, hours):
    msgs = filter_msgs(get_group_msg(group_id, hours), IGNORE_QQ)

    # 无消息情况
    if not msgs:
        short = load_memory_short(group_id)
        last_summary = short["mem_json"].get("last_summary") if short else None
        if not last_summary:
            return "(本时间段无消息，且系统暂无历史摘要)"
        return f"（本时间段无消息）\n\n[上次摘要回顾]\n\n{last_summary}\n"

    # 读取缓存与短期记忆
    cache = load_chat_cache(group_id)
    short = load_memory_short(group_id)
    last_check_ts = short.get("last_check_ts") if short else None
    last_hours = short["mem_json"].get("last_window_hours") if short else None

    first_run = (cache is None or short is None or last_check_ts is None)
    windows_changed = (last_hours is not None and last_hours != hours)

    if first_run:
        mode = "HIGH"
    elif windows_changed:
        mode = "HIGH"
    else:
        cache_end_ts = int(cache["end_ts"])
        new_msgs = get_group_msg_after(group_id, cache_end_ts)
        new_msgs = filter_msgs(new_msgs, IGNORE_QQ)

        if not new_msgs:
            mode = "LOW"
        else:
            if len(new_msgs) >= 20:
                mode = "HIGH"
            else:
                mode = "LOW"

    if mode == "HIGH":
        if len(msgs) > 220:
            return high_refresh_chunk(group_id, msgs, hours)
        else:
            return high_refresh(group_id, msgs, hours)
    else:
        return low_refresh(group_id, msgs, short)
