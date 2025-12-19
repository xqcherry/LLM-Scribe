from ..memory.memory_short import load_memory_short, save_memory_short
from ..memory.memory_long import save_memory_long
from ..memory.cache import save_chat_cache
from ..Prompt.create_prompt import create_prompt, create_delta_prompt
from ..LLM.model import model
from ..utils.text_utils import to_str, beautify_smy, display_summary
from ..utils.meta_utils import base_info
from ..utils.msg_utils import chunk_msgs

# 全量更新, 将生成的summary和 mem_json存入长期，短期记忆,cache
def high_refresh(group_id, msgs, hours):
    short = load_memory_short(group_id)
    pool = short.get("mem_json", {}).copy()

    # 基础信息
    meta = base_info(msgs)

    # 摘要部分
    prompt = create_prompt(msgs)
    response = to_str(model.invoke(prompt))
    summary = beautify_smy(response)

    # 保存cache
    start_ts = msgs[0]["time"]
    end_ts = msgs[-1]["time"]
    save_chat_cache(group_id, msgs, start_ts, end_ts)

    # 保存短期记忆
    pool["last_summary"] = summary
    pool["last_window_hours"] = hours
    save_memory_short(group_id, pool)

    # 存入长期记忆
    save_memory_long(group_id, summary)

    final_summary = display_summary(summary, meta)
    return final_summary

def high_refresh_chunk(group_id, msgs, hours):
    short = load_memory_short(group_id)
    pool = short["mem_json"].copy()

    # 切片
    chunks = list(chunk_msgs(msgs, chunk_size=220, overlap=50))

    # 每段做小摘要
    chunk_summaries = []
    for idx, c in enumerate(chunks, 1):
        prompt = create_prompt(c)
        resp = to_str(model.invoke(prompt))
        chunk_summary = beautify_smy(resp)

        # 包装为“分段摘要 N”
        chunk_summaries.append(
            f"=== 分段摘要（{idx}/{len(chunks)}）===\n{chunk_summary}\n"
        )

    # cache
    start_ts = msgs[0]["time"]
    end_ts = msgs[-1]["time"]
    save_chat_cache(group_id, msgs, start_ts, end_ts)

    # 更新短期记忆
    all_summary_text = "\n".join(chunk_summaries)
    pool["last_summary"] = all_summary_text
    pool["last_window_hours"] = hours
    save_memory_short(group_id, pool)

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
        save_memory_short(group_id, None)
        return f"（本时间段无消息）\n\n[上次摘要回顾]\n\n{summary}\n"

    # 只更新cache
    start_ts = msgs[0]["time"]
    end_ts = msgs[-1]["time"]
    save_chat_cache(group_id, msgs, start_ts, end_ts)

    # 不更新 mem_json，只更新时间戳
    save_memory_short(group_id, None)

    # 生成新的基础信息
    meta = base_info(msgs)
    final_summary = display_summary(summary, meta)
    return final_summary

def delta_refresh(group_id, msgs, new_msgs, short, hours):
    """
    小增量刷新：
    基于上次摘要 + 新增原文消息，生成增量摘要并合并到 last_summary 中。
    """
    # 获取上次摘要
    last_summary = ""
    if short and short.get("mem_json"):
        last_summary = short["mem_json"].get("last_summary", "") or ""

    # 如果没有历史摘要可用，直接全量刷新
    if not last_summary:
        return high_refresh(group_id, msgs, hours)

    # 只保留基础摘要部分
    base_summary = last_summary
    if "[本次新增内容]" in last_summary:
        base_summary = last_summary.split("[本次新增内容]")[0].strip()

    prompt = create_delta_prompt(base_summary, new_msgs)
    if not prompt:
        return low_refresh(group_id, msgs, short)
    delta_resp = to_str(model.invoke(prompt))
    delta_summary = beautify_smy(delta_resp)

    # 基础摘要 + 本次新增部分
    combined_summary = (
        base_summary
        + "\n\n** [本次新增内容] **\n"
        + delta_summary
    ).strip()

    # 更新短期记忆
    pool = short.get("mem_json", {}).copy() if short else {}
    pool["last_summary"] = combined_summary
    pool["last_window_hours"] = hours
    save_memory_short(group_id, pool)

    # 更新 cache：当前窗口内的完整消息
    start_ts = msgs[0]["time"]
    end_ts = msgs[-1]["time"]
    save_chat_cache(group_id, msgs, start_ts, end_ts)

    # 基础信息
    meta = base_info(msgs)
    final_summary = display_summary(combined_summary, meta)
    return final_summary
