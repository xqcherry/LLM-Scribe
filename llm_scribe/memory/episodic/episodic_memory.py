"""事件记忆实现"""
from typing import List, Dict
from datetime import datetime


class EpisodicMemory:
    """事件记忆：存储具体的对话片段"""
    
    def __init__(self):
        self.memories: List[Dict] = []
    
    def add_episode(
        self,
        group_id: int,
        messages: List[Dict],
        summary: str,
        timestamp: int
    ):
        """添加事件记忆"""
        episode = {
            "group_id": group_id,
            "messages": messages,
            "summary": summary,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat()
        }
        self.memories.append(episode)
    
    def get_recent_episodes(
        self,
        group_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """获取最近的事件"""
        group_episodes = [
            e for e in self.memories
            if e["group_id"] == group_id
        ]
        return sorted(
            group_episodes,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
