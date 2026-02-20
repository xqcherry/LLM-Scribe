from functools import lru_cache
from nonebot import get_plugin_config
from pydantic import BaseModel, Field
from typing import Optional


class Config(BaseModel):
    # 数据库配置
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=3307)
    db_user: str = Field(default="root")
    db_password: str = Field(default="123456")
    db_name: str = Field(default="llm_scribe")
    db_charset: str = Field(default="utf8mb4")

    # Moonshot API
    moonshot_api_key: str = Field(default="sk-oYmzIcdwWOG8YMLkpcYTtj3sVsmkmQkCnBC1mNBTUqjXJI5k")

    # Redis 配置（用于缓存）
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)

    # ChromaDB 配置
    chroma_persist_dir: str = Field(default="./chroma_db")

    # GPTCache 配置
    gptcache_dir: str = Field(default="./gptcache_db")
    cache_similarity_threshold: float = Field(default=0.85)

    # LangSmith 配置
    langsmith_api_key: Optional[str] = Field(default=None)
    langsmith_project: Optional[str] = Field(default="llm-scribe")


@lru_cache()
def get_config():
    return get_plugin_config(Config)