from typing import List, Dict, Any
from langchain_core.documents import Document
from llm_scribe.retrieval.rag.retriever import RAGRetriever
from llm_scribe.retrieval.rag.reranker import Reranker


class HybridSearch:
    """混合检索：结合向量粗排与关键词精排"""
    
    def __init__(
            self,
            rag_retriever: RAGRetriever,
            reranker: Reranker = None,
            retrieval_multiplier: float = 3.0
    ):
        self.rag_retriever = rag_retriever
        self.reranker = reranker or Reranker(use_simple_rerank=True)
        self.retrieval_multiplier = retrieval_multiplier
    
    async def search(
        self,
        query: str,
        group_id: int,
        top_k: int = 5,
        use_rerank: bool = True
    ) -> List[Document]:

        # 1. RAG 检索 (粗排)
        retrievers_k = int(top_k * self.retrieval_multiplier)
        rag_results = await self.rag_retriever.retrieve_relevant_context(
            query=query,
            group_id=group_id,
            top_k=retrievers_k,
        )

        if not rag_results:
            return []

        # 2. 重排序 (精排)
        if use_rerank and len(rag_results) > top_k:
            reranked = self.reranker.rerank(
                documents=rag_results,
                query=query,
                top_k=top_k
            )
            return reranked

        return rag_results[:top_k]

    async def search_with_metadata(
            self,
            query: str,
            group_id: int,
            top_k: int = 5,
            use_rerank: bool = True
    ) -> Dict[str, Any]:

        documents = await self.search(query, group_id, top_k, use_rerank)

        return {
            "documents": documents,
            "count": len(documents),
            "query": query,
            "group_id": group_id,
            "used_rerank": use_rerank,
            "config": {
                "multiplier": self.retrieval_multiplier,
                "score_threshold": self.rag_retriever.score_threshold
            }
        }