from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# 全局时区（上海）
CN_TZ = ZoneInfo("Asia/Shanghai")

def unix_to_shanghai(ts: int) -> datetime:
    """UNIX 秒 → 上海 datetime"""
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(CN_TZ)

def shanghai_to_unix(dt: datetime) -> int:
    """上海 datetime → UNIX 秒"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CN_TZ)
    return int(dt.timestamp())

def now_shanghai() -> datetime:
    """当前上海时区时间"""
    return datetime.now(CN_TZ)
