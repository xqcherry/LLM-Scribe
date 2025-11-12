from langchain.messages import SystemMessage, HumanMessage
from llm_scribe.Prompt.bascial_prompt import BASE_RULES, OUTPUT_RULES
import json
# 生成完整摘要提示词,需要last_summary, 主体信息msgs, 基础信息meta
def create_prompt(mem_json, msgs, meta, semantic_related=None):
    time_span = meta["time_span"]
    user_count = meta["user_count"]
    msg_count = meta["msg_count"]
    duration = meta["duration"]
    # 语义池背景
    semantic_text = json.dumps(semantic_related or {}, ensure_ascii=False)
    # json To str
    last_summary = mem_json.get("last_summary", "")

    chat_text = "\n".join(
        f"{m['sender_nickname']}: {m['raw_message']}"
        for m in msgs
    )

    sys = SystemMessage(content=(
        BASE_RULES +
        "\n\n【本次任务】请基于下面的“基础信息”和“聊天内容”生成一份高信息量的‘纯摘要’（不要输出基础信息）。"
        "\n必须只生成摘要本体，不得重复输出基础信息。\n\n" +
        "需要覆盖所有核心内容、主题、事件。\n\n" +
        OUTPUT_RULES
    ))

    hum = HumanMessage(content=(
        f"【语义背景】（不可写入输出，但用于补齐上下文）\n{semantic_text}\n\n"
        f"(上次摘要参考：{last_summary or '无'})\n\n"
        "以下为本次对话的基础信息（用于理解，不要写入摘要输出）：\n"
        f"基础信息：\n"
        f"- 时段：{time_span}\n"
        f"- 参与：{user_count}人，{msg_count}条消息\n"
        f"- 时长：{duration}\n\n"
        "以下为本次聊天内容，请生成‘纯摘要’：\n\n" +
        chat_text
    ))

    return [sys, hum]