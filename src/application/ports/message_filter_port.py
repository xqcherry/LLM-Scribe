from __future__ import annotations

from typing import Any, Dict, List, Protocol


class MessageFilterPort(Protocol):
    """消息过滤端口：应用层依赖的抽象接口。"""

    def filter_and_clean(self, raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤并清洗原始消息，返回可用于摘要的消息列表。"""
        ...
