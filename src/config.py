import os
from pathlib import Path
from typing import Set
from pydantic import BaseModel, Field
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config(BaseModel):
    # 数据库配置
    db_host: str = Field(
        default=os.getenv("DB_HOST", "127.0.0.1"),
        description="MySQL 主机地址"
    )
    db_port: int = Field(
        default=int(os.getenv("DB_PORT", "3308")),
        description="MySQL 端口"
    )
    db_user: str = Field(
        default=os.getenv("DB_USER", ""),
        description="MySQL 用户名"
    )
    db_password: str = Field(
        default=os.getenv("DB_PASSWORD", ""),
        description="MySQL 密码"
    )
    db_name: str = Field(
        default=os.getenv("DB_NAME", ""),
        description="数据库名"
    )
    db_charset: str = Field(
        default=os.getenv("DB_CHARSET", "utf8mb4"),
        description="数据库字符集"
    )

    # 通用 LLM 提供方 API
    llm_api_key: str = Field(
        default=os.getenv("LLM_API_KEY"),
        description="通用 LLM API Key",
    )

    ignore_qq: Set[int] = Field(
        default_factory=lambda: set(
            int(x.strip()) for x in os.getenv("IGNORE_QQ", "").split(",") if x.strip()
        )
    )


def _get_plugin_config() -> Config:
    try:
        from nonebot import get_driver, get_plugin_config
        if get_driver():
            return get_plugin_config(Config)
    except (ImportError, ValueError, RuntimeError):
        pass

    return Config()

plugin_config = _get_plugin_config()