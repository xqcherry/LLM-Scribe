import re
import html
from typing import List, Dict, Iterable

# 预编译正则
RE_FACE = re.compile(r'\[CQ:face,[^]]*]')
RE_AT = re.compile(r'\[CQ:at,qq=(\d+)]')
RE_REPLY = re.compile(r'\[CQ:reply,[^]]*]')
RE_IMAGE = re.compile(r'\[CQ:image,[^]]*]|\[图片][^]]*]')  # 合并图片处理
RE_FORWARD = re.compile(r'\[CQ:forward,[^]]*]')
RE_FILE = re.compile(r'\[CQ:file,[^]]*file=([^,\]\s]+)[^]]*]')
RE_VIDEO = re.compile(r'\[CQ:video,[^]]*]')
RE_JSON_PROMPT = re.compile(r'\[CQ:json,[^]]*"prompt":"([^"]+)"[^]]*]')
RE_JSON_GENERIC = re.compile(r'\[CQ:json,[^]]*]')
RE_OTHER_CQ = re.compile(r'\[CQ:[^]]+]')
RE_WHITESPACE = re.compile(r'\s+')

def cq_filter(text: str) -> str:
    """智能过滤 CQ 码"""
    if not text:
        return ""

    # 1. 解码 HTML 转义字符 (如 &amp; -> &)
    text = html.unescape(text)

    # 2. 按优先级替换
    text = RE_REPLY.sub('', text)
    text = RE_AT.sub(r'[@\1]', text)
    text = RE_FACE.sub('[表情]', text)
    text = RE_IMAGE.sub('[图片]', text)
    text = RE_FORWARD.sub('[转发消息]', text)
    text = RE_FILE.sub(r'[文件: \1]', text)
    text = RE_VIDEO.sub('[视频]', text)

    # 3. 处理 JSON 卡片
    text = RE_JSON_PROMPT.sub(lambda m: f"[卡片: {m.group(1)}]", text)
    text = RE_JSON_GENERIC.sub('[卡片]', text)

    # 4. 清理残留的所有其他 CQ 码并压缩空白符
    text = RE_OTHER_CQ.sub('', text)
    text = RE_WHITESPACE.sub(' ', text).strip()

    return text


def filter_msgs(msgs: List[Dict], ignore_ids: Iterable) -> List[Dict]:
    """过滤指定 QQ 的消息"""
    if not msgs:
        return []
    ignore_set = set(ignore_ids)
    return [m for m in msgs if m.get("user_id") not in ignore_set]