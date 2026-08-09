import time
from typing import Any, Optional


class TTLCache:
    """带 TTL 的进程内缓存，用于 L1 最终结果与 L2 分块摘要。"""

    def __init__(self, default_ttl: float = 3600)-> None:
        self._store = dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if item is None:
            return None
        value, expire_at = item
        if time.monotonic() > expire_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expire_at = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
        self._store[key] = (value, expire_at)

    def pop(self, key: str) -> Optional[Any]:
        item = self._store.pop(key, None)
        return item[0] if item is not None else None

    def clear(self) -> None:
        self._store.clear()