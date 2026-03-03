"""
消息仓储接口。

用于从不同存储实现中获取群聊消息，领域层仅依赖该抽象。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class MessageRepositoryInterface(ABC):
    """群消息仓储抽象接口。"""

    @abstractmethod
    def get_group_messages(self, group_id: int, hours: int = 24) -> List[Dict]:
        """按时间窗口获取指定群的消息列表。"""

    @abstractmethod
    def get_group_messages_after(self, group_id: int, timestamp: int) -> List[Dict]:
        """获取指定时间戳之后的群消息。"""

