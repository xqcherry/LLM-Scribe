"""
LLM 摘要缓存的基础设施实现。

这里通过适配器的方式，复用现有的 `RedisSemanticCache` 实现，
并将其暴露为领域层的 `LLMCacheInterface`。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.domain.services.cache_service import LLMCacheInterface
from src.infrastructure.cache.detail.semantic_cache import RedisSemanticCache


class RedisLLMCache(LLMCacheInterface):
    """基于 Redis 的 LLM 结果缓存实现。"""

    def __init__(self, inner: RedisSemanticCache | None = None) -> None:
        self._inner = inner or RedisSemanticCache()

    def get(self, group_id: int, messages: List[Dict]) -> Optional[Dict[str, Any]]:
        return self._inner.get(group_id=group_id, messages=messages)

    def put(
        self,
        group_id: int,
        hours: int,
        messages: List[Dict],
        summary: str,
        metadata: Dict | None = None,
        ttl: int = 86400,
    ) -> None:
        self._inner.put(
            group_id=group_id,
            hours=hours,
            messages=messages,
            summary=summary,
            metadata=metadata or {},
            ttl=ttl,
        )

