from pydantic import BaseModel


class MessageModel(BaseModel):
    """消息数据模型"""
    user_id: int
    sender_nickname: str
    raw_message: str
    time: int

    class Config:
        json_scheme_extra = {
            "example": {
                "user_id": 123456,
                "sender_nickname": "用户A",
                "raw_message": "这是一条消息",
                "time": 1704067200
            }
        }