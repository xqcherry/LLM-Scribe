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

        # 新逻辑：整段摘要直接使用 cvmd 接口生成一张图片发送
        await send_summary_as_cvmd(bot, event, summary_text)
        return

    except Exception as e:
        logger.error(f"[llm_scribe] 群 {group_id} 摘要生成失败: {e}")
        await smy_cmd.send(f"摘要生成失败: {e}")

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


# ==================== 本地测试代码 ====================

# if __name__ == "__main__":
#     import sys
#     import os
#
#     # 添加父目录到路径，以便导入模块
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     parent_dir = os.path.dirname(current_dir)
#     if parent_dir not in sys.path:
#         sys.path.insert(0, parent_dir)
#
#     from llm_scribe.main.manger import run
#
#     group_id = 1017750994
#     hours = 11
#
#     output_file = sys.argv[1] if len(sys.argv) >= 2 else "summary_output.txt"
#
#     summary = run(group_id, hours)
#
#     # 输出到控制台
#     print(summary)
#
#     # 保存到文件
#     with open(output_file, 'w', encoding='utf-8') as f:
#         f.write(summary)
