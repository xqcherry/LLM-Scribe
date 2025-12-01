# LLM-Scribe · LangChain 驱动的群聊智能摘要管家

> 将「消息采集 → 语义抽取 → 分层记忆 → 自适应刷新 → 高质量摘要」串成闭环，可独立运行，也能嵌入 NoneBot/NapCat 实时响应群聊指令。

---

## 1. 项目概览
**LLM-Scribe** 是一个围绕 LangChain 构建的群聊摘要系统，支持多模型切换、结构化语义存储、分层记忆与可追溯的历史版本。核心目标：
- 自动拉取 MySQL 中的群聊数据，清洗噪声，构造语义上下文；
- 调度主流 LLM（Moonshot / OpenAI / DeepSeek / Qwen / GLM / Claude / Gemini / Ollama）生成高信息量摘要；
- 将结果写入短期、长期记忆，结合缓存策略降低 Token 消耗；
- 对接 NoneBot 指令，实现“随喊随有”的聊天复盘体验。

---

## 2. 核心能力
- **多模型 LangChain 中枢**：通过 `LLM_PROVIDER` 动态切换模型，所有调用遵循 ChatModel 接口规范，可与其他 LangChain Chain 复用。
- **分层记忆引擎**：短期记忆维护最新语义池，长期记忆记录版本化摘要，`chat_cache` 避免重复查询 MySQL。
- **自适应刷新策略**：根据窗口、增量消息与请求粒度自动选择高/低刷新，并在大窗口场景中自动切片分段摘要。
- **语义抽取器**：在正式生成摘要前，先用 `Prompt/prompt3.py` 将对话拆解为 `concepts/events/quotes`，提高一致性与可解释性。
- **插件化部署**：既能 `python -m llm_scribe` 独立运行，也可放入 NoneBot `plugins/` 目录，用 NapCat/OneBot 触发 `/sum` 指令。

---

## 3. 系统架构与数据流
```
MySQL (messages_event_logs)
        │
        ▼
DB/chat_loader.py  ——>  utils/filter.py  (CQ 码 & 噪声清洗)
        │
        ▼
memory/cache.py          memory/memory_short.py        memory/memory_long.py
   (最近窗口缓存)             (短期语义池)                       (版本归档)
        │
        ▼
Prompt/prompt3.py  →  utils/tools.build_mem_json()  →  Prompt/prompt1.py
        │                                                 │
        └─────────────>  LangChain ChatModel  <───────────┘
                                  │
                                  ▼
refresh.high_refresh() / high_refresh_chunk() / low_refresh()
                                  │
                                  ▼
display_summary()  →  标准化输出（含基础信息 + 纯摘要文本）
```

---

## 4. 目录速览
```
llm_scribe/
├── __main__.py            # 独立运行入口
├── config.py              # Pydantic Settings，统一读取 .env
├── DB/
│   ├── connection.py      # MySQL 连接封装
│   └── chat_loader.py     # 消息查询与基础清洗
├── LLM/
│   └── model.py           # LangChain ChatModel 统一工厂
├── main/manger.py         # 主流程：窗口判断、刷新策略
├── memory/
│   ├── cache.py           # chat_cache 读写
│   ├── memory_short.py    # 短期记忆 + 时间戳维护
│   ├── memory_long.py     # 摘要版本归档
│   └── refresh.py         # high / chunk / low 刷新策略
├── Prompt/
│   ├── bascial_prompt.py  # 行为准则与输出模板
│   ├── prompt1.py         # 摘要生成 Prompt
│   └── prompt3.py         # 语义抽取 Prompt
└── utils/
    ├── filter.py          # CQ 码过滤
    └── tools.py           # meta 构建、chunk、摘要美化等工具
```

---

## 5. 快速开始
### 5.1 环境要求
| 组件 | 最低版本 | 说明 |
| --- | --- | --- |
| Python | 3.10 | 建议 3.10~3.12 |
| MySQL | 5.7 / 8.0 | 消息与记忆持久化 |
| NoneBot2 | 2.2 | 可选：命令入口 |
| NapCat (OneBot v11) | 2.0 | 可选：QQ 网关 |
| 操作系统 | Windows / Linux / macOS | 三平台均可 |

### 5.2 克隆与安装
```bash
git clone https://github.com/xqcherry/LLM-Scribe.git
cd LLM-Scribe
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # macOS/Linux
pip install -U pip
pip install -e .
# 或 pip install -r requirements.txt
```

### 5.3 配置 `.env`
复制示例并填写模型/数据库信息：
```bash
cp .env.example .env
```
```ini
LLM_PROVIDER=moonshot
MOONSHOT_API_KEY=your_key
MOONSHOT_MODEL=moonshot-v1-32k
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=diting_qq_bot
```
只需保证对应 Provider 的 API Key 不为空，其余会被忽略。切换模型时改 `LLM_PROVIDER` 即可（支持 `openai/deepseek/qwen/glm/claude/gemini/ollama` 等）。

### 5.4 初始化数据库
| 表 | 作用 |
| --- | --- |
| `messages_event_logs` | 原始群聊消息 |
| `chat_cache` | 最近窗口的消息快照 |
| `memory_short` | 短期记忆 + 时间戳 |
| `memory_long` | 摘要历史版本 |

可直接执行根目录 `sql/schema.sql`（如需自建，见下例）：
```mysql
CREATE TABLE messages_event_logs(
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  message_type VARCHAR(20) NOT NULL,
  group_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  sender_nickname VARCHAR(100),
  raw_message TEXT NOT NULL,
  time INT NOT NULL,
  KEY idx_group_time (group_id,time)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.5 运行方式
- **独立模式**
  ```bash
  python -m llm_scribe
  # 默认示例：group_id=123454325, hours=23，可在 __main__.py 中修改
  ```
- **NoneBot 插件模式**
  1. 在 NoneBot 项目 `.env` 内配置同样的 LLM & MySQL 字段；
  2. 将 `llm_scribe/` 拷贝到 `your_nonebot_project/plugins/`；
  3. `pyproject.toml` 中设置：
     ```toml
     [tool.nonebot]
     plugin_dirs = ["plugins"]
     ```
  4. 安装依赖：
     ```bash
     pip install nonebot2[fastapi] nonebot-adapter-onebot langchain langchain-community pymysql jieba python-dotenv
     ```
  5. 运行 `nb run`，在群内使用 `/sum` 或 `/summary 6` 触发。

### 5.6 Docker（可选）
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install -U pip && pip install -e .
CMD ["python","-m","llm_scribe.main.manger"]
```
```bash
docker build -t llm-scribe .
docker run --env-file .env llm-scribe
```

---

## 6. 工作流细节
### 6.1 消息采集与过滤
- `DB/chat_loader.py` 通过 `pymysql` 从 `messages_event_logs` 拉取最近 `hours` 小时群聊；
- `utils/filter.py` 针对 QQ `CQ:` 码、表情、图片等做可读化映射，保留有效文本。

### 6.2 语义抽取 → 摘要生成
1. `utils/tools.build_mem_json()` 将消息拼接成时序文本，并调用 `Prompt/prompt3.py (EXTRACT)` 获取 `concepts/events/quotes`；
2. `Prompt/prompt1.py` 把基础信息 + 语义片段 + 原始对话联合喂给 LLM；
3. `LLM/model.py` 根据 `LLM_PROVIDER` 构造对应的 LangChain `ChatModel`；
4. `utils/tools.beautify_smy()` 做输出清洗，确保“整体摘要 / 话题总结”格式稳定。

### 6.3 分层记忆 + 刷新策略
- **短期记忆 (`memory_short`)**：保存最近一次摘要及语义池，允许无损增量；
- **长期记忆 (`memory_long`)**：每次高刷都会写入一个自增版本号，方便回溯；
- **缓存 (`chat_cache`)**：保存上次窗口的消息快照，减少数据库读取和 Token 利用；
- **刷新策略 (`main/manger.py`)**：
  - 首次或窗口变更 → `high_refresh`，必要时 `high_refresh_chunk` 将消息按 250 条分段摘要；
  - 无增量或增量不足 10 条 → `low_refresh` 直接复用上一份摘要，仅更新时间戳；
  - 大窗口/大增量 → 重新高刷，保证语义一致性。

---

## 7. 配置详解
`llm_scribe/config.py` 使用 Pydantic Settings，支持以下关键字段：

| 字段 | 说明 |
| --- | --- |
| `LLM_PROVIDER` | 选择模型：`moonshot/openai/deepseek/qwen/glm/claude/gemini/ollama` |
| `*_API_KEY` / `*_BASE_URL` / `*_MODEL` | 各 Provider 的凭据、模型名与 Base URL |
| `MYSQL_HOST/PORT/USER/PASSWORD/DB` | MySQL 连接信息 |

若启用 Claude/Gemini，对应 LangChain 依赖需要手动安装：`pip install langchain-anthropic` / `langchain-google-genai`。

---

## 8. 开发者提示
- **Prompt 调优**：调整 `Prompt/bascial_prompt.py` 的规则段或 `Prompt/prompt1.py` 的 HumanMessage 内容即可改变输出格式。
- **自定义消息源**：若不使用 MySQL，可在 `DB/chat_loader.py` 中替换为 REST/CSV/消息队列，并保持返回 `{user_id, sender_nickname, raw_message, time}` 结构。
- **扩展刷新策略**：`memory/refresh.py` 中的 `high_refresh`/`low_refresh` 可根据需要扩展 `mid_refresh`、引入命令行参数等。
- **复用工具**：`utils/tools.chunk_msgs()` 可在其他长上下文任务里复用，快速切片对话。

---

## 9. 示例输出
```
基础信息：
- 时段：2025-11-10 10:00~12:00
- 参与：8人，共 302 条消息
- 时长：约2小时

整体摘要
围绕 LangChain 管线重构、模型接口封装与摘要准确性校验展开讨论；成员同步了缓存策略、数据库查询优化和上线计划。

话题总结
技术开发（占比45%）
- 摘要：聚焦多模型封装、NapCat 网关升级以及缓存滑动窗口实现。
- 关键点：LangChain 抽取器调试、数据库索引补齐、NoneBot 插件路径调整
- 结论：统一使用 `LLM_PROVIDER` 切换模型并在测试群验证。

摘要准确性（占比30%）
- 摘要：讨论 prompt 调优与高/低刷新阈值设定。
- 关键点：概念池去重、事件排序、分段摘要阈值
- 结论：先上线 chunk 模式，再观察 token 消耗。
```

---

## 10. 路线图 & 贡献
- [ ] 提供官方 `mid_refresh` 增量模式
- [ ] 支持 PostgreSQL/SQLite 配置模板
- [ ] 发布 NoneBot 插件商店版本
- [ ] 引入可视化控制台（FastAPI + Tailwind）

欢迎 Issue / PR，一起把群聊摘要体验做到极致。如果项目对你有帮助，别忘了点亮 ⭐。

---

## 11. 许可证
本项目以 **MIT License** 发布，详情见 `LICENSE`。