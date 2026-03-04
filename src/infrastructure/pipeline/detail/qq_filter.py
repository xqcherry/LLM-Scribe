from typing import List, Dict, Iterable


def filter_msgs(msgs: List[Dict], ignore_ids: Iterable) -> List[Dict]:
    """过滤指定 QQ 的消息"""
    if not msgs:
        return []
    ignore_set = set(ignore_ids)
    return [m for m in msgs if m.get("user_id") not in ignore_set]