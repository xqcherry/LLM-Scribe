from functools import lru_cache

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    # 数据库配置
    db_host: str = "100.103.229.56"
    db_port: int = 3307
    db_user: str = "gxuicpc"
    db_password: str = "gxuicpc"
    db_name: str = "diting_qq_bot"
    db_charset: str = "utf8mb4"

    # Moonshot API Key
    moonshot_api_key: str = "sk-oYmzIcdwWOG8YMLkpcYTtj3sVsmkmQkCnBC1mNBTUqjXJI5k"


@lru_cache()
def get_config():
    return get_plugin_config(Config)