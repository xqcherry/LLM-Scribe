try:
    import asyncio
    from nonebot import on_command
    from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
    from nonebot.log import logger
    from nonebot.params import CommandArg
    from llm_scribe.main.manger import run as summarize_group

    smy_cmd = on_command("sum", aliases={"summary"}, block=True)

    @smy_cmd.handle()
    async def _(event: GroupMessageEvent, args: Message = CommandArg()):
        group_id = event.group_id
        text = args.extract_plain_text().strip()
        hours = 24

        if text:
            try:
                hours = int(text)
                if hours <= 0 or hours > 24:
                    await smy_cmd.send("无效参数,请输入1~24h")
                    return
            except ValueError:
                await smy_cmd.send("参数必须是数字1~24h")
                return
        try:
            loop = asyncio.get_running_loop()
            summary_text = await loop.run_in_executor(None, summarize_group, group_id, hours)

            if summary_text and isinstance(summary_text, str):
                preview = summary_text[:1500]
                await smy_cmd.send(f"群聊摘要结果：\n\n{preview}")
            else:
                await smy_cmd.send("未生成有效摘要内容。")

        except Exception as e:
            logger.error(f"[ChatSummarizer] 群 {group_id} 摘要生成失败: {e}")
            await smy_cmd.send(f"摘要生成失败: {e}")

except Exception as e:
    pass
