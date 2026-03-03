"""
记忆系统领域接口。

通过该抽象，可以将具体的 MemoryManager 实现放在基础设施层。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class MemoryManagerInterface(ABC):
    """记忆管理抽象接口。"""

    @property
    @abstractmethod
    def vector_store_instance(self) -> Any:
        """用于检索的向量存储实例。"""

    @abstractmethod
    def add_memory(
        self,
        group_id: int,
        messages: List[Dict],
        summary: str,
        concepts: List[str] | None = None,
        events: List[Dict] | None = None,
        metadata: Dict | None = None,
    ) -> None:
        """写入新的记忆记录。"""

