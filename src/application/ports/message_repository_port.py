from __future__ import annotations

from typing import Any, Dict, List, Protocol


class MessageRepositoryPort(Protocol):
    """群消息仓储端口：应用层依赖的抽象接口。"""

    def get_group_messages(self, group_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """按时间窗口获取指定群的消息列表。"""
        ...

    def get_group_messages_after(self, group_id: int, timestamp: int) -> List[Dict[str, Any]]:
        """获取指定时间戳之后的群消息。"""
        ...
