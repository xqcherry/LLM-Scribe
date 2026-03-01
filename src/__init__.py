import asyncio
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, Bot
from nonebot.log import logger
from nonebot.params import CommandArg

smy_cmd = on_command("sum", aliases={"summary"}, block=True)

logger.success("[llm_scribe] 命令 sum/summary 已注册")

HELP_TEXT = (
    "[llm-Scribe 摘要帮助]\n"
    "\n"
    "/sum           默认近 6 小时\n"
    "/sum 12        最近 12 小时\n"
    "/sum day / d   最近 24 小时\n"
    "/sum help / ls 查看帮助\n"
    "(只支持 1~24 小时的整数)\n"
)

@smy_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    from llm_scribe.core.graph import SummaryGraph

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
        # 使用新的 SummaryGraph 工作流
        graph = SummaryGraph()
        summary_text = await graph.invoke(group_id, hours)

        if not summary_text or not isinstance(summary_text, str):
            await smy_cmd.send("未生成有效摘要内容。")
            return

        # 直接以文本形式发送摘要（按段落拆分，避免单条过长）
        await send_parts(bot, event, summary_text.split("\n\n"))
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
