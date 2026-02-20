"""语义记忆实现"""
from typing import List, Dict, Set
from datetime import datetime


class SemanticMemory:
    """语义记忆：提取的概念和知识"""
    
    def __init__(self):
        self.concepts: Dict[int, Set[str]] = {}  # group_id -> concepts
        self.events: Dict[int, List[Dict]] = {}  # group_id -> events
        self.relationships: Dict[int, List[Dict]] = {}  # group_id -> relationships
    
    def add_concepts(self, group_id: int, concepts: List[str]):
        """添加概念"""
        if group_id not in self.concepts:
            self.concepts[group_id] = set()
        self.concepts[group_id].update(concepts)
    
    def add_event(
        self,
        group_id: int,
        event: str,
        participants: List[str],
        timestamp: int
    ):
        """添加事件"""
        if group_id not in self.events:
            self.events[group_id] = []
        
        self.events[group_id].append({
            "event": event,
            "participants": participants,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat()
        })
    
    def get_concepts(self, group_id: int) -> List[str]:
        """获取概念列表"""
        return list(self.concepts.get(group_id, set()))
    
    def get_recent_events(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """获取最近事件"""
        events = self.events.get(group_id, [])
        return sorted(
            events,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
