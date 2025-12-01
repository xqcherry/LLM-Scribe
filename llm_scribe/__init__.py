import asyncio
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, Bot
from nonebot.log import logger
from nonebot.params import CommandArg
from llm_scribe.main.manger import run as summarize_group

smy_cmd = on_command("sum", aliases={"summary"}, block=True)

@smy_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    group_id = event.group_id
    text = args.extract_plain_text().strip()
    hours = 24

    if text:
        try:
            hours = int(text)
            if hours <= 0 or hours > 24:
                await smy_cmd.send("无效参数，请输入 1~24 之间的数字，例如：/sum 6")
                return
        except ValueError:
            await smy_cmd.send("参数必须是数字，例如：/sum 6")
            return

    try:
        loop = asyncio.get_running_loop()
        summary_text = await loop.run_in_executor(None, summarize_group, group_id, hours)

        if not summary_text or not isinstance(summary_text, str):
            await smy_cmd.send("未生成有效摘要内容。")
            return

        # 分段提取
        parts = extract_parts(summary_text)

        # 单段情况：直接发送
        if len(parts) == 1:
            await bot.send(event, parts[0])
            return

        # 多段情况：逐段发送
        await send_parts(bot, event, parts)

    except Exception as e:
        logger.error(f"[llm_scribe] 群 {group_id} 摘要生成失败: {e}")
        await smy_cmd.send(f"摘要生成失败: {e}")

def extract_parts(summary: str):
    # 若不存在分段标题，直接整体输出
    if "=== 分段摘要" not in summary:
        return [summary]

    raw = summary.split("=== 分段摘要")
    parts = []

    for idx, segment in enumerate(raw):
        seg = segment.strip()
        if not seg:
            continue

        # 第一段（基础信息 + 内容）不加标签
        if idx == 0:
            parts.append(seg)
        else:
            parts.append("=== 分段摘要" + seg)

    return parts

async def send_parts(bot, event, parts):
    for p in parts:
        p = p.strip()
        if not p:
            continue
        await bot.send(event, p)
        await asyncio.sleep(1)
