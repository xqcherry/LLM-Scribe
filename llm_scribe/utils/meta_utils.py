from ..utils.time_utils import unix_to_shanghai

# 基础信息meta
def base_info(msgs):

    timestamps = [m["time"] for m in msgs]
    dt_start = unix_to_shanghai(min(timestamps))
    dt_end = unix_to_shanghai(max(timestamps))

    duration_minutes = int((dt_end - dt_start).total_seconds() / 60)
    duration = f"约{duration_minutes}分钟" if duration_minutes < 60 else f"约{duration_minutes // 60}小时"

    meta = {
        "time_span": f"{dt_start:%Y-%m-%d %H:%M}~{dt_end:%Y-%m-%d %H:%M}",
        "user_count": len(set(m["user_id"] for m in msgs)),
        "msg_count": len(msgs),
        "duration": duration
    } # dict
    return meta

def info_to_str(meta):
    data = (
        "[基础信息]\n"
        f"- 时段：{meta['time_span']}\n"
        f"- 参与：{meta['user_count']}人，共 {meta['msg_count']} 条消息\n"
        f"- 时长：{meta['duration']}\n"
    )
    return data # str