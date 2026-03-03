"""
记忆系统基础设施实现。

从原先的 `src.memory.manager` 迁移而来，统一对接领域接口。
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from src.domain.services.memory_service import MemoryManagerInterface
from src.infrastructure.memory.vector_store import VectorMemoryStore
from src.infrastructure.memory.detail.episodic_memory import EpisodicMemory
from src.infrastructure.memory.detail import SemanticMemory
from src.infrastructure.memory.detail.memory_compressor import MemoryCompressor


class DefaultMemoryManager(MemoryManagerInterface):
    """默认的记忆管理实现。"""

    def __init__(
        self,
        vector_store: VectorMemoryStore | None = None,
        compression_llm: Any | None = None,
    ) -> None:
        self.vector_store = vector_store or VectorMemoryStore()
        self.compressor = (
            MemoryCompressor(compression_llm) if compression_llm else None
        )

    def add_memory(
        self,
        group_id: int,
        messages: List[Dict],
        summary: str,
        concepts: List[str] | None = None,
        events: List[Dict] | None = None,
        metadata: Dict | None = None,
    ) -> None:
        timestamp = int(time.time())
        EpisodicMemory.add_episodic(
            group_id,
            messages,
            summary,
            timestamp,
        )

        if concepts:
            SemanticMemory.add_concepts(group_id, concepts)

        if events:
            for event in events:
                SemanticMemory.add_event(
                    group_id,
                    event.get("event", ""),
                    event.get("participants", []),
                    event.get("timestamp", timestamp),
                )

        vector_metadata = {
            "timestamp": timestamp,
            "concepts": concepts or [],
            "events": events or [],
            **(metadata or {}),
        }
        self.vector_store.add_summary(
            group_id,
            summary,
            vector_metadata,
        )

    @property
    def vector_store_instance(self) -> VectorMemoryStore:
        return self.vector_store
