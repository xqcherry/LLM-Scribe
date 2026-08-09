from __future__ import annotations

from typing import Optional

import aiomysql

from ...config import plugin_config as config

_pool: Optional[aiomysql.Pool] = None


def _load_db_config() -> dict:
    return {
        "host": config.db_host,
        "port": config.db_port,
        "user": config.db_user,
        "password": config.db_password,
        "db": config.db_name,
        "charset": config.db_charset,
        "autocommit": True,
    }


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = await aiomysql.create_pool(minsize=1, maxsize=10, **_load_db_config())
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None and not _pool.closed:
        _pool.close()
        await _pool.wait_closed()
    _pool = None
