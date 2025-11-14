from llm_scribe.DB.chat_loader import get_group_msg
from llm_scribe.memory.memory_short import load_memory_short
from llm_scribe.memory.cache import load_chat_cache, get_group_msg_after, save_chat_cache
from llm_scribe.memory.refresh import high_refresh, low_refresh, high_refresh_chunk
from datetime import datetime, timezone

def run(group_id, hours):
    msgs = get_group_msg(group_id, hours)

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

    # 第一次运行：直接high
    if not cache or short["last_check_ts"] is None:
        if len(msgs) > 250:
            return high_refresh_chunk(group_id, msgs, hours)
        return high_refresh(group_id, msgs, hours)

    # 查询窗口大小变化(24h → 6h)：直接high
    last_hours = short["mem_json"].get("last_window_hours")
    if last_hours is not None and last_hours != hours:
        if len(msgs) > 250:
            return high_refresh_chunk(group_id, msgs, hours)
        return high_refresh(group_id, msgs, hours)

    # 从缓存获取旧消息
    cache_msgs = cache["msgs"]
    cache_end_time = cache_msgs[-1]["time"]

    # 如果当前请求窗口比缓存覆盖更大，需要重新拉全量 high
    now = int(datetime.now().timestamp())
    cache_window_hours = (cache_end_time - cache_msgs[0]["time"]) / 3600

    if hours > cache_window_hours + 0.1:
        full_msgs = get_group_msg(group_id, hours)
        if len(full_msgs) > 250:
            return high_refresh_chunk(group_id, full_msgs, hours)
        return high_refresh(group_id, full_msgs, hours)

    # 增量消息获取
    new_msgs = get_group_msg_after(group_id, cache_end_time)

    # 没有增量,low
    if not new_msgs:
        return low_refresh(group_id, msgs, short)

    # 更新缓存
    cache_msgs = cache_msgs + new_msgs
    start_ts = datetime.fromtimestamp(cache_msgs[0]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_ts = datetime.fromtimestamp(cache_msgs[-1]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    save_chat_cache(group_id, cache_msgs, start_ts, end_ts)

    # 增量数量判断
    deltaN = len(new_msgs)

    if deltaN >= 10:
        if len(msgs) > 250:
            return high_refresh_chunk(group_id, msgs, hours)
        return high_refresh(group_id, msgs, hours)
    # 少量增量 low
    return low_refresh(group_id, msgs, short)