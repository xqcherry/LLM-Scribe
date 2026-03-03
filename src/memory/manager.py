import time
from typing import List, Dict, Optional
from src.memory.detail.episodic_memory import EpisodicMemory
from src.memory.detail.semantic_memory import SemanticMemory
from src.memory.detail.memory_compressor import MemoryCompressor
from src.memory.vector.vector_store import VectorMemoryStore


class MemoryManager:
    """记忆管理器：统一管理各种记忆（事件记忆、语义记忆、向量存储）"""
    
    def __init__(
        self,
        vector_store: VectorMemoryStore = None,
        compression_llm = None
    ):
        self.vector_store = vector_store or VectorMemoryStore()
        self.compressor = MemoryCompressor(compression_llm) \
                            if compression_llm else None
    
    def add_memory(
        self,
        group_id: int,
        messages: List[Dict],
        summary: str,
        concepts: List[str] = None,
        events: List[Dict] = None,
        metadata: Dict = None
    ):

        timestamp = int(time.time())
        EpisodicMemory.add_episodic(
            group_id,
            messages,
            summary,
            timestamp
        )

        if concepts:
            SemanticMemory.add_concepts(group_id, concepts)
        
        if events:
            for event in events:
                SemanticMemory.add_event(
                    group_id,
                    event.get("event", ""),
                    event.get("participants", []),
                    event.get("timestamp", timestamp)
                )

        vector_metadata = {
            "timestamp": timestamp,
            "concepts": concepts or [],
            "events": events or [],
            **(metadata or {})
        }
        self.vector_store.add_summary(
            group_id,
            summary,
            vector_metadata
        )
    
    def get_memory_context(
        self,
        group_id: int,
        query: str,
        top_k: int = 3
    ) -> str:

        docs = self.vector_store.search_similar_summaries(
            query,
            group_id,
            top_k
        )
        
        contexts = [doc.page_content for doc in docs]
        return "\n\n".join(contexts)

    @staticmethod
    def get_recent_episodes(
        group_id: int,
        limit: int = 5
    ) -> List[Dict]:

        return EpisodicMemory.get_episodic(group_id, limit)

    @staticmethod
    def get_concepts(group_id: int) -> List[Dict]:

        return SemanticMemory.get_concepts(group_id)

    @staticmethod
    def get_recent_events(
        group_id: int,
        limit: int = 10
    ) -> List[Dict]:

        return SemanticMemory.get_events(group_id, limit)
    
    async def compress_memories(
        self,
        summaries: List[str],
        max_length: int = 500
    ) -> Optional[str]:

        if not self.compressor:
            return None

        if not MemoryCompressor.is_compress(summaries):
            return summaries[0] if summaries else ""

        return await self.compressor.compress_summaries(summaries, max_len=max_length)
    
    @property
    def vector_store_instance(self) -> VectorMemoryStore:
        return self.vector_store