from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMCacheInterface(ABC):
    """LLM 结果缓存抽象接口。"""

    @abstractmethod
    def get(self, group_id: int, messages: List[Dict]) -> Optional[Dict[str, Any]]:
        """按群与消息集合进行语义检索，命中则返回缓存摘要与元数据。"""

    @abstractmethod
    def put(
        self,
        group_id: int,
        hours: int,
        messages: List[Dict],
        summary: str,
        metadata: Dict | None = None,
        ttl: int = 86400,
    ) -> None:
        """写入摘要缓存。"""

