import asyncio
import aiohttp
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, Bot, MessageSegment
from nonebot.log import logger
from nonebot.params import CommandArg
from .utils.send_forward_msg import send_forward_msg

# cvmd 接口配置（和剪切板插件一致即可）
CVMD_URL = "http://8.163.30.212:1145/api/generate-markdown-image"
CVMD_TIMEOUT = 30

smy_cmd = on_command("sum", aliases={"summary"}, block=True)

logger.success("[llm_scribe] 命令 sum/summary 已注册")

HELP_TEXT = (
    "[LLM-Scribe 摘要帮助]\n"
    "\n"
    "/sum           默认近 6 小时\n"
    "/sum 12        最近 12 小时\n"
    "/sum day / d   最近 24 小时\n"
    "/sum help / ls 查看帮助\n"
    "(只支持 1~24 小时的整数)\n"
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

        # 旧逻辑：分段 + 合并转发长文本
        # parts = extract_parts(summary_text)
        # await send_forward_msg.by_onebot_api(
        #     bot=bot,
        #     event=event,
        #     messges=parts,
        #     group_id=str(event.group_id),
        #     user_id=str(event.user_id)
        # )

        # 新逻辑：先分段，再对每一段分别使用 cvmd 接口生成多张图片发送
        parts = extract_parts(summary_text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            await send_summary_as_cvmd(bot, event, part)
            await asyncio.sleep(0.5)
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


async def send_summary_as_cvmd(bot: Bot, event: GroupMessageEvent, summary_text: str):
    """
    调用 cvmd 接口把摘要渲染成图片并发送
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                CVMD_URL,
                json={"content": summary_text},
                timeout=CVMD_TIMEOUT,
            ) as res:
                if res.status != 200:
                    await smy_cmd.send(f"cvmd 生成图片失败，HTTP {res.status}")
                    return

                img_bytes = await res.read()

        await bot.send(event, MessageSegment.image(img_bytes))
    except Exception as e:
        logger.error(f"[llm_scribe] 调用 cvmd 接口生成图片失败: {e}")
        await smy_cmd.send(f"生成图片失败：{e}")