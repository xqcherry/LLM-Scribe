"""
检索系统领域接口。

用于从长期记忆 / 向量库中检索与当前摘要相关的上下文。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document


class RetrievalInterface(ABC):
    """检索抽象接口。"""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        group_id: int,
        top_k: int = 5,
    ) -> List[Document]:
        """检索与查询最相关的文档列表。"""

