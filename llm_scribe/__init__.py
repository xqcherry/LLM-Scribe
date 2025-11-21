import asyncio
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, Bot
from nonebot.log import logger
from nonebot.params import CommandArg
from .utils.send_forward_msg import send_forward_msg

smy_cmd = on_command("sum", aliases={"summary"}, block=True)

logger.success("[llm_scribe] 命令 sum/summary 已注册")

HELP_TEXT = (
    "【LLM-Scribe 摘要帮助】\n"
    "用法：\n"
    "  /sum              → 默认近 6 小时摘要\n"
    "  /sum 12           → 摘要最近 12 小时消息\n"
    "  /sum day / d      → 摘要最近 24 小时（相当于 /sum 24）\n"
    "  /sum help / ls    → 显示此帮助\n"
    "\n"
    "范围：1~24 小时，不支持浮点数\n"
)

@smy_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):

    from .main.manger import run

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
        loop = asyncio.get_running_loop()
        summary_text = await loop.run_in_executor(None, run, group_id, hours)

        if not summary_text or not isinstance(summary_text, str):
            await smy_cmd.send("未生成有效摘要内容。")
            return

        # 分段提取
        parts = extract_parts(summary_text)

        # 合并转发
        await send_forward_msg.by_onebot_api(
            bot=bot,
            event=event,
            messges=parts,
            group_id=str(event.group_id),
            user_id=str(event.user_id)
        )
        return

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