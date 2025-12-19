import re
from .meta_utils import info_to_str

def to_str(text):
    if text is None:
        return ""
    if hasattr(text, "content"):
        return text.content or ""
    return str(text)

# 从消息列表中提取唯一昵称
def extract_nicknames(msgs):
    return list(set(m.get('sender_nickname', '')
                    for m in msgs if m.get('sender_nickname')))

# 美化纯摘要
def beautify_smy(text, nicknames=None):

    if not text:
        return "摘要为空"
    # 去 markdown 格式
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`]+", "", text)
    # 标题格式
    text = re.sub(r"\s*(整体摘要)\s*", r"\n\n** [\1] **\n", text)
    text = re.sub(r"\s*(话题总结)\s*", r"\n\n** [\1] **\n", text)
    
    # 标记昵称
    if nicknames:
        unique_nicknames = sorted(set(n for n in nicknames if n and n.strip()), key=len, reverse=True)
        for nickname in unique_nicknames:
            escaped = re.escape(nickname)
            # 只标记不在「」中的昵称，避免重复标记
            text = re.sub(r'(?<!「)' + escaped + r'(?!」)', r'「\g<0>」', text)
    
    # 删除多余空行
    text = re.sub(r"(\n){3,}", "\n", text)

    return text.strip()

# 展示完整输出 info + summary
def display_summary(summary, meta):
    info = info_to_str(meta)
    return info + "\n" + summary


def extract_parts(summary: str):

    if "=== 分段摘要" not in summary:
        return [summary]

    raw = summary.split("=== 分段摘要")
    parts = []

    for idx, segment in enumerate(raw):
        seg = segment.strip()
        if not seg:
            continue

        # 第一段（基础信息 + 内容）不加标签
        if idx == 0:
            parts.append(seg)
        else:
            parts.append("=== 分段摘要" + seg)

    return parts