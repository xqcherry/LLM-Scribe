# LLM-Scribe

一个面向 QQ 群聊场景的 **LLM 智能摘要插件**（基于 NoneBot2 + OneBot v11）。

它会从数据库读取指定时间窗口内的群聊消息，完成清洗、结构化总结与主题提炼，并最终渲染成一张可直接发送到群里的摘要长图。

---

## 项目亮点

- **端到端摘要流水线**  
  从消息加载 → 过滤清洗 → Token 估算 → 模型选择 → 结构化摘要 → 图片渲染，流程完整。

- **基于 LangGraph 的可编排工作流**  
  摘要流程拆解为独立节点，结构清晰、可扩展，便于后续接入更多策略节点。

- **自动模型选择与成本估算**  
  根据 Token 数自动选择不同上下文窗口的模型（8k / 32k / 128k），并计算估算成本。

- **结构化输出而非纯文本摘要**  
  输出包含：总览摘要、话题列表、参与者、统计信息等，利于后续展示和二次加工。

- **高质量图文报告渲染**  
  使用 Jinja2 + Playwright 将 HTML 模板渲染为高清长图，适合直接在群聊展示。

- **清晰分层架构（领域/应用/基础设施/接口）**  
  采用 Ports & Adapters 风格，业务逻辑和外部依赖隔离良好，便于维护与替换实现。

---

## 项目结构

```text
src/
├─ application/            # 应用层（用例与端口）
├─ domain/                 # 领域层（实体与领域服务）
├─ infrastructure/         # 基础设施层（LLM、DB、渲染、模板等实现）
└─ interfaces/             # 接口层（NoneBot 命令）
```

---

## 核心能力

- 命令入口：`/sum`、`/summary`
- 时间窗口：默认近 6 小时，可指定 1~72 小时
- 支持参数：
  - `/sum`：默认 6 小时
  - `/sum 12`：最近 12 小时
  - `/sum day` 或 `/sum d`：最近 24 小时
  - `/sum ls`：查看帮助

---

## 运行要求

- Python 3.10+
- MySQL（需存在消息表 `messages_event_logs`）
- NoneBot2 运行环境（本项目作为插件接入）
- 可用的 LLM API Key（当前实现默认 Moonshot 兼容）

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器内核

```bash
python -m playwright install chromium
```

### 3. 配置环境变量

复制并填写配置：

```bash
cp .env.example .env
```

主要字段：

- `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`
- `LLM_API_KEY`
- `IGNORE_QQ`（可选，逗号分隔）

### 4. 在 NoneBot2 项目中加载插件

将本项目作为插件模块接入你的 NoneBot2 主程序（具体加载方式取决于你的 Bot 主项目组织方式）。

---

## 数据来源说明

当前仓储默认从 MySQL 表 `messages_event_logs` 读取群消息，主要字段：

- `message_type`（需为 `group`）
- `group_id`
- `user_id`
- `sender_nickname`
- `raw_message`
- `time`

请确保你的消息入库链路与上述字段兼容。

---

## 架构简述

1. `interfaces/bot/summary_command.py` 接收命令并解析参数
2. `application/services/summary_report_app_service.py` 串联“摘要 + 渲染”
3. `infrastructure/summary/graph/summary_graph.py` 执行 LangGraph 工作流
4. `infrastructure/persistence/adapters/mysql_message_repository.py` 读取消息
5. `infrastructure/summary/chains/summary_chain.py` 调用 LLM 输出结构化摘要
6. `infrastructure/reporting/` 将结果渲染为 HTML 并截图为图片

---

## 许可证

本项目采用 `LICENSE` 文件中声明的开源许可证。