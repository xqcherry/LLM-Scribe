"""混合检索"""
from typing import List, Optional
from langchain_core.documents import Document
from .rag.retriever import RAGRetriever
from .rag.reranker import Reranker


class HybridSearch:
    """
    混合检索：结合向量检索和重排序
    
    策略：
    1. 使用 RAGRetriever 进行向量相似度检索（检索更多候选）
    2. 使用 Reranker 进行重排序（基于关键词匹配或相似度分数）
    3. 返回最相关的 top_k 个文档
    """
    
    def __init__(
        self,
        rag_retriever: RAGRetriever,
        reranker: Reranker = None,
        retrieval_multiplier: float = 2.0
    ):
        """
        初始化混合检索
        
        Args:
            rag_retriever: RAG 检索器
            reranker: 重排序器，如果为 None 则创建默认实例
            retrieval_multiplier: 检索倍数（检索 top_k * multiplier 个候选，然后重排序到 top_k）
        """
        self.rag_retriever = rag_retriever
        self.reranker = reranker or Reranker(use_simple_rerank=True)
        self.retrieval_multiplier = retrieval_multiplier
    
    def search(
        self,
        query: str,
        group_id: int,
        top_k: int = 5,
        use_rerank: bool = True
    ) -> List[Document]:
        """
        混合检索
        
        Args:
            query: 查询文本
            group_id: 群组 ID
            top_k: 返回前 k 个文档
            use_rerank: 是否使用重排序
            
        Returns:
            检索到的文档列表
        """
        # 1. RAG 检索（检索更多候选）
        retrieval_k = int(top_k * self.retrieval_multiplier)
        rag_results = self.rag_retriever.retrieve_relevant_context(
            query,
            group_id,
            top_k=retrieval_k,
            use_rerank=False
        )
        
        if not rag_results:
            return []
        
        # 2. 重排序（如果需要）
        if use_rerank and len(rag_results) > top_k:
            reranked = self.reranker.rerank(
                rag_results,
                query,
                top_k
            )
            return reranked
        else:
            # 如果不需要重排序，直接返回
            return rag_results[:top_k]
    
    def search_with_metadata(
        self,
        query: str,
        group_id: int,
        top_k: int = 5,
        use_rerank: bool = True
    ) -> dict:
        """
        混合检索并返回元数据
        
        Args:
            query: 查询文本
            group_id: 群组 ID
            top_k: 返回前 k 个文档
            use_rerank: 是否使用重排序
            
        Returns:
            包含文档列表和元数据的字典
        """
        documents = self.search(query, group_id, top_k, use_rerank)
        
        return {
            "documents": documents,
            "count": len(documents),
            "query": query,
            "group_id": group_id,
            "used_rerank": use_rerank,
            "retrieval_multiplier": self.retrieval_multiplier
        }
