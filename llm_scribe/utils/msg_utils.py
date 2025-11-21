from ..Prompt.extract_prompt import EXTRACT
from ..LLM.model import model
from ..memory.memory_short import STRUCTURE
from .text_utils import to_str
import json

def chunk_msgs(msgs, chunk_size=220, overlap=50):

    n = len(msgs)
    if n == 0:
        return []

    chunks = []
    i = 0
    while i < n:
        end = min(i + chunk_size, n)
        chunks.append(msgs[i:end])
        i += (chunk_size - overlap)

    return chunks

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