from langchain.messages import SystemMessage, HumanMessage
from llm_scribe.Prompt.bascial_prompt import BASE_RULES
import json

# 追加摘要的提示词
def append_prompt(new_msgs, mem_json, semantic_related):
    old_summary = mem_json.get("last_summary", "")
    semantic_text = json.dumps(semantic_related or {}, ensure_ascii=False)
    new_text = "\n".join(
        f"{m['sender_nickname']}: {m['raw_message']}"
        for m in new_msgs
    )

    sys = SystemMessage(content=(
        BASE_RULES +
        "\n\n【本次任务】基于“新增消息”对旧摘要进行增量补充。\n"
        "增量补充规则：\n"
        "1. 输出内容必须是“新增信息”的补充，不得重复旧摘要内容。\n"
        "2. 严禁重新生成完整摘要，只生成新增部分的总结。\n"
        "3. 请以若干句的“补充摘要”形式输出。\n"
        "4. 严禁输出基础信息（时段、人数等）。\n"
        "5. 严禁输出标题（如‘摘要’、‘补充内容’等）。\n"
        "6. 风格保持客观、中立、简洁。\n"
    ))

    hum = HumanMessage(content=(
        f"【语义背景】（用于补齐上下文，不要写入输出）：\n{semantic_text}\n\n"
        "以下是旧摘要（仅用于参考，不要重复其内容）：\n"
        f"{old_summary or '无'}\n\n"
        "以下是新增消息，请基于这些补充若干句摘要：\n\n" +
        new_text
    ))

    return [sys, hum]