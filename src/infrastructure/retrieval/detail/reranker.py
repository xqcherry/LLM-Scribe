"""
检索结果重排序实现。

从原先的 `src.retrieval.rag.reranker` 迁移而来。
"""

from typing import List

from langchain_core.documents import Document
import re


class Reranker:
    """检索相似的历史摘要。"""

    def __init__(self, use_simple_rerank: bool = True) -> None:
        self.use_simple_rerank = use_simple_rerank
        self.stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            "那",
            "群组",
            "最近",
            "小时",
            "聊天",
            "摘要",
        }

    def rerank(
        self,
        documents: List[Document],
        query: str,
        top_k: int = 3,
    ) -> List[Document]:
        """重排序文档。"""
        if not documents:
            return []
        if len(documents) <= 1:
            return documents

        scored_docs: list[tuple[float, Document]] = []
        query_keywords = self._extract_keywords(query)

        for doc in documents:
            # 基础相关性分数 (关键词匹配)
            relevance_score = self._calculate_relevance_score(
                doc.page_content, query_keywords
            )

            # 向量相似度权重 (从 Chroma 检索时自带的 score)
            vector_score = self._get_similarity_score(doc)

            # 综合评分：结合关键词和向量相似度
            final_score = (relevance_score * 0.7) + (vector_score * 0.3)

            scored_docs.append((final_score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)

        return [doc for _, doc in scored_docs[:top_k]]

    def _extract_keywords(self, query: str) -> List[str]:
        """query关键词提取。"""
        words = re.findall(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}", query.lower())
        return [w for w in words if w not in self.stop_words]

    @staticmethod
    def _calculate_relevance_score(
        content: str,
        query_keywords: List[str],
    ) -> float:
        """计算相关性分数。"""
        if not query_keywords:
            return 0.5

        # 计算覆盖率
        content_lower = content.lower()
        match_count = sum(1 for kw in query_keywords if kw in content_lower)
        coverage = match_count / len(query_keywords)

        # 计算密度：关键词出现的总频率
        # 给长文档一点“惩罚”(类似 TF-IDF 思想）
        total_hits = sum(content_lower.count(kw) for kw in query_keywords)
        density_bonus = min(total_hits / (len(content_lower) / 50 + 1), 0.5)

        return min(coverage + density_bonus, 1.0)

    @staticmethod
    def _get_similarity_score(doc: Document) -> float:
        """从 metadata 获取原始相似度。"""
        score = doc.metadata.get("score", 0.5)
        try:
            return float(score)
        except (ValueError, TypeError):
            return 0.5

