"""去重器"""
from typing import List, Dict
from collections import defaultdict


class Deduplicator:
    """消息去重器"""
    
    def deduplicate(
        self,
        messages: List[Dict],
        time_window: int = 60  # 60秒内的重复消息视为重复
    ) -> List[Dict]:
        """去重消息"""
        if not messages:
            return []
        
        deduplicated = []
        seen = defaultdict(set)  # user_id -> {message_hash}
        
        for msg in messages:
            user_id = msg.get("user_id")
            content = msg.get("raw_message", "").strip()
            
            if not content:
                continue
            
            # 简单的哈希去重
            msg_hash = hash(content)
            
            # 检查是否在时间窗口内重复
            is_duplicate = False
            for prev_msg in deduplicated[-10:]:  # 只检查最近10条
                if (prev_msg.get("user_id") == user_id and
                    prev_msg.get("raw_message", "").strip() == content and
                    abs(prev_msg.get("time", 0) - msg.get("time", 0)) < time_window):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(msg)
        
        return deduplicated
