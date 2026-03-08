from __future__ import annotations

from datetime import datetime

from ..adapters.utility_service_adapter import UtilityServiceAdapter

_utility = UtilityServiceAdapter()


def unix_to_shanghai(ts: int) -> datetime:
    return _utility.unix_to_shanghai(ts)


def shanghai_to_unix(dt: datetime) -> int:
    return _utility.shanghai_to_unix(dt)


def now_shanghai() -> datetime:
    return _utility.now_shanghai()
