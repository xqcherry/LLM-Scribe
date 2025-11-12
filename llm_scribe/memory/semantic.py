import json, jieba, re
from llm_scribe.LLM.model import get_llm
from llm_scribe.Prompt.prompt3 import EXTRACT
from llm_scribe.utils import to_str
from datetime import datetime

model = get_llm()

STRUCTURE = {
    "concepts": [],
    "facts": [],
    "events": [],
    "quotes": [],
    "topics": [],
    "last_update_ts": None,
    "last_summary": ""
}

MAX_CONCEPTS = 20
MAX_FACTS = 50
MAX_EVENTS = 50
MAX_QUOTES = 30
MAX_TOPICS = 30
# 语义池关键词提取
def semantic_extract(new_msgs):
    if not new_msgs:
        return {
            "concepts": [],
            "facts": [],
            "events": [],
            "quotes": [],
            "topics": []
        }

    lines = []
    for m in new_msgs:
        t = m.get("time")
        u = m.get("sender_nickname", m.get("user_id"))
        txt = m.get("raw_message")
        lines.append(f"[{t}] {u}: {txt}")
    chat_text = "\n".join(lines)

    prompt = EXTRACT.replace("{CHAT_MESSAGES}", chat_text)

    response = to_str(model.invoke(prompt))

    try:
        data = json.loads(response)
    except:
        data = {
            "concepts": [],
            "facts": [],
            "events": [],
            "quotes": [],
            "topics": []
        }
    return data # dict
# 语义池合并
def semantic_merge(short, blocks):
    # 初始化 short
    if not isinstance(short, dict):
        short = STRUCTURE.copy()
    else:
        for k, v in STRUCTURE.items():
            short.setdefault(k, v if not isinstance(v, list) else v.copy())
    if not isinstance(blocks, dict):
        blocks = {}
    # 保留摘要
    last_summary = short.get("last_summary", "")
    # concepts
    merged = short["concepts"] + blocks.get("concepts", [])
    dedup = []
    seen = set()
    for c in merged:
        if c not in seen:
            seen.add(c)
            dedup.append(c)
    short["concepts"] = dedup[:MAX_CONCEPTS]
    # facts
    merged = short["facts"] + blocks.get("facts", [])
    dedup = []
    seen = set()
    for f in reversed(merged):
        if f not in seen:
            seen.add(f)
            dedup.append(f)
    short["facts"] = list(reversed(dedup[:MAX_FACTS]))
    # events
    merged = short["events"] + blocks.get("events", [])
    def get_ts(e):
        try:
            t = e.get("time")
            return datetime.fromisoformat(t) if t else datetime.min
        except:
            return datetime.min
    merged = sorted(merged, key=get_ts, reverse=True)
    short["events"] = merged[:MAX_EVENTS]
    # quotes
    merged = short["quotes"] + blocks.get("quotes", [])
    dedup = []
    seen = set()
    for q in reversed(merged):
        if q not in seen:
            seen.add(q)
            dedup.append(q)
    short["quotes"] = list(reversed(dedup[:MAX_QUOTES]))
    # topics
    merged = short["topics"] + blocks.get("topics", [])
    dedup = []
    seen = set()
    for t in reversed(merged):
        title = t.get("topic", "")
        if title not in seen:
            seen.add(title)
            dedup.append(t)
    short["topics"] = list(reversed(dedup[:MAX_TOPICS]))
    # 时间戳 & 上次摘要恢复 ----
    short["last_update_ts"] = datetime.utcnow().isoformat()
    short["last_summary"] = last_summary

    return short

# 从当前窗口消息中，提取语义关键词
def extract_keywords(msgs):
    text_parts = []
    for m in msgs:
        raw = m.get("raw_message", "")
        if not raw:
            continue
        # 跳过无意义标记
        if raw in ["[图片]", "[表情]", "[视频]", "[转发消息]"]:
            continue
        if re.fullmatch(r"\[@\d+\]", raw):
            continue
        if len(raw.strip()) <= 1:
            continue

        text_parts.append(raw)

    text = " ".join(text_parts)
    words = jieba.lcut(text)
    return {w for w in words if len(w.strip()) >= 2}
# 判断一个文本是否含关键字
def match_keywords(text, keywords):
    if not text:
        return False
    return any(k in text for k in keywords)
# 用关键词在语义池中筛选“相关语义”
def filter_keywords(pool, keywords):
    return {
        "concepts": [c for c in pool.get("concepts", []) if match_keywords(c, keywords)],
        "facts":    [f for f in pool.get("facts", []) if match_keywords(f, keywords)],
        "events":   [e for e in pool.get("events", []) if match_keywords(e.get("desc", ""), keywords)],
        "quotes":   [q for q in pool.get("quotes", []) if match_keywords(q, keywords)],
        "topics":   [
            t for t in pool.get("topics", [])
            if match_keywords(t.get("topic", ""), keywords)
            or match_keywords(t.get("summary", ""), keywords)
        ]
    }
# 筛选 + fallback
def semantic_filter(pool, msgs):
    keywords = extract_keywords(msgs)
    related = filter_keywords(pool, keywords)
    # 统计是否完全匹配不到
    if sum(len(v) for v in related.values()) == 0:
        # fallback：最近语义作为背景
        return {
            "concepts": pool.get("concepts", [])[:5],
            "facts": pool.get("facts", [])[:5],
            "events": pool.get("events", [])[:3],
            "quotes": [],
            "topics": pool.get("topics", [])[:3],
        }
    # 如果 topics缺失, 用最近主题
    if not related["topics"]:
        related["topics"] = pool.get("topics", [])[:2]

    return related

