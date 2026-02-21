from functools import lru_cache
from nonebot import get_plugin_config
from pydantic import BaseModel, Field
from typing import Optional


class Config(BaseModel):
    # 数据库配置
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=3306)
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
    
    # LLM Cache 配置
    cache_similarity_threshold: float = Field(default=0.85)
    
    # 检索配置
    retrieval_score_threshold: float = Field(default=0.7, description="向量检索相似度阈值")
    retrieval_use_compression: bool = Field(default=True, description="是否使用上下文压缩")
    retrieval_use_hybrid_search: bool = Field(default=True, description="是否使用混合检索（向量+重排序）")

    # LangSmith 配置
    langsmith_api_key: Optional[str] = Field(default=None)
    langsmith_project: Optional[str] = Field(default="llm-scribe")
    
    # 忽略的 QQ 号列表
    ignore_qq: set = Field(default_factory=lambda: {3674697536, 2303866129})


@lru_cache()
def get_config():
    return get_plugin_config(Config)