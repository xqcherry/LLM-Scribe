# LLM-Scribe 开发计划

> 最近更新：2026-08-07
>
> 本文件记录项目的中长期改进方向，按问题域组织。每项含优先级与状态字段，启动/完成时更新对应状态。实现细节在落地时再细化，本计划只锁定「要解决什么、目标是什么、大致怎么改」。

## 背景

项目当前主要痛点集中在两块：

1. **摘要效果差**：多阶段/增量摘要功能已被移除（仅剩 `.pyc` 残留与未调用的 `compression_prompt`/`extraction_prompt`），退化成单次全量 LLM 调用。长时段（24h/72h）消息全量塞入一次调用，上下文越长越丢细节，`max_tokens=2000` 又卡住输出。
2. **缺乏缓存**：LLM 摘要结果、分块中间结果均无缓存，重复请求重复花钱；DB 每次新建连接无连接池；头像缓存无失效机制。

附带问题：报告视觉陈旧且暴露技术指标；胶囊头像在 QQ 换头像后不更新；缺少用户画像维度。

## 改进方向总览

| # | 方向 | 优先级 | 状态 | 一句话目标 |
|---|------|--------|------|-----------|
| 1 | 报告视觉重做 | 高 | 未开始 | 重排信息架构，群友视角，多主题可切换 |
| 2 | 摘要分块 + 滑动窗口 + 多级缓存 | 最高 | 未开始 | 激活多阶段摘要，建立缓存与增量机制，治本效果与成本 |
| 3 | 胶囊头像缓存失效 | 中 | 未开始 | 头像缓存可过期刷新，QQ 换头像后能更新 |
| 4 | 用户画像 | 低 | 未开始 | 预留端口与实体，后续接入采集与展示 |

状态取值：`未开始` / `进行中` / `部分完成` / `已完成` / `已搁置`

---

## 方向一：报告视觉重做

### 现状与问题

- `reporting/templates/default/default.html` 为单文件 glassmorphism + 紫蓝渐变，视觉单调。
- 统计区四宫格暴露 `tokens` / `预估成本`，技术指标不应呈现给群友。
- 话题卡信息层级单一（标题 + 参与者 + 正文），无参与度可视化；`footer` 空置。
- 胶囊 HTML 硬编码在 `generators.py` 拼字符串里，与模板 CSS 耦合。
- `templates.py:24` 模板缺失时回退到不存在的 `scrapbook` 目录，为死引用。

### 目标

群友视角的信息架构，系统化的设计 token，多主题可切换，胶囊样式回归模板。

### 方案

- 信息架构重排：四宫格改为消息数 / 活跃成员 / 最活跃时段 / 话题数；tokens 与成本降级为可选 debug 字段。
- 抽 CSS 变量（配色 / 字号 / 间距 / 圆角）；保持单文件 HTML（Playwright 渲染最优解）。
- 预留多主题目录 `templates/default|dark|scrapbook`，修复 `templates.py` 回退逻辑。
- 话题卡增强：参与度可视化（头像 + 发言占比条）、编号节奏、空状态处理。
- 胶囊解耦：结构由模板定义，`generators.py` 只产数据/占位。

### 涉及模块

`reporting/templates/default/default.html`、`reporting/data_adapter.py`、`reporting/generators.py`、`reporting/templates.py`

### 工作项

- [ ] 1.1 定义设计 token 与基础样式系统
- [ ] 1.2 重排统计区信息架构，隐藏技术指标到 debug 模式
- [ ] 1.3 重做话题卡（参与度可视化、编号节奏、空状态）
- [ ] 1.4 胶囊 HTML 结构迁移至模板，`generators.py` 只产数据
- [ ] 1.5 多主题目录与 `templates.py` 回退逻辑修复
- [ ] 1.6 浏览器实测渲染效果，对比改前改后

### 优先级 / 状态

高 / 未开始

---

## 方向二：摘要分块 + 滑动窗口 + 多级缓存

### 现状与问题

- 单次全量 LLM：`summary/graph/summary_graph.py` 5 节点，`generate_summary` 把全部 `filtered_messages` 一次塞给 LLM，长窗上下文越长越丢细节，`max_tokens=2000` 卡输出。
- 零缓存：无最终结果缓存、无分块缓存；`persistence/db_connection.py` 每次新建连接无连接池。
- 滑动窗口机制名存实亡：`get_group_messages_after`（端口 + 实现）无人调用；`memory_context` 在 `summary_graph.py:98` 调用 chain 时始终传空；`compression_prompt` / `extraction_prompt` 为死代码。
- `format_messages.py` 返回 `(text, id2name)` 元组，但 `summary_chain.py:31` 只取了文本，丢了映射。

### 目标

长消息走分块提取 + 合并；短消息走原单次链路。建立多级缓存与按群锚点的滑动窗口，重复请求不重复调用 LLM，增量请求只处理新消息。

### 方案

**多阶段摘要**：graph 增节点 `split_chunks`（按 token 预算分块）→ `extract`（逐块用 `extraction_prompt`）→ `compress_merge`（用 `compression_prompt` 合并）→ `generate_summary`。复用已有死代码 prompt；按消息量路由，短消息走原链路。

**滑动窗口**：为每个群维护「上次摘要锚点时间」，新请求优先 `get_group_messages_after` 取增量消息，与上次压缩摘要（喂给 `memory_context`）做增量合并；锚点过期或窗口不连续则回退全量。

**多级缓存**（新建 `infrastructure/cache/`）：

| 层级 | 键 | 值 | 失效策略 |
|------|----|----|---------|
| L1 最终结果 | `(group_id, hours, 消息指纹)` | `SummaryResult` + image bytes | 短 TTL 或「窗口内无新消息即命中」 |
| L2 分块摘要 | 消息块内容 hash | extraction 结果 | 内容不变即命中 |
| L3 锚点状态 | `group_id` | 上次摘要时间 + 压缩摘要 | 滑动窗口依据 |

**DB 连接池**：`get_connection` 改 `aiomysql` 连接池；当前 repository 是同步阻塞而链路全异步，顺带修这个不一致。

**输出上限**：`max_tokens` 按模型动态调整，不硬编码 2000。

### 涉及模块

`summary/graph/`（新增节点 + state 扩展）、`summary/chains/summary_chain.py`、`prompts/templates/compression_prompt.py`、`prompts/templates/extraction_prompt.py`、新增 `infrastructure/cache/`、`persistence/db_connection.py`、`persistence/adapters/mysql_message_repository.py`、新增 anchor store、`message_processing/formatters/format_messages.py`（修返回值丢失）

### 工作项

- [ ] 2.1 新建 `infrastructure/cache/`，定义缓存端口与内存/可持久化实现
- [ ] 2.2 graph 增加分块 + extract + compress_merge 节点，按消息量路由
- [ ] 2.3 激活 `compression_prompt` / `extraction_prompt`，接入多阶段链路
- [ ] 2.4 实现 L1 最终结果缓存（消息指纹判定窗口是否变化）
- [ ] 2.5 实现 L2 分块摘要缓存（块内容 hash）
- [ ] 2.6 实现 L3 锚点状态存储 + 滑动窗口增量合并逻辑
- [ ] 2.7 激活 `memory_context` 机制，喂入上次压缩摘要
- [ ] 2.8 `db_connection` 改 `aiomysql` 连接池，repository 改异步
- [ ] 2.9 `max_tokens` 按模型动态化
- [ ] 2.10 修 `format_messages` 返回值在 `summary_chain` 被丢弃的问题
- [ ] 2.11 端到端验证：长窗效果提升、重复请求命中缓存、增量请求只处理新消息

### 优先级 / 状态

最高 / 未开始

---

## 方向三：胶囊头像缓存失效

### 现状与问题

- `generators.py:266` `_get_user_avatar_base64`：命中缓存文件直接返回，无 TTL、无校验；QQ 换头像后永远是旧图。
- 下载失败时无保留旧缓存逻辑。

### 目标

头像缓存可过期刷新，QQ 换头像后能更新；失败时不丢旧图。

### 方案

- TTL 失效：缓存文件按 mtime 判定，超过阈值（如 7 天）触发重下载。
- 轻量校验（可选）：QQ 头像接口无可靠 etag，用 HEAD 对比 `Content-Length` 或定期刷新；TTL 内直接用，超 TTL 但 size 未变则续期、变了才覆盖。
- 失败保留旧缓存：下载失败不覆盖、不写空，返回旧图。
- 缓存键加 `spec` 参数，避免不同尺寸混用同一文件。

### 涉及模块

`reporting/generators.py`（`_get_user_avatar_base64`）

### 工作项

- [ ] 3.1 缓存文件加 mtime TTL 判定
- [ ] 3.2 下载失败保留旧缓存
- [ ] 3.3 缓存键加 `spec` 维度
- [ ] 3.4（可选）HEAD 轻量校验刷新策略

### 优先级 / 状态

中 / 未开始

---

## 方向四：用户画像

### 现状与问题

无任何画像能力。摘要中只有 `participants` 列表，缺乏跨周期的用户维度。

### 目标

建立用户画像数据模型与采集通道，为摘要与报告提供用户维度增强（「XX 擅长 XXX」、参与度排行、活跃用户展示）。

### 方案（方向性，先留接口）

- 数据模型：`UserProfile(user_id, 昵称历史, 活跃时段分布, 话题参与记录, 兴趣标签, 发言风格)`。
- 采集：从摘要流程的 `participants` + 消息元数据被动积累；后续在 graph 加 `update_profile` 节点。
- 存储：MySQL 新表 `user_profiles`。
- 用途：摘要补充用户标签、参与度排行、渲染卡展示活跃用户。
- 现阶段：先定义 `UserProfilePort` + 实体，不实现采集，待方向二/三稳定后接入。

### 涉及模块

新 domain entity、新 port、新 adapter、graph 增节点（后续）、新 DB 表

### 工作项

- [ ] 4.1 定义 `UserProfile` 实体与 `UserProfilePort` 端口
- [ ] 4.2 设计 `user_profiles` 表结构（暂不建表）
- [ ] 4.3（后续）graph 增 `update_profile` 采集节点
- [ ] 4.4（后续）摘要 prompt 接入用户标签
- [ ] 4.5（后续）报告模板展示活跃用户

### 优先级 / 状态

低 / 未开始

---

## 推进顺序

建议 **2 → 3 → 1 → 4**：

- **2** 治本，同时解效果与成本，其缓存基础设施可服务 3/4；
- **3** 改动小，可顺带在 2 之后做；
- **1** 视觉独立，但最好等 2 的数据字段稳定后再重排；
- **4** 依赖前面稳定，最后接入。

若优先追求直观感受，1 可提前（视觉重做不依赖 2 的内部重构，只需约定数据字段）。
