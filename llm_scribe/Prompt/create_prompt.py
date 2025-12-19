from langchain.messages import SystemMessage, HumanMessage
from ..Prompt.bascial_prompt import BASE_RULES, OUTPUT_RULES


def create_prompt(msgs):
    # 拼接聊天内容
    chat_text = "\n".join(
        f"{m.get('sender_nickname', m.get('user_id', ''))}: {m.get('raw_message', '')}"
        for m in msgs
        if m.get("raw_message")
    )

    sys = SystemMessage(content=(
        BASE_RULES +
        "\n\n任务说明\n"
        "你将看到：基础信息 + 聊天内容\n"
        "在摘要中引用成员时，优先使用聊天内容中的昵称，而不是'有的成员''有人'等模糊说法。\n\n"
        + OUTPUT_RULES
    ))

    # 用户消息
    hum = HumanMessage(content=(
        "以下为本次聊天内容：\n\n"
        + chat_text
    ))

    return [sys, hum]


def create_delta_prompt(last_summary: str, new_msgs):
    """
    基于"上次摘要 + 新增聊天内容"的增量摘要提示词。
    只要求模型总结新增部分带来的变化，不重复旧摘要。
    """
    new_chat_text = "\n".join(
        f"{m.get('sender_nickname', m.get('user_id', ''))}: {m.get('raw_message', '')}"
        for m in new_msgs
        if m.get("raw_message")
    )

    sys = SystemMessage(
        content=(
            "你是一个群聊摘要助手。\n"
            "你已经有一份'上次摘要'，现在给你一小段新增的聊天记录。\n"
            "请在不重复上次摘要内容的前提下，准确、详细地说明本次新增聊天为整体带来的新增信息和变化。\n"
            "禁止编造不存在的对话，只能基于提供的新增聊天内容进行总结。\n"
        )
    )

    hum = HumanMessage(
        content=(
            "下面是[上次摘要]\n"
            "请只针对本次新增部分，生成一段'本次新增内容'的详细摘要，用于附加在上次摘要之后。\n\n"
            "[上次摘要]:\n"
            f"{last_summary}\n\n"
            "[本次新增聊天内容]:\n"
            f"{new_chat_text}\n"
        )
    )

    return [sys, hum]
