"""
混合检索基础设施实现。

通过组合现有的 `RAGRetriever` 与 `HybridSearch`，实现
领域层定义的 `RetrievalInterface`。
"""

from __future__ import annotations

from typing import List

from langchain_core.documents import Document

from src.domain.services.retrieval_service import RetrievalInterface
from src.infrastructure.retrieval.hybrid_search import HybridSearch
from src.infrastructure.retrieval.rag_retriever import RAGRetriever


class HybridRetriever(RetrievalInterface):
    """基于向量检索 + 重排序的混合检索实现。"""

    def __init__(
        self,
        rag_retriever: RAGRetriever,
        use_hybrid: bool = True,
    ) -> None:
        self._rag_retriever = rag_retriever
        self._use_hybrid = use_hybrid
        self._hybrid = HybridSearch(rag_retriever) if use_hybrid else None

    async def retrieve(
        self,
        query: str,
        group_id: int,
        top_k: int = 5,
    ) -> List[Document]:
        if self._use_hybrid and self._hybrid is not None:
            return await self._hybrid.search(
                query=query,
                group_id=group_id,
                top_k=top_k,
            )

        # 回退到纯 RAG 检索
        return await self._rag_retriever.retrieve_relevant_context(
            query=query,
            group_id=group_id,
            top_k=top_k,
        )

