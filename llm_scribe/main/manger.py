from llm_scribe.DB.chat_loader import get_group_msg
from llm_scribe.memory.memory_short import load_memory_short
from llm_scribe.memory.cache import load_chat_cache, get_group_msg_after, save_chat_cache
from llm_scribe.memory.refresh import high_refresh, mid_refresh, low_refresh
from datetime import datetime, timezone

def run(group_id, hours):
    msgs = get_group_msg(group_id, hours)
    # 如果无信息
    if not msgs:
        short = load_memory_short(group_id)
        last_summary = short["mem_json"].get("last_summary") if short else None
        # 如果从未生成过摘要
        if not last_summary:
            return f"(本时间段无消息，且系统暂无历史摘要)"
        # 有摘要
        return (
            f"（本时间段无消息）\n\n"
            f"[上次摘要回顾]\n\n{last_summary}\n"
        )
    # 获取上一次聊天
    cache = load_chat_cache(group_id)
    short = load_memory_short(group_id)
    # 第一次运行，直接high
    if not cache or short["last_check_ts"] is None:
        return high_refresh(group_id, msgs, hours)
    # 窗口变化判定
    last_hours = short["mem_json"].get("last_window_hours")
    if last_hours is not None and last_hours != hours:
        return high_refresh(group_id, msgs, hours)

    cache_msgs = cache["msgs"]
    cache_end = cache_msgs[-1]["time"]

    # 判断查询窗口是否大于缓存窗口, 不足则high
    now = int(datetime.now().timestamp())
    win_start = now - hours * 3600
    cache_hours = (cache_end - cache_msgs[0]["time"]) / 3600 # 计算缓存内时间范围
    if hours > cache_hours + 0.1:
        full_msgs = get_group_msg(group_id, hours)
        return high_refresh(group_id, full_msgs, hours)
    # 增量补齐缓存，保证缓存最新
    new_msgs = get_group_msg_after(group_id, cache_end)
    # 滑动窗口
    if new_msgs:
        cache_msgs = cache_msgs + new_msgs
        # 修剪掉超过24h的部分
        bounds = now - 24*3600
        cache_msgs = [m for m in cache_msgs if m["time"] >= bounds]
        start_ts = datetime.fromtimestamp(cache_msgs[0]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        end_ts = datetime.fromtimestamp(cache_msgs[-1]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        save_chat_cache(group_id, cache_msgs, start_ts, end_ts)
    # 从缓存切片请求的 hours内的msgs
    msgs = [m for m in cache_msgs if m["time"] >= win_start]
    # 从新cache中读取正确的msgs和时间戳
    deltaN = len(new_msgs)
    # 更新传入mid的cache
    cache_obj = {"msgs": msgs}
    if not new_msgs:
        return low_refresh(group_id, msgs, short)
    if deltaN >= 30:
        return high_refresh(group_id, msgs, hours)
    if deltaN >= 5:
        return mid_refresh(group_id, new_msgs, short, cache_obj)

    return low_refresh(group_id, msgs, short)
