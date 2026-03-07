from __future__ import annotations

from datetime import datetime
from typing import Protocol


class UtilityServicePort(Protocol):
    """通用工具能力端口。"""

    def now_shanghai(self) -> datetime:
        """获取当前上海时区时间。"""
        ...

    def unix_to_shanghai(self, ts: int) -> datetime:
        """UNIX 秒转换为上海时区 datetime。"""
        ...

    def shanghai_to_unix(self, dt: datetime) -> int:
        """上海时区 datetime 转换为 UNIX 秒。"""
        ...
