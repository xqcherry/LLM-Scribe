import re
from .meta_utils import info_to_str

def to_str(text):
    if text is None:
        return ""
    if hasattr(text, "content"):
        return text.content or ""
    return str(text)

# 美化纯摘要
def beautify_smy(text):

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