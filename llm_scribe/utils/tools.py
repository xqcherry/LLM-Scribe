from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from llm_scribe.Prompt.prompt3 import EXTRACT
from llm_scribe.LLM.model import get_llm
from llm_scribe.memory.memory_short import STRUCTURE
import re, json

model = get_llm()

def to_str(text):
    if text is None:
        return ""
    if hasattr(text, "content"):
        return text.content or ""
    return str(text)

def modify_ts(value):
    if isinstance(value, datetime):
        return int(value.timestamp())
    # 字符串 DATETIME
    return int(datetime.strptime(value, "%Y-%m-%d %H:%M:%S").timestamp())

# 基础信息meta
def base_info(msgs):
    CN_TZ = ZoneInfo("Asia/Shanghai")

    timestamps = [m["time"] for m in msgs]
    dt_start = datetime.fromtimestamp(min(timestamps), tz=timezone.utc).astimezone(CN_TZ)
    dt_end = datetime.fromtimestamp(max(timestamps), tz=timezone.utc).astimezone(CN_TZ)

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
        "基础信息：\n"
        f"- 时段：{meta['time_span']}\n"
        f"- 参与：{meta['user_count']}人，共 {meta['msg_count']} 条消息\n"
        f"- 时长：{meta['duration']}\n"
    )
    return data # str
# 美化纯摘要
def beautify_smy(text):

    text = to_str(text)

    if not text:
        return "摘要为空"
    # 去 markdown 格式
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`]+", "", text)
    # 标题格式
    text = re.sub(r"\s*(基础信息)\s*", r"\n\n\1\n", text)
    text = re.sub(r"\s*(整体摘要)\s*", r"\n\n\1\n", text)
    text = re.sub(r"\s*(话题总结)\s*", r"\n\n\1\n", text)
    # 删除多余空行
    text = re.sub(r"(\n){3,}", "\n", text)

    return text.strip()
# 展示完整输出 info + summary
def display_summary(summary, meta):
    info = info_to_str(meta)
    return info + "\n" + summary
# 构建mem_json
def build_mem_json(msgs):

    data = STRUCTURE.copy()
    if not msgs:
        return data;

    lines = []
    for m in msgs:
        t = m.get("time")  # 时间戳
        u = m.get("sender_nickname", m.get("user_id"))  # 优先昵称，其次用户ID
        txt = m.get("raw_message")  # 消息内容
        lines.append(f"[{t}] {u}: {txt}")

    chat_text = "\n".join(lines)

    prompt = EXTRACT.replace("{CHAT_MESSAGES}", chat_text)
    response = to_str(model.invoke(prompt))

    try:
        data = json.loads(response)
    except:
        data = {
            "concepts": [],
            "events": [],
            "quotes": [],
        }

    return data
