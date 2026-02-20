"""记忆管理器"""
from typing import List, Dict
from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .compression import MemoryCompressor
from .vector_store import VectorMemoryStore


class MemoryManager:
    """记忆管理器：统一管理各种记忆"""
    
    def __init__(
        self,
        vector_store: VectorMemoryStore = None,
        compression_llm = None
    ):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.vector_store = vector_store or VectorMemoryStore()
        self.compressor = MemoryCompressor(compression_llm) if compression_llm else None
    
    def add_memory(
        self,
        group_id: int,
        messages: List[Dict],
        summary: str,
        concepts: List[str] = None,
        events: List[Dict] = None
    ):
        """添加记忆"""
        import time
        
        # 添加到事件记忆
        self.episodic.add_episode(
            group_id,
            messages,
            summary,
            int(time.time())
        )
        
        # 添加到语义记忆
        if concepts:
            self.semantic.add_concepts(group_id, concepts)
        
        if events:
            for event in events:
                self.semantic.add_event(
                    group_id,
                    event.get("event", ""),
                    event.get("participants", []),
                    event.get("timestamp", int(time.time()))
                )
        
        # 添加到向量存储
        self.vector_store.add_summary(
            group_id,
            summary,
            {
                "timestamp": int(time.time()),
                "concepts": concepts or [],
                "events": events or []
            }
        )
    
    def get_memory_context(
        self,
        group_id: int,
        query: str,
        top_k: int = 3
    ) -> str:
        """获取记忆上下文"""
        # 从向量存储检索
        docs = self.vector_store.search_similar_summaries(
            query,
            group_id,
            top_k
        )
        
        contexts = [doc.page_content for doc in docs]
        return "\n\n".join(contexts)
