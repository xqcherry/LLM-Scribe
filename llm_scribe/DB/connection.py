import pymysql

DB_CONFIG = {
    "host": "100.103.229.56",
    "port": 3307,
    "user": "gxuicpc",
    "password": "gxuicpc",
    "database": "diting_qq_bot",
    "charset": "utf8mb4"
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)