import os
import pymysql

ENV_MAPPING = {
    "host": "DB_HOST",
    "port": "DB_PORT",
    "user": "DB_USER",
    "password": "DB_PASSWORD",
    "database": "DB_NAME",
    "charset": "DB_CHARSET",
}


def _load_db_config():
    """Read connection settings from environment variables."""
    config = {}
    missing = []

    for key, env_key in ENV_MAPPING.items():
        value = os.getenv(env_key)
        if value is None:
            missing.append(env_key)
        else:
            config[key] = value

    if missing:
        raise RuntimeError(
            f"Missing database configuration environment variables: {', '.join(missing)}"
        )

    config["port"] = int(config["port"])
    return config


def get_connection():
    return pymysql.connect(**_load_db_config())