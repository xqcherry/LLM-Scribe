import os
from pathlib import Path
from typing import Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config(BaseModel):
    # 数据库配置
    db_host: str = Field(default="localhost", description="MySQL 主机地址")
    db_port: int = Field(default=3306, description="MySQL 端口")
    db_user: str = Field(default=os.getenv("DB_USER", ""), description="MySQL 用户名")
    db_password: str = Field(default=os.getenv("DB_PASSWORD", ""), description="MySQL 密码")
    db_name: str = Field(default=os.getenv("DB_NAME", ""), description="数据库名")
    db_charset: str = Field(default="utf8mb4", description="数据库字符集")

    # Moonshot API
    moonshot_api_key: str = Field(
        default=os.getenv("MOONSHOT_API_KEY", ""),
        description="Moonshot API Key"
    )

    # Redis 配置
    redis_host: str = Field(default=os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = Field(default=int(os.getenv("REDIS_PORT", 6379)))
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=os.getenv("REDIS_PASSWORD", None))

    # ChromaDB 配置
    chroma_host: str = Field(default=os.getenv("CHROMA_HOST", "localhost"))
    chroma_port: int = Field(default=int(os.getenv("CHROMA_PORT", 8000)))
    chroma_collection_name: str = Field(default="group_summaries")

    # HuggingFace 配置
    huggingface_model_name: str = Field(
        default=os.getenv("HUGGINGFACE_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
        description="模型名称或本地路径"
    )
    huggingface_model_kwargs: Dict[str, Any] = Field(
        default_factory=lambda: {"device": "cpu"},
        description="模型运行参数"
    )

    # LLM Cache 配置
    cache_similarity_threshold: float = Field(default=0.85)

    # 检索配置
    retrieval_score_threshold: float = Field(default=0.7)
    retrieval_use_compression: bool = Field(default=True)
    retrieval_use_hybrid_search: bool = Field(default=True)

    # 忽略的 QQ 号列表
    ignore_qq: Set[int] = Field(default_factory=set)


def _get_plugin_config() -> Config:
    try:
        from nonebot import get_driver, get_plugin_config
        if get_driver():
            return get_plugin_config(Config)
    except (ImportError, ValueError, RuntimeError):
        pass

    return Config()

plugin_config = _get_plugin_config()