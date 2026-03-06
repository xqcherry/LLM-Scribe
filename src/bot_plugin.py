import asyncio
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, Bot
from nonebot.log import logger
from nonebot.params import CommandArg

from src.application.services.group_summary_app_service import (
    GroupSummaryApplicationService,
)


smy_cmd = on_command("sum", aliases={"summary"}, block=True)

logger.success("[LLM-Scribe] 命令 sum/summary 已注册")

HELP_TEXT = (
    "[llm-Scribe 摘要帮助]\n"
    "\n"
    "/sum           默认近 6 小时\n"
    "/sum 12        最近 12 小时\n"
    "/sum day / d   最近 24 小时\n"
    "/sum help / ls 查看帮助\n"
    "(只支持 1~24 小时的整数)\n"
)

# 应用服务实例（当前为无状态实现，可直接复用）
_summary_app_service = GroupSummaryApplicationService()


@smy_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    group_id = event.group_id
    text = args.extract_plain_text().strip()
    hours = 6

    if text.lower() in ["help", "h", "ls", "?", "帮助"]:
        await smy_cmd.send(HELP_TEXT)
        return

    if text.lower() in ["day", "d"]:
        hours = 24

    elif text:
        try:
            hours = int(text)
            if hours <= 0 or hours > 24:
                await smy_cmd.send("只支持1~24h间整数查询")
                return
        except ValueError:
            await smy_cmd.send("参数必须是整数，例如：/sum 6\n输入 /sum ls 查看用法")
            return

    try:
        # 通过应用服务层调用摘要用例（内部仍然使用 SummaryGraph）
        summary_result = await _summary_app_service.summarize_group(group_id, hours)
        summary_text = summary_result.summary_text

        if not summary_text or not isinstance(summary_text, str):
            await smy_cmd.send("未生成有效摘要内容。")
            return

        # 直接以文本形式发送摘要（按段落拆分，避免单条过长）
        await send_parts(bot, event, summary_text.split("\n\n"))
        return

    except Exception as e:
        logger.error(f"[LLM-Scribe] 群 {group_id} 摘要生成失败: {e}")
        await smy_cmd.send(f"摘要生成失败: {e}")


async def send_parts(bot, event, parts):
    for p in parts:
        p = p.strip()
        if not p:
            continue
        await bot.send(event, p)
        await asyncio.sleep(1)
