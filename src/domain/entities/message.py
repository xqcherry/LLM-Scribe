"""
消息相关领域实体。

在领域层直接定义消息模型，避免依赖 core 层实现。
"""

from pydantic import BaseModel


class Message(BaseModel):
    """领域层的群消息实体。"""

    user_id: int
    sender_nickname: str
    raw_message: str
    time: int

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456,
                "sender_nickname": "用户A",
                "raw_message": "这是一条消息",
                "time": 1704067200,
            }
        }

