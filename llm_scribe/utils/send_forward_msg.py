from nonebot import logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
    Message
)

class SendForwardMsg:
    @staticmethod
    async def by_onebot_api(bot: Bot, event: MessageEvent, messges: list, group_id: str, user_id: str):
        """发送合并转发消息"""
        def to_node(name: str, uin: str, message: Message):
            """构建统一的格式"""
            return {
                "type": "node",
                "data": {"name": name, "uin": uin, "content": message},
            }

        info = await bot.get_login_info()
        name = info['nickname']
        uin = bot.self_id

        # 构建消息节点
        message_nodes = [to_node(name=name, uin=uin, message=Message(message)) for message in messges]

        if isinstance(event, GroupMessageEvent):
            await bot.call_api("send_group_forward_msg", group_id=group_id, messages=message_nodes)
        else:
            await bot.call_api("send_private_forward_msg", user_id=user_id, messages=message_nodes)

    @staticmethod
    async def by_napcat_api(
        messages: list[str],
        prompt: str = "prompt",
        summary: str = "查看聊天消息",
        source: str = "群聊的聊天消息",
        news: list[str] = ["查看记录"]
    ):
        return

send_forward_msg = SendForwardMsg()
