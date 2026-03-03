"""
缓存键生成工具。

从原先的 `src.cache.llm_cache.cache_key` 迁移而来。
"""

import hashlib
import json
from typing import List, Dict


class CacheKeyGenerator:
    """缓存键生成器。"""

    @staticmethod
    def generate_message_hash(messages: List[Dict]) -> str:
        """生成消息内容的哈希。"""
        key_info = {
            "count": len(messages),
            "participants": sorted(
                set(
                    m.get("sender_nickname", "")
                    for m in messages
                    if m.get("sender_nickname")
                )
            ),
            "time_range": (
                messages[0]["time"] if messages else 0,
                messages[-1]["time"] if messages else 0,
            ),
        }
        content = json.dumps(key_info, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    @staticmethod
    def generate_cache_key(group_id: int, hours: int, messages_hash: str) -> str:
        """生成完整的缓存键。"""
        key_data = {
            "group_id": group_id,
            "hours": hours,
            "messages_hash": messages_hash,
        }
        return json.dumps(key_data, sort_keys=True)

    @staticmethod
    def generate_semantic_query(messages: List[Dict]) -> str:
        """生成用于语义匹配的查询字符串。"""
        participants = set(
            m.get("sender_nickname", "") for m in messages if m.get("sender_nickname")
        )

        if len(messages) <= 10:
            message_text = "\n".join(
                m.get("raw_message", "")[:100] for m in messages
            )
        else:
            # 采样策略：开头 + 结尾 + 中间采样
            head = messages[:3]
            tail = messages[-3:]
            middle_idx = len(messages) // 2
            middle = messages[middle_idx : middle_idx + 3]

            message_text = "\n".join(
                m.get("raw_message", "")[:100] for m in head + middle + tail
            )

        return (
            f"群组消息摘要请求：参与者{len(participants)}人，共{len(messages)}条消息\n"
            f"{message_text}"
        )

