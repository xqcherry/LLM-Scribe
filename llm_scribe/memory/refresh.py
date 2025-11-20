from ..memory.memory_short import load_memory_short, save_memory_short
from ..memory.memory_long import save_memory_long
from ..memory.cache import save_chat_cache
from ..Prompt.prompt1 import create_prompt
from ..LLM.model import model
from ..utils.tools import display_summary, to_str, beautify_smy, base_info, chunk_msgs
from datetime import datetime, timezone

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

def high_refresh_chunk(group_id, msgs, hours):
    short = load_memory_short(group_id)
    pool = short["mem_json"].copy()

    # 切片
    chunks = list(chunk_msgs(msgs, chunk_size=250, overlap=50))

    # 每段做小摘要
    clean_pool = {"concepts": [], "events": [], "quotes": [], "last_summary": ""}
    chunk_summaries = []
    for idx, c in enumerate(chunks, 1):
        meta = base_info(c)
        prompt = create_prompt(clean_pool, c, meta)
        resp = to_str(model.invoke(prompt))
        chunk_summary = beautify_smy(resp)

        # 包装为“分段摘要 N”
        chunk_summaries.append(
            f"=== 分段摘要（{idx}/{len(chunks)}）===\n{chunk_summary}\n"
        )

    # cache
    start_ts = datetime.fromtimestamp(msgs[0]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_ts = datetime.fromtimestamp(msgs[-1]["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    save_chat_cache(group_id, msgs, start_ts, end_ts)

    # 更新短期记忆
    all_summary_text = "\n".join(chunk_summaries)
    pool["last_summary"] = all_summary_text
    pool["last_window_hours"] = hours
    save_memory_short(group_id, pool, full_refresh=True)

    # 保存长期记忆
    save_memory_long(group_id, all_summary_text)

    # 基础信息
    info = base_info(msgs)
    final_summary = display_summary(all_summary_text, info)

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

