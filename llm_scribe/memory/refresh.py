from llm_scribe.memory.memory_short import load_memory_short, save_memory_short
from llm_scribe.memory.memory_long import save_memory_long
from llm_scribe.memory.cache import save_chat_cache
from llm_scribe.Prompt.prompt1 import create_prompt
from llm_scribe.LLM.model import get_llm
from llm_scribe.utils import display_summary, to_str, beautify_smy, base_info
from datetime import datetime, timezone

model = get_llm()

# 全量更新, 将生成的summary和 mem_json存入长期，短期记忆,cache
def high_refresh(group_id, msgs, hours):
    short = load_memory_short(group_id)
    pool = short.get("mem_json", {}).copy()

    # 基础信息
    meta = base_info(msgs)

    # 摘要部分
    prompt = create_prompt(pool, msgs, meta)
    response = to_str(model.invoke(prompt))
    summary = beautify_smy(response)

    # 保存cache
    start_ts = datetime.fromtimestamp(msgs[0]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_ts = datetime.fromtimestamp(msgs[-1]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    save_chat_cache(group_id, msgs, start_ts, end_ts)

    # 保存短期记忆
    pool["last_summary"] = summary
    pool["last_window_hours"] = hours
    save_memory_short(group_id, pool, full_refresh=True)

    # 存入长期记忆
    save_memory_long(group_id, summary)

    final_summary = display_summary(summary, meta)
    return final_summary

def low_refresh(group_id, msgs, short):
    summary = short["mem_json"].get("last_summary", "")

    if not msgs:
        # 本时间段没有消息不更新 cache，不更新 last_summary
        save_memory_short(group_id, None, full_refresh=False)
        return f"（本时间段无消息）\n\n[上次摘要回顾]\n\n{summary}\n"

    # 只更新cache
    start_ts = datetime.fromtimestamp(msgs[0]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_ts = datetime.fromtimestamp(msgs[-1]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    save_chat_cache(group_id, msgs, start_ts, end_ts)

    # 不更新 mem_json，只更新时间戳
    save_memory_short(group_id, None, full_refresh=False)

    # 生成新的基础信息
    meta = base_info(msgs)
    final_summary = display_summary(summary, meta)
    return final_summary

# # 中量更新
# def mid_refresh(group_id, new_msgs, short, cache):
#     pool = short["mem_json"] # short片段是上次记忆
#     old_summary = pool.get("last_summary", "")
#     # 语义池部分
#     # 生成新摘要: summary + increasing
#     prompt = append_prompt(new_msgs, pool)
#     reponse = to_str(model.invoke(prompt))
#     append_summary = beautify_smy(reponse)
#     # 新摘要拼接
#     new_summary = (old_summary + "\n" + append_summary).strip()
#     # 只保存短期记忆
#     pool["last_summary"] = new_summary
#     save_memory_short(group_id, pool, full_refresh=False)
#     # 生成新的基础信息meta
#     meta = base_info(cache["msgs"])
#     final_summary = display_summary(new_summary, meta)
#     return final_summary