"""消息清洗器"""
from typing import List, Dict
from ...utils.filter import CQ_filter


class MessageCleaner:
    """消息清洗器"""
    
    def clean(self, messages: List[Dict]) -> List[Dict]:
        """清洗消息"""
        cleaned = []
        for msg in messages:
            cleaned_msg = msg.copy()
            cleaned_msg["raw_message"] = CQ_filter(msg.get("raw_message", ""))
            if cleaned_msg["raw_message"].strip():
                cleaned.append(cleaned_msg)
        return cleaned
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        return CQ_filter(text)
