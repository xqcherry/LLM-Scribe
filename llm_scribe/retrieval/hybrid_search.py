"""混合检索"""
from typing import List
from langchain.schema import Document
from .rag.retriever import RAGRetriever
from .rag.reranker import Reranker


class HybridSearch:
    """混合检索：结合多种检索策略"""
    
    def __init__(
        self,
        rag_retriever: RAGRetriever,
        reranker: Reranker = None
    ):
        self.rag_retriever = rag_retriever
        self.reranker = reranker or Reranker()
    
    def search(
        self,
        query: str,
        group_id: int,
        top_k: int = 5
    ) -> List[Document]:
        """混合检索"""
        # 1. RAG 检索
        rag_results = self.rag_retriever.retrieve_relevant_context(
            query,
            group_id,
            top_k * 2  # 检索更多，然后重排序
        )
        
        # 2. 重排序
        reranked = self.reranker.rerank(
            rag_results,
            query,
            top_k
        )
        
        return reranked
