"""记忆管理器"""
import time
from typing import List, Dict, Optional
from llm_scribe.memory.detail.episodic_memory import EpisodicMemory
from llm_scribe.memory.detail.semantic_memory import SemanticMemory
from llm_scribe.memory.detail.memory_compressor import MemoryCompressor
from llm_scribe.memory.vector.vector_store import VectorMemoryStore


class MemoryManager:
    """记忆管理器：统一管理各种记忆（事件记忆、语义记忆、向量存储）"""
    
    def __init__(
        self,
        vector_store: VectorMemoryStore = None,
        compression_llm = None
    ):
        """
        初始化记忆管理器
        
        Args:
            vector_store: 向量存储实例，如果为 None 则创建默认实例
            compression_llm: 用于记忆压缩的 LLM，如果为 None 则不启用压缩
        """
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
        events: List[Dict] = None,
        metadata: Dict = None
    ):
        """
        添加记忆到所有子系统
        
        Args:
            group_id: 群组 ID
            messages: 消息列表
            summary: 摘要文本
            concepts: 提取的概念列表（可选）
            events: 事件列表（可选）
            metadata: 额外的元数据（可选）
        """
        timestamp = int(time.time())
        
        # 添加到事件记忆（持久化到 MySQL）
        self.episodic.add_episode(
            group_id,
            messages,
            summary,
            timestamp
        )
        
        # 添加到语义记忆（持久化到 MySQL）
        if concepts:
            self.semantic.add_concepts(group_id, concepts)
        
        if events:
            for event in events:
                self.semantic.add_event(
                    group_id,
                    event.get("event", ""),
                    event.get("participants", []),
                    event.get("timestamp", timestamp)
                )
        
        # 添加到向量存储（持久化到 ChromaDB）
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
        """
        获取记忆上下文（从向量存储检索）
        
        Args:
            group_id: 群组 ID
            query: 查询文本
            top_k: 返回最相关的 k 条记录
            
        Returns:
            拼接后的上下文文本
        """
        docs = self.vector_store.search_similar_summaries(
            query,
            group_id,
            top_k
        )
        
        contexts = [doc.page_content for doc in docs]
        return "\n\n".join(contexts)
    
    def get_recent_episodes(
        self,
        group_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """
        获取最近的事件记忆
        
        Args:
            group_id: 群组 ID
            limit: 返回数量限制
            
        Returns:
            事件记忆列表
        """
        return self.episodic.get_recent_episodes(group_id, limit)
    
    def get_concepts(self, group_id: int) -> List[str]:
        """
        获取群组的概念列表
        
        Args:
            group_id: 群组 ID
            
        Returns:
            概念列表
        """
        return self.semantic.get_concepts(group_id)
    
    def get_recent_events(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取最近的语义事件
        
        Args:
            group_id: 群组 ID
            limit: 返回数量限制
            
        Returns:
            事件列表
        """
        return self.semantic.get_recent_events(group_id, limit)
    
    def compress_memories(
        self,
        summaries: List[str],
        max_length: int = 500
    ) -> Optional[str]:
        """
        压缩多个记忆摘要
        
        Args:
            summaries: 摘要列表
            max_length: 最大长度
            
        Returns:
            压缩后的摘要，如果未启用压缩则返回 None
        """
        if not self.compressor:
            return None
        
        if not self.compressor.should_compress(summaries):
            return summaries[0] if summaries else ""
        
        # 注意：这是异步方法，但这里返回协程对象
        # 实际使用时需要 await
        return self.compressor.compress_summaries(summaries, max_length)
    
    @property
    def vector_store_instance(self) -> VectorMemoryStore:
        """获取向量存储实例（用于需要直接访问的场景）"""
        return self.vector_store