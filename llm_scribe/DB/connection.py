import pymysql

from ..config import get_config


def _load_db_config():
    cfg = get_config()
    return {
        "host": cfg.db_host,
        "port": int(cfg.db_port),
        "user": cfg.db_user,
        "password": cfg.db_password,
        "database": cfg.db_name,
        "charset": cfg.db_charset,
    }


def get_connection():
    return pymysql.connect(**_load_db_config())