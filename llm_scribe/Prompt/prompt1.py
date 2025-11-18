from langchain.messages import SystemMessage, HumanMessage
from plugins.llm_scribe.Prompt.bascial_prompt import BASE_RULES, OUTPUT_RULES

def create_prompt(mem_json, msgs, meta):
    time_span = meta["time_span"]
    user_count = meta["user_count"]
    msg_count = meta["msg_count"]
    duration = meta["duration"]

    concepts = mem_json.get("concepts", [])
    events = mem_json.get("events", [])
    quotes = mem_json.get("quotes", [])

    chat_text = "\n".join(
        f"{m['sender_nickname']}: {m['raw_message']}"
        for m in msgs
    )

    sys = SystemMessage(content=(
        BASE_RULES +
        "\n\n【任务说明】\n"
        "你将看到：基础信息 + 聊天内容 + 结构化预处理信息（概念、事件、引用）。\n"
        "请基于这些信息，生成一份高信息量的【纯摘要】，不要输出基础信息。\n\n"
        + OUTPUT_RULES
    ))

    # 用户消息
    hum = HumanMessage(content=(
        "以下是基础信息（用于理解，不要写入摘要输出）：\n"
        f"- 时段：{time_span}\n"
        f"- 参与：{user_count}人，{msg_count}条消息\n"
        f"- 时长：{duration}\n\n"

        "以下是模型预处理后提取出的概念（关键词）：\n"
        f"{concepts}\n\n"

        "以下是模型预处理后提取出的事件列表：\n"
        f"{events}\n\n"

        "以下是模型预处理后提取出的关键引用句子：\n"
        f"{quotes}\n\n"

        "以下为本次聊天内容，请生成【纯摘要】：\n\n"
        + chat_text
    ))

    return [sys, hum]
