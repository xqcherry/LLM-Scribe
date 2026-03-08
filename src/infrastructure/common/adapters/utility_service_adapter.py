from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ....application.ports.utility_service_port import UtilityServicePort


class UtilityServiceAdapter(UtilityServicePort):
    """通用工具能力适配器。"""

    CN_TZ = ZoneInfo("Asia/Shanghai")

    def now_shanghai(self) -> datetime:
        return datetime.now(self.CN_TZ)

    def unix_to_shanghai(self, ts: int) -> datetime:
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(self.CN_TZ)

    def shanghai_to_unix(self, dt: datetime) -> int:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.CN_TZ)
        return int(dt.timestamp())
