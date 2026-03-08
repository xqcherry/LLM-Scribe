from __future__ import annotations

from typing import Protocol

from ...domain.entities.summary_result import SummaryResult


class SummaryGeneratorPort(Protocol):
    """摘要生成端口：应用层依赖的抽象接口。"""

    async def generate_summary(self, group_id: int, hours: int) -> SummaryResult:
        """生成结构化摘要结果。"""
        ...
