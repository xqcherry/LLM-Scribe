from langchain.messages import SystemMessage, HumanMessage
from ..Prompt.bascial_prompt import BASE_RULES, OUTPUT_RULES
from ..utils.msg_utils import build_alias_map


def create_prompt(msgs, alias_map=None):
    # 昵称哈希表
    alias_map = alias_map or build_alias_map(msgs)

    mapping_lines = [
        f"{info['code']} = {info['nickname']}"
        for info in alias_map.values()
    ]
    mapping_block = "【参与成员映射表】\n" + "\n".join(mapping_lines) + "\n\n"

    # 拼接聊天内容
    chat_text = "\n".join(
        f"{alias_map[m.get('user_id')]['code']}: {m.get('raw_message', '')}"
        for m in msgs
        if m.get("raw_message")
    )

    sys = SystemMessage(content=(
        BASE_RULES +
        "\n\n【任务说明】\n"
        "你将看到：基础信息 + 聊天内容\n"
        "聊天内容中的发言人使用代号（如 U1、U2），请结合映射表理解具体是谁。\n"
        "在摘要中引用成员时，优先使用映射表中的昵称，而不是“有的成员”“有人”等模糊说法。\n\n"
        + OUTPUT_RULES
    ))

    # 用户消息
    hum = HumanMessage(content=(
        mapping_block +
        "以下为本次聊天内容（发言人使用代号 U1/U2 等）：\n\n"
        + chat_text
    ))

    return [sys, hum]


def create_delta_prompt(last_summary: str, new_msgs, alias_map=None):
    """
    基于“上次摘要 + 新增聊天内容”的增量摘要提示词。
    只要求模型总结新增部分带来的变化，不重复旧摘要。
    """
    # 为新增消息构建代号映射，减少昵称长度，同时配合映射表保证指代清晰
    alias_map = alias_map or build_alias_map(new_msgs)

    mapping_lines = [
        f"{info['code']} = {info['nickname']}"
        for info in alias_map.values()
    ]
    mapping_block = "【参与成员映射表】\n" + "\n".join(mapping_lines) + "\n\n"

    new_chat_text = "\n".join(
        f"{alias_map[m.get('user_id')]['code']}: {m.get('raw_message', '')}"
        for m in new_msgs
        if m.get("raw_message")
    )

    sys = SystemMessage(
        content=(
            "你是一个群聊摘要助手。\n"
            "你已经有一份“上次摘要”，现在给你一小段新增的聊天记录。\n"
            "请在不重复上次摘要内容的前提下，准确、详细地说明本次新增聊天为整体带来的新增信息和变化。\n"
            "禁止编造不存在的对话，只能基于提供的新增聊天内容进行总结。\n"
        )
    )

    hum = HumanMessage(
        content=(
            "下面是【上次摘要】和【本次新增的聊天内容】。\n"
            "请只针对本次新增部分，生成一段“本次新增内容”的详细摘要，用于附加在上次摘要之后。\n\n"
            "【上次摘要】:\n"
            f"{last_summary}\n\n"
            "【本次新增聊天内容】（发言人使用代号 U1/U2 等，对照上方映射表理解具体昵称）:\n"
            f"{mapping_block}{new_chat_text}\n"
        )
    )

    return [sys, hum]
