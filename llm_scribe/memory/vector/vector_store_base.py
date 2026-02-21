"""向量存储抽象基类"""
from abc import ABC, abstractmethod
from typing import List, Dict
from langchain.schema import Document


class BaseVectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def add_summary(
        self,
        group_id: int,
        summary: str,
        metadata: Dict
    ):
        """添加摘要"""
        pass
    
    @abstractmethod
    def search_similar_summaries(
        self,
        query: str,
        group_id: int,
        top_k: int = 3
    ) -> List[Document]:
        """搜索相似摘要"""
        pass
