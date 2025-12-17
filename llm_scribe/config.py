from functools import lru_cache

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):

    # 数据库配置
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_charset: str

    # Moonshot API Key
    moonshot_api_key: str


@lru_cache()
def get_config():

    return get_plugin_config(Config)

