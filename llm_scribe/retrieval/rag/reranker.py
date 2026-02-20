"""重排序器"""
from typing import List
from langchain.schema import Document


class Reranker:
    """重排序器（简化版，实际可以使用更复杂的算法）"""
    
    def rerank(
        self,
        documents: List[Document],
        query: str,
        top_k: int = 3
    ) -> List[Document]:
        """重排序文档"""
        # 简化实现：按相似度分数排序（如果文档有 score）
        # 实际可以使用 CrossEncoder 等更复杂的重排序模型
        
        if not documents:
            return []
        
        # 如果有 score，按 score 排序
        scored_docs = []
        for doc in documents:
            score = getattr(doc.metadata, 'score', 0.5)
            scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for _, doc in scored_docs[:top_k]]
