# LLM-Scribe 测试说明

## 测试文件

1. **test_all_modules.py** - 全面模块测试（包含所有测试）
   - 数据库连接测试（Redis, ChromaDB, MySQL）
   - 所有核心功能模块测试
   - 一次性运行所有测试

2. **test_single.py** - 单独测试运行器（推荐用于开发调试）
   - 支持单独测试任意模块
   - 支持测试多个指定模块
   - 支持列出所有可用模块
   - 支持运行所有测试

## 测试覆盖的模块

### 1. 消息处理模块
- ✅ **cq_filter.py** - CQ 码过滤
  - 测试各种 CQ 码的过滤（表情、@、图片、转发等）
  - 测试 HTML 转义字符处理
  - 测试消息过滤（忽略指定用户）

### 2. 工具模块
- ✅ **time_utils.py** - 时间工具
  - UNIX 时间戳 ↔ 上海时区转换
  - 获取当前上海时区时间

### 3. LLM 相关模块
- ✅ **token_counter.py** - Token 计数器
  - 基本文本 Token 计数
  - 消息列表 Token 计数
  - 完整提示词 Token 估算

- ✅ **model_factory.py** - Moonshot 模型工厂
  - 模型工厂初始化
  - 根据 Token 数量自动选择模型
  - 成本估算

- ✅ **summary_chain.py** - 摘要生成链
  - 摘要链初始化
  - 实际调用 LLM 生成摘要（需要 API Key）

### 4. 缓存模块
- ✅ **redis_cache.py** - Redis 数据缓存
  - 设置缓存
  - 获取缓存
  - 检查键是否存在
  - 删除缓存

- ✅ **semantic_cache.py** - 语义缓存
  - 语义缓存初始化
  - 存入语义缓存
  - 检索语义缓存（相同消息）
  - 相似消息检索（语义相似度）

- ✅ **cache_key.py** - 缓存键生成
  - 消息哈希生成
  - 语义查询字符串生成
  - 完整缓存键生成

### 5. 记忆模块
- ✅ **memory/manager.py** - 记忆管理器
  - 记忆管理器初始化
  - 添加记忆
  - 获取记忆上下文
  - 获取概念列表
  - 获取事件列表

- ✅ **memory/detail/episodic_memory.py** - 事件记忆
  - 添加事件记忆
  - 获取事件记忆

- ✅ **memory/detail/semantic_memory.py** - 语义记忆
  - 添加语义概念
  - 获取语义概念
  - 添加语义事件
  - 获取语义事件

- ✅ **memory/vector/vector_store.py** - 向量存储
  - 向量存储初始化
  - 添加摘要到向量存储
  - 相似度搜索

### 6. 检索模块
- ✅ **retrieval/rag/retriever.py** - RAG 检索器
  - RAG 检索器初始化
  - 检索相关上下文

- ✅ **retrieval/hybrid_search.py** - 混合检索
  - 混合检索（向量检索 + 重排序）

### 7. 数据访问模块
- ✅ **storage/database/repositories.py** - 消息仓库
  - 获取群组消息
  - 获取指定时间后的消息

### 8. 数据处理模块
- ✅ **pipeline/meta_extractor.py** - 元信息提取
  - 提取基础元信息
  - 格式化元信息为字符串
  - 处理空消息列表

### 9. 提示词模块
- ✅ **prompts/templates/summary_prompt.py** - 摘要提示词模板
  - 提示词模板初始化
  - 提示词生成

### 10. 配置模块
- ✅ **config.py** - 配置加载
  - 配置对象加载
  - 关键配置项检查

### 11. 数据库连接模块
- ✅ **数据库连接测试** - 连接验证
  - Redis 连接测试
  - ChromaDB 连接测试
  - MySQL 连接测试

## 运行测试

### 前置条件

1. 确保已安装所有依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量（`.env` 文件）：
   - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
   - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`（可选）
   - `CHROMA_HOST`, `CHROMA_PORT`
   - `MOONSHOT_API_KEY`（用于 LLM 相关测试）

3. 确保服务运行：
   - MySQL 数据库
   - Redis（可选，用于缓存测试）
   - ChromaDB（用于向量存储测试）

### 运行所有测试

```bash
# 方式1: 使用 test_all_modules.py（一次性运行所有测试）
python test/test_all_modules.py

# 方式2: 使用 test_single.py（推荐，更灵活）
python test/test_single.py --all
```

**注意**：测试会首先执行数据库连接测试，然后依次测试所有功能模块。

### 单独测试指定模块（推荐）

使用 `test_single.py` 可以单独测试任意模块，非常适合开发调试：

```bash
# 列出所有可用模块
python test/test_single.py --list
# 或
python test/test_single.py -l

# 测试单个模块
python test/test_single.py 消息过滤
python test/test_single.py 数据库连接
python test/test_single.py Token计数器

# 测试多个模块
python test/test_single.py 消息过滤 时间工具 Token计数器

# 使用别名（支持中英文）
python test/test_single.py db redis vector
python test/test_single.py 数据库连接 Redis缓存 向量存储

# 运行所有测试
python test/test_single.py --all
```

**支持的别名**：
- `db` / `database` → 数据库连接
- `cq` / `filter` → 消息过滤
- `time` → 时间工具
- `token` → Token计数器
- `model` / `factory` → 模型工厂
- `redis` → Redis缓存
- `semantic` → 语义缓存
- `vector` → 向量存储
- `memory` → 记忆管理器
- `retrieval` → 检索模块
- `repo` / `repository` → 消息仓库
- `meta` → 元信息提取
- `config` → 配置加载
- `cache_key` → 缓存键生成
- `episodic` → 事件和语义记忆
- `prompt` → 提示词模板
- `summary` → 摘要链
- `extraction` → 提取链
- `compression` → 压缩链
- `reranker` → 重排序器
- `compressor` → 记忆压缩器

## 测试结果说明

测试会输出每个模块的测试结果：
- ✅ 通过 - 测试成功
- ❌ 失败 - 测试失败（会显示错误信息）

最后会显示测试总结，包括：
- 总模块数
- 通过数
- 失败数
- 通过率

## 注意事项

1. **数据库连接测试**：需要数据库服务运行且配置正确
2. **Redis 测试**：如果 Redis 未运行，相关测试会失败
3. **ChromaDB 测试**：如果 ChromaDB 未运行，相关测试会失败
4. **LLM 测试**：需要有效的 Moonshot API Key，否则会跳过相关测试
5. **实际数据测试**：某些测试（如消息仓库）需要数据库中有实际数据

## 测试覆盖统计

- **总模块数**：21 个核心模块（包含数据库连接）
- **测试用例**：65+ 个测试点
- **覆盖范围**：所有核心功能模块，包括数据库连接

## 新增测试模块

### 12. 链式处理模块
- ✅ **compression_chain.py** - 记忆压缩链
  - 压缩链初始化
  - 摘要压缩（实际调用 LLM）

- ✅ **extraction_chain.py** - 实体提取链
  - 提取链初始化
  - 实体提取（实际调用 LLM）

### 13. 重排序模块
- ✅ **reranker.py** - 重排序器
  - 重排序器初始化
  - 文档重排序
  - 关键词提取
  - 相关性分数计算

### 14. 记忆压缩模块
- ✅ **memory_compressor.py** - 记忆压缩器
  - 压缩判断逻辑
  - 记忆压缩器初始化
  - 摘要压缩（实际调用 LLM）

## 扩展测试

如果需要添加新的测试：
1. 在 `test_all_modules.py` 中添加新的测试函数
2. 在 `test_all_modules.py` 的 `run_all_tests()` 中调用新测试函数
3. 在 `test_single.py` 的 `TEST_MODULES` 字典中添加新模块映射
4. 确保测试函数返回 `True`（通过）或 `False`（失败）

**注意**：如果新测试是异步函数，需要在 `TEST_MODULES` 中设置 `"async": True`
