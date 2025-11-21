from langchain.messages import SystemMessage, HumanMessage
from ..Prompt.bascial_prompt import BASE_RULES, OUTPUT_RULES

def create_prompt(msgs):

    chat_text = "\n".join(
        f"{m['sender_nickname']}: {m['raw_message']}"
        for m in msgs
    )

    sys = SystemMessage(content=(
        BASE_RULES +
        "\n\n【任务说明】\n"
        "你将看到：基础信息 + 聊天内容\n"
        "请基于这些信息，生成一份高信息量的【纯摘要】，不要输出基础信息。\n\n"
        + OUTPUT_RULES
    ))

    # 用户消息
    hum = HumanMessage(content=(
        "以下为本次聊天内容，请生成【纯摘要】：\n\n"
        + chat_text
    ))

    return [sys, hum]
