"""重排序器"""
from typing import List, Optional
from langchain_core.documents import Document
import re


class Reranker:
    """重排序器：基于查询-文档相关性的重排序"""
    
    def __init__(self, use_simple_rerank: bool = True):
        """
        初始化重排序器
        
        Args:
            use_simple_rerank: 是否使用简单的关键词匹配重排序（True）
                              或基于相似度分数重排序（False）
        """
        self.use_simple_rerank = use_simple_rerank
    
    def rerank(
        self,
        documents: List[Document],
        query: str,
        top_k: int = 3
    ) -> List[Document]:
        """
        重排序文档
        
        Args:
            documents: 待重排序的文档列表
            query: 查询文本
            top_k: 返回前 k 个文档
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        if len(documents) <= top_k:
            return documents
        
        scored_docs = []
        query_keywords = self._extract_keywords(query)
        
        for doc in documents:
            if self.use_simple_rerank:
                # 基于关键词匹配的简单重排序
                score = self._calculate_relevance_score(doc.page_content, query_keywords)
            else:
                # 基于 metadata 中的相似度分数
                score = self._get_similarity_score(doc)
            
            scored_docs.append((score, doc))
        
        # 按分数降序排序
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for _, doc in scored_docs[:top_k]]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现：去除停用词）"""
        # 中文停用词（简化版）
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', 
                     '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', 
                     '自己', '这', '那', '群组', '最近', '小时', '聊天', '摘要'}
        
        # 提取中文和英文单词
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        
        return keywords
    
    def _calculate_relevance_score(self, content: str, query_keywords: List[str]) -> float:
        """
        计算文档与查询的相关性分数
        
        Args:
            content: 文档内容
            query_keywords: 查询关键词列表
            
        Returns:
            相关性分数 (0-1)
        """
        if not query_keywords:
            return 0.5
        
        content_lower = content.lower()
        matches = sum(1 for keyword in query_keywords if keyword in content_lower)
        
        # 归一化分数
        score = matches / len(query_keywords) if query_keywords else 0.0
        
        # 考虑关键词出现频率
        total_occurrences = sum(content_lower.count(keyword) for keyword in query_keywords)
        frequency_bonus = min(total_occurrences / (len(query_keywords) * 10), 0.3)
        
        return min(score + frequency_bonus, 1.0)
    
    def _get_similarity_score(self, doc: Document) -> float:
        """
        从文档 metadata 中获取相似度分数
        
        Args:
            doc: 文档对象
            
        Returns:
            相似度分数
        """
        if isinstance(doc.metadata, dict):
            score = doc.metadata.get('score', 0.5)
        elif hasattr(doc.metadata, 'score'):
            score = getattr(doc.metadata, 'score', 0.5)
        else:
            score = 0.5
        
        # 确保分数在合理范围内
        return max(0.0, min(1.0, float(score)))