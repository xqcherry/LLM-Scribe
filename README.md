LLM-Scribe
==========

LLM-Scribe 是一个适配 NoneBot + OneBot (QQ) 的群聊摘要插件。它会抓取指定时间窗口内的群消息，调用 Moonshot LLM 生成高密度摘要，并利用数据库缓存与“短/长期记忆”来避免重复推理。

功能亮点
--------
- `/sum` 命令即可生成最近 1~24 小时的群聊摘要，支持快捷参数（`/sum 12`、`/sum day`）。
- 智能噪声过滤：剔除 CQ 码、表情、转发、图片等低价值内容。
- 多级记忆：短期记忆记录最近摘要，长期记忆以版本号沉淀历史摘要；缓存避免重复读库。
- 自适应刷新模式：根据消息增量自动选择全量推理（High Refresh）或复用上次摘要（Low Refresh）。
- 摘要格式结构化，包含基础信息、整体摘要以及按话题拆分的结论。

目录概览
--------
- `llm_scribe/__init__.py`：注册 NoneBot 命令、参数解析、调用核心 `run()`。
- `llm_scribe/main/manger.py`：根据窗口选择刷新策略并驱动记忆/缓存逻辑。
- `llm_scribe/DB/*`：数据库连接与消息、缓存、记忆的读写。
- `llm_scribe/memory/*`：短期记忆 `memory_short`、长期记忆 `memory_long`、缓存 `cache` 以及刷新策略实现。
- `llm_scribe/Prompt/*` 与 `llm_scribe/LLM/model.py`：Moonshot 模型封装与提示词模板。
- `llm_scribe/utils/*`：消息清洗、分片、元信息、文本美化、时间换算、合并转发等工具。

环境需求
--------
- Python 3.10+
- NoneBot2 与 nonebot-adapter-onebot v11
- 主要三方依赖：`pymysql`, `langchain`, `langchain-community`, `moonshot`, `zoneinfo` (Python 3.9+ 自带), 以及一个可用的 Moonshot API Key

安装步骤
--------
1. 将 `llm_scribe` 目录放入 NoneBot 插件目录（或以包形式安装），在 `bot.py` 中 `nonebot.load_plugin("llm_scribe")`。
2. 安装依赖：
   ```
   pip install nonebot2[fastapi] nonebot-adapter-onebot pymysql langchain langchain-community
   ```
3. 复制配置模板：`cp config.env.example .env`，并在 `.env` 中填入实际密钥。
4. 按下文配置环境变量后启动 NoneBot。

环境变量与隐私
--------------
所有敏感信息已移除，请在运行环境中注入以下变量（可放入 `.env`）：

| 变量名 | 说明 |
| --- | --- |
| `DB_HOST` | MySQL 主机 |
| `DB_PORT` | MySQL 端口，整数 |
| `DB_USER` | 数据库用户名 |
| `DB_PASSWORD` | 数据库密码 |
| `DB_NAME` | 存放消息/记忆的数据库名 |
| `DB_CHARSET` | 字符集（例如 `utf8mb4`） |
| `MOONSHOT_API_KEY` | Moonshot LLM 的 API Key |

示例：`config.env.example` 提供占位符配置，复制后在 `.env` 中填入真实值：
```
cp config.env.example .env
```
（`.env` 已加入 `.gitignore`，真实密钥仅保存在本地环境。）

使用方式
--------
- `/sum`：默认 6 小时
- `/sum <n>`：最近 n 小时（1~24 的整数）
- `/sum day` 或 `/sum d`：24 小时
- `/sum help`：显示帮助

机器人会自动将摘要拆分为合并转发消息发回群里。

工作流程
--------
1. `run(group_id, hours)` 从数据库拉取消息并调用 `filter_msgs()` 做 CQ 清洗与忽略名单过滤。
2. 根据缓存/短期记忆判定刷新模式：
   - **High Refresh**：重新生成摘要，更新短期记忆、长期记忆与缓存；
   - **High Refresh Chunk**：当消息量 > 220 条时按 220/50 重叠切片分多段摘要；
   - **Low Refresh**：无新消息，仅更新时间戳并返回上次摘要。
3. `Prompt` 模块拼接系统提示与聊天文本，`LLM/model.py` 包装 Moonshot 模型进行推理。
4. `text_utils` 对输出做去 Markdown、美化、添加基础信息等处理。
5. `send_forward_msg` 调用 OneBot API 以合并转发方式发送。

开发与调试
----------
- 可在独立脚本内直接调用 `llm_scribe.main.manger.run(<group_id>, <hours>)` 获取摘要。
- `IGNORE_QQ` 位于 `llm_scribe/main/manger.py`，可按照需要扩展。
- 数据表依赖：`messages_event_logs`, `chat_cache`, `memory_short`, `memory_long`，需提前建表。
- 推荐在本地配置 `.env` 或通过进程管理器注入变量，确保敏感信息不写入代码仓库。

致谢与隐私说明
---------------
- 本仓库已清除硬编码数据库凭据与 API Key，请勿再将真实密钥写入源码。
- 部署时请限制数据库访问来源，并为机器人帐号配置必要的群权限。

