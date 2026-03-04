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

