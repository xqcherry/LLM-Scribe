import re
import html
from typing import List, Dict, Iterable


def cq_filter(text: str) -> str:
    """智能过滤 CQ 码，将 OneBot 格式转为可读文本"""
    if not text:
        return ""
    text = html.unescape(text)

    text = re.sub(r'\[图片][,，]?\s*file=[^,\]\s]+[^]]*]', '[图片]', text)
    text = re.sub(r'\[CQ:face,[^]]*]', '[表情]', text)
    text = re.sub(r'\[CQ:at,qq=(\d+)]', r'[@\1]', text)
    text = re.sub(r'\[CQ:reply,[^]]*]', '', text)
    text = re.sub(r'\[CQ:image,[^]]*]', '[图片]', text)
    text = re.sub(r'\[CQ:forward,[^]]*]', '[转发消息]', text)
    text = re.sub(r'\[CQ:file,[^]]*file=([^,]+)[^]]*]', r'[文件: \1]', text)
    text = re.sub(r'\[CQ:video,[^]]*]', '[视频]', text)
    text = re.sub(
        r'\[CQ:json,[^]]*"prompt":"([^"]+)"[^]]*]',
        lambda m: f"[卡片: {m.group(1)}]",
        text
    )
    text = re.sub(r'\[CQ:json,[^]]*]', '[卡片]', text)
    text = re.sub(r'\[图片][,，]?\s*file=[^,\]\s]+[^]]*]', '[图片]', text)
    text = re.sub(r'\[CQ:[^]]+]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def filter_msgs(msgs: List[Dict], ignore_ids: Iterable) -> List[Dict]:
    """过滤指定 QQ 的消息"""
    if not msgs:
        return []
    ignore_ids = set(ignore_ids)
    return [m for m in msgs if m.get("user_id") not in ignore_ids]
