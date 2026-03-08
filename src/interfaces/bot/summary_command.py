import base64

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.log import logger
from nonebot.params import CommandArg

from ...application.services.summary_report_app_service import (
    SummaryReportApplicationService,
)


smy_cmd = on_command("sum", aliases={"summary"}, block=True)

logger.success("[LLM-Scribe] 命令 sum/summary 已注册")

MAX_HOURS = 72
DEFAULT_HOURS = 6
HELP_TEXT = (
    "[llm-Scribe 摘要帮助]\n"
    "\n"
    "/sum             默认近 6 小时\n"
    "/sum 12          最近 12 小时\n"
    "/sum day / d     最近 24 小时\n"
    "/sum 72          最近 3 天\n"
    "/sum help / ls   查看帮助\n"
    f"(只支持 1~{MAX_HOURS} 小时的整数)\n"
)

_summary_report_service = SummaryReportApplicationService()


@smy_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if bot is None or event is None:
        logger.error("[LLM-Scribe] 收到空 bot/event，上下文异常")
        return

    group_id = getattr(event, "group_id", None)
    if group_id is None:
        logger.error("[LLM-Scribe] 事件中缺少 group_id，无法生成群摘要")
        await smy_cmd.send("当前上下文不是有效群聊，无法生成摘要。")
        return

    if _summary_report_service is None:
        logger.error("[LLM-Scribe] SummaryReportApplicationService 未初始化")
        await smy_cmd.send("摘要服务当前不可用，请稍后再试。")
        return

    text = args.extract_plain_text().strip() if args else ""
    hours = DEFAULT_HOURS

    if text.lower() in ["help", "h", "ls", "?", "帮助"]:
        await smy_cmd.send(HELP_TEXT)
        return

    if text.lower() in ["day", "d"]:
        hours = 24
    elif text:
        try:
            hours = int(text)
            if hours <= 0 or hours > MAX_HOURS:
                await smy_cmd.send(f"只支持 1~{MAX_HOURS} 小时的整数查询（最高 3 天）")
                return
        except ValueError:
            await smy_cmd.send(
                f"参数必须是整数，例如：/sum 6\n输入 /sum ls 查看用法（最高 {MAX_HOURS} 小时）"
            )
            return

    try:
        summary_result, image_bytes = await _summary_report_service.summarize_and_render_image(
            group_id=group_id,
            hours=hours,
        )

        if summary_result is None:
            logger.warning(f"[LLM-Scribe] 群 {group_id} 摘要结果为空")

        if not image_bytes or not isinstance(image_bytes, (bytes, bytearray)):
            logger.error(f"[LLM-Scribe] 群 {group_id} 图片渲染失败或返回为空")
            await smy_cmd.send("摘要渲染失败，未生成图片，请稍后重试。")
            return

        image_b64 = base64.b64encode(bytes(image_bytes)).decode("utf-8")
        if not image_b64:
            logger.error(f"[LLM-Scribe] 群 {group_id} 图片 base64 编码为空")
            await smy_cmd.send("摘要渲染失败，图片编码异常，请稍后重试。")
            return

        await bot.send(event, MessageSegment.image(f"base64://{image_b64}"))

    except Exception as e:
        logger.exception(f"[LLM-Scribe] 群 {group_id} 摘要生成失败: {e}")
        await smy_cmd.send("摘要生成失败，请稍后重试。")
