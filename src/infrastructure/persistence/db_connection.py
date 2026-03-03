"""
数据库连接基础设施。

从原先的 `src.storage.database.connection` 迁移而来，
保持配置与行为完全一致。
"""

import pymysql
from src.config import plugin_config as config


def _load_db_config() -> dict:
    return {
        "host": config.db_host,
        "port": config.db_port,
        "user": config.db_user,
        "password": config.db_password,
        "database": config.db_name,
        "charset": config.db_charset,
    }


def get_connection() -> pymysql.connections.Connection:
    """获取数据库连接。"""
    return pymysql.connect(**_load_db_config())

