# LLM-Scribe —— LangChain 驱动的群聊智能摘要系统

> 一款基于 **LangChain 智能语义管线** 的群聊摘要与记忆系统  
> 可独立运行，也可作为 **NoneBot 插件** 接入 NapCat 等消息框架，  
> 实现 “消息 → 语义结构 → 摘要生成 → 记忆沉淀” 的自动化闭环

---

## 🚀 项目简介

**LLM-Scribe** 以 **LangChain** 为核心语义调度框架，  
构建了一个高可扩展、可多模型切换的 **群聊语义摘要系统**。  

系统从 MySQL 读取群聊消息，通过 LangChain 管线完成语义抽取、筛选与融合，  
再结合多层记忆机制与自适应刷新策略，生成结构化、可追溯的高质量摘要。

> **NoneBot + NapCat** 仅承担消息输入输出与命令触发的接口作用，  
> **LangChain、语义记忆与多模型封装** 才是本项目的核心。

---

## 🧩 技术架构亮点

### 🌐 LangChain 多模型语义中枢
- 统一封装各大模型（Moonshot / OpenAI / DeepSeek / Qwen / GLM / Claude / Gemini / Ollama）。  
- 通过环境变量 `LLM_PROVIDER` 动态切换模型，无需修改代码。  
- 所有输出均遵循 LangChain ChatModel 接口规范，可无缝集成至其他 LangChain 流程中。  

---

### 🧠 分层记忆系统（Layered Memory）

通过 **分层记忆结构** 保持摘要的上下文一致性与生成效率：

- **短期记忆（memory_short）**  
  存储最近语义块与摘要内容，维持“当前语境”的连续性；  
  每次摘要更新检查时间戳与语义池，用于增量生成。  
- **长期记忆（memory_long）**  
  存储版本化摘要，用于历史回溯与语义演化分析；  
  让系统不仅“记得当前”，还能“理解过去”。  
- **缓存层（chat_cache）**  
  缓存近 24 小时消息快照，避免重复查询数据库；  
  通过消息去重与窗口滑动显著降低 I/O 与 token 成本。  

---

### ⚙️ 自适应刷新策略（Adaptive Refresh）

为平衡模型调用成本与摘要时效，系统采用三级刷新机制：

| 模式   | 触发条件                           | 行为                           |
| ------ | ---------------------------------- | ------------------------------ |
| `high` | 新消息量大 / 超过 24h / 每日 23:00 | 全量摘要，重构记忆与长期归档   |
| `mid`  | 小批增量 / 语义差异明显            | 增量摘要，附加到上次结果       |
| `low`  | 新消息少 / 内容相似                | 直接复用上次摘要，仅更新时间戳 |

这种自适应策略让模型调用既智能又经济：  
**高频对话不浪费 token，低频群聊也能保持语义新鲜度。**

---

### 🧬 语义抽取与筛选机制（Semantic Extraction & Selection）

基于 LangChain Prompt 管线，系统将原始群聊消息转化为结构化语义块：

1. **语义抽取**：  
   使用 LLM 将消息解析为 concepts、events、quotes、topics 等 JSON 结构。  
2. **语义合并**：  
   与短期记忆中的语义池对齐，自动去重、排序与权重更新。  
3. **语义筛选**：  
   从语义池中挑选与当前窗口最相关的内容，以最小上下文生成最优摘要。  

这种结构化语义处理使摘要更具 **主题聚合性与语义连贯性**。  

---

### 🧰 模块化设计（Modular Architecture）

**LLM-Scribe** 采用完全模块化的架构，每个组件都可独立替换或扩展：

- **数据库层（DB）**：负责消息加载（支持 MySQL、REST API 等）。  
- **语义层（Semantic）**：负责语义抽取与合并逻辑，可替换不同 Prompt 模板或算法。  
- **模型层（LLM）**：基于 LangChain 的统一封装，支持任意兼容模型。  
- **刷新层（Refresh）**：负责 high / mid / low 自适应刷新逻辑。  
- **接口层（Interface）**：提供 NoneBot + NapCat 交互，也可独立运行或嵌入其他系统。  

---

## ⚙️ 安装与运行（Installation & Usage）

### 🧩 环境要求

| 组件      | 推荐版本                | 说明                      |
| --------- | ----------------------- | ------------------------- |
| Python    | ≥ 3.10                  | 建议使用 3.10 ~ 3.12      |
| MySQL     | ≥ 5.7 / 8.0             | 存储消息与记忆数据        |
| NoneBot 2 | ≥ 2.2.0                 | （可选）命令接口层        |
| NapCat    | ≥ 2.0                   | （可选）消息网关，QQ 接入 |
| 操作系统  | Windows / Linux / macOS | 全平台支持                |

---

###  1️⃣ 克隆项目

```bash
git clone https://github.com/xqcherry/LLM-Scribe.git
cd LLM-Scribe
```

###  2️⃣ 创建虚拟环境并安装依赖

```
python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
pip install -U pip
pip install -e .
```

> `-e .` 表示以开发模式安装当前包（即 llm_scribe）

或使用简版依赖安装：

```
pip install -r requirements.txt
```

------

### 3️⃣ 配置环境变量（.env）

LLM-Scribe 使用 `.env` 文件统一管理模型 API 密钥与数据库配置

1. 在项目根目录复制示例文件：

```bash
cp .env.example .env
```

2. 打开 `.env` 并填写核心字段（以下为最简可用示例，使用 Moonshot 模型）：

```
LLM_PROVIDER=moonshot

# Moonshot
MOONSHOT_API_KEY=你的APIKey
MOONSHOT_MODEL=moonshot-v1-32k
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1

# MySQL 数据库
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=diting_qq_bot
```

3. 如需使用其他模型（OpenAI / DeepSeek / Qwen / GLM / Claude / Gemini / Ollama 等），
	 请参考完整模板文件 `.env.example`，取消对应段落注释并填写各自 API Key 和 Base URL。

>  提示：
>
> - 未填写的 API Key 会被自动忽略，不影响启动
> - 你可以随时修改 `LLM_PROVIDER=openai` 等来切换默认模型

------

### 4️⃣ 初始化数据库

执行以下 SQL（或使用 sql/schema.sql）：

```mysql
CREATE TABLE IF NOT EXISTS `messages_event_logs` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `message_type` VARCHAR(20) NOT NULL,         -- 'group' / 'private'
  `group_id` BIGINT NOT NULL,                  -- 群聊ID
  `user_id` BIGINT NOT NULL,                   -- 发送者ID
  `sender_nickname` VARCHAR(100) DEFAULT NULL, -- 昵称
  `raw_message` TEXT NOT NULL,                 -- 原始消息文本
  `time` INT NOT NULL,                         -- 消息时间戳（Unix秒）
  KEY `idx_group_time` (`group_id`, `time`),   -- 查询优化
  KEY `idx_type_time` (`message_type`, `time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

```mysql
CREATE TABLE `chat_cache` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` bigint NOT NULL,
  `msg_json` longtext NOT NULL,
  `start_ts` timestamp NOT NULL,
  `end_ts` timestamp NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_group` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

```mysql
CREATE TABLE `memory_short` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` bigint NOT NULL,
  `mem_json` longtext NOT NULL,
  `last_check_ts` timestamp NOT NULL,
  `last_full_refresh_ts` timestamp NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_group` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

```mysql
CREATE TABLE `memory_long` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` bigint NOT NULL,
  `ver` int NOT NULL,
  `summary_text` longtext NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_group_version` (`group_id`,`ver`),
  KEY `idx_group` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

------

### 5️⃣ 独立运行模式

配置好`.env`后直接运行`__main__.py`

------

### 6️⃣ 作为 NoneBot 插件集成

> LLM-Scribe 可以作为 **NoneBot 插件** 使用，用于在群聊中直接触发摘要指令。  
> 当前版本尚未上架 NoneBot 官方插件商店，仅支持 **本地导入安装**。

在你的 NoneBot 项目中：

1. 在 NoneBot 根目录的`.env`文件配置好字段

```
LLM_PROVIDER=moonshot

# Moonshot
MOONSHOT_API_KEY=你的APIKey
MOONSHOT_MODEL=moonshot-v1-32k
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1

# MySQL 数据库
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=diting_qq_bot
```

2. 将整个 `llm_scribe/` 文件夹（或仓库根目录）放入你的 NoneBot 项目的plugins下

```
your_nonebot_project/
├── .env
├── pyproject.toml
└── plugins/
    └── llm_scribe/ 
```

3. 在 `pyproject.toml` 中添加路径：

```
[tool.nonebot]
plugin_dirs = ["plugins"]
```

4. 确保依赖安装完整

```
pip install -U nonebot2[fastapi] nonebot-adapter-onebot
pip install langchain langchain-community openai pymysql jieba python-dotenv
```

运行：

```
nb run
```

群聊命令：

```
/sum
/summary 6
```

> 详细操作请看官方文档: [nonebot官方文档](https://nonebot.dev/docs/)

------

### 7️⃣ Docker 部署（可选）

```
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install -U pip && pip install -e .
CMD ["python", "-m", "llm_scribe.main.manger"]
docker build -t llm-scribe .
docker run --env-file .env llm-scribe
```

------

## 📊 示例输出

```
基础信息：
- 时段：2025-11-10 10:00 ~ 12:00
- 参与：8人，302条消息

整体摘要：
群成员讨论了新功能部署、模型接口封装和摘要准确性问题。
核心话题聚焦在 LangChain 管线、MySQL 数据读取与多模型切换。

话题总结：
技术开发（45%）—— 模型封装、缓存逻辑优化
摘要准确性（30%）—— Prompt 模板调优与语义筛选改进
团队沟通（25%）—— 任务分工与版本同步
```

------

## 🧑‍💻 开发者指南（Developer Guide）

### 🧬 调整 Prompt 模板

编辑 `llm_scribe/Prompt/base.py` 可修改生成格式与内容结构。

### 🧠 更换数据库源

替换 `llm_scribe/DB/connection.py` 中的连接配置即可支持 PostgreSQL、SQLite 或 REST 接口。

### 🧩 官方文档与相关资源

#### NoneBot 官方资源

[nonebot官方文档](https://nonebot.dev)

[命令行工具（nb CLI）](https://cli.nonebot.dev/docs/)

[GitHub 仓库](https://github.com/nonebot/nonebot2)

#### NapCat（OneBot v11）官方资源

[官方文档（NapCat QQ 协议适配器）](https://github.com/NapNeko/NapCatQQ)

[OneBot v11 协议规范](https://github.com/botuniverse/onebot-11)

[ NoneBot OneBot 适配器](https://github.com/nonebot/adapter-onebot)

#### LLM 与框架生态资源

[LangChain](https://docs.langchain.com/oss/python/langchain/overview)

[Moonshot AI](https://www.moonshot.cn/)

[OpenAI API](https://platform.openai.com/docs/api-reference/introduction)

------

## 📜 License

本项目采用 **MIT License**

------

## 🌟 支持与贡献

欢迎提交 Issue 或 PR！
如果本项目对你有帮助，请给一个 ⭐ Star，
帮助更多人发现 **LLM-Scribe** 🧠✨