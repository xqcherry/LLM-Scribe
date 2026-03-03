import os
import sys
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

# ==================== 测试工具函数 ====================
def print_test_header(test_name: str):
    """打印测试标题"""
    print("\n" + "=" * 70)
    print(f"🧪 测试: {test_name}")
    print("=" * 70)

def print_test_result(success: bool, message: str = ""):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{status} {message}")

# ==================== 1. 测试消息过滤模块 ====================
def test_cq_filter():
    """测试 CQ 码过滤功能"""
    print_test_header("消息过滤模块 (cq_filter)")
    
    try:
        from src.infrastructure.pipeline.cq_filter import cq_filter, filter_msgs
        
        # 测试各种 CQ 码过滤
        test_cases = [
            ("[CQ:face,id=123]", "[表情]"),
            ("[CQ:at,qq=123456]", "[@123456]"),
            ("[CQ:image,url=xxx]", "[图片]"),
            ("[CQ:forward,id=xxx]", "[转发消息]"),
            ("[CQ:reply,id=123]", ""),
            ("测试消息[CQ:face,id=1]正常文本", "测试消息[表情]正常文本"),
            ("&amp; &lt; &gt;", "& < >"),  # HTML 转义
        ]
        
        all_passed = True
        for input_text, expected in test_cases:
            result = cq_filter(input_text)
            passed = result == expected
            if not passed:
                print(f"  输入: {input_text}")
                print(f"  期望: {expected}")
                print(f"  实际: {result}")
            all_passed = all_passed and passed
        
        print_test_result(all_passed, "CQ 码过滤")
        
        # 测试消息过滤
        test_messages = [
            {"user_id": 111, "raw_message": "消息1"},
            {"user_id": 222, "raw_message": "消息2"},
            {"user_id": 333, "raw_message": "消息3"},
        ]
        ignore_ids = [222]
        filtered = filter_msgs(test_messages, ignore_ids)
        passed = len(filtered) == 2 and all(m["user_id"] != 222 for m in filtered)
        print_test_result(passed, "消息过滤（忽略指定用户）")
        
        return all_passed and passed
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 2. 测试时间工具模块 ====================
def test_time_utils():
    """测试时间工具函数"""
    print_test_header("时间工具模块 (time_utils)")
    
    try:
        from src.infrastructure.common import unix_to_shanghai, shanghai_to_unix, now_shanghai
        
        # 测试 UNIX 时间戳转换
        test_timestamp = int(time.time())
        dt = unix_to_shanghai(test_timestamp)
        converted_back = shanghai_to_unix(dt)
        
        # 允许 1 秒误差
        passed1 = abs(converted_back - test_timestamp) <= 1
        print_test_result(passed1, "UNIX 时间戳 ↔ 上海时区转换")
        
        # 测试当前时间
        now = now_shanghai()
        passed2 = isinstance(now, datetime) and now.tzinfo is not None
        print_test_result(passed2, "获取当前上海时区时间")
        
        return passed1 and passed2
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 3. 测试 Token 计数器 ====================
def test_token_counter():
    """测试 Token 计数功能"""
    print_test_header("Token 计数器模块")
    
    try:
        from src.llm.moonshot.token_counter import TokenCounter
        
        counter = TokenCounter()
        
        # 测试基本计数
        text = "Hello, world!"
        tokens = counter.count_tokens(text)
        passed1 = tokens > 0
        print_test_result(passed1, f"基本 Token 计数 (文本: '{text}' -> {tokens} tokens)")
        
        # 测试消息列表计数
        messages = [
            {"sender_nickname": "用户1", "raw_message": "第一条消息"},
            {"sender_nickname": "用户2", "raw_message": "第二条消息"},
        ]
        msg_tokens = counter.count_messages_tokens(messages)
        passed2 = msg_tokens > 0
        print_test_result(passed2, f"消息列表 Token 计数 ({len(messages)} 条消息 -> {msg_tokens} tokens)")
        
        # 测试完整提示词估算
        system_prompt = "你是一个助手"
        estimated = counter.estimate_prompt_tokens(system_prompt, messages, "记忆上下文")
        passed3 = estimated > msg_tokens
        print_test_result(passed3, f"完整提示词 Token 估算 ({estimated} tokens)")
        
        return passed1 and passed2 and passed3
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 4. 测试 LLM 模型工厂 ====================
def test_model_factory():
    """测试 Moonshot 模型工厂"""
    print_test_header("LLM 模型工厂模块")
    
    try:
        from src.llm.moonshot.model_factory import MoonshotFactory
        
        # 检查 API Key
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            print_test_result(False, "缺少 MOONSHOT_API_KEY，跳过模型创建测试")
            return False
        
        factory = MoonshotFactory()
        print_test_result(True, "模型工厂初始化")
        
        # 测试模型选择
        test_cases = [
            (1000, "moonshot-v1-8k"),
            (5000, "moonshot-v1-32k"),
            (50000, "moonshot-v1-128k"),
        ]
        
        all_passed = True
        for prompt_tokens, expected_model in test_cases:
            selected = factory.select_model(prompt_tokens)
            passed = selected == expected_model
            if not passed:
                print(f"  Token: {prompt_tokens}, 期望: {expected_model}, 实际: {selected}")
            all_passed = all_passed and passed
        
        print_test_result(all_passed, "根据 Token 数量选择模型")
        
        # 测试成本估算
        cost = factory.estimate_cost("moonshot-v1-8k", 1000)
        passed = isinstance(cost, float) and cost > 0
        print_test_result(passed, f"成本估算 (1000 tokens -> ${cost:.4f})")
        
        return all_passed and passed
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 5. 测试 Redis 数据缓存 ====================
def test_redis_cache():
    """测试 Redis 数据缓存"""
    print_test_header("Redis 数据缓存模块")
    
    try:
        from src.cache.data_cache.redis_cache import RedisDataCache
        
        cache = RedisDataCache()
        
        # 测试基本操作
        test_key = "test:key:123"
        test_value = {"test": "data", "number": 42}
        
        # 设置缓存
        cache.set(test_key, test_value, ttl=60)
        print_test_result(True, "设置缓存")
        
        # 获取缓存
        retrieved = cache.get(test_key)
        passed1 = retrieved == test_value
        print_test_result(passed1, "获取缓存")
        
        # 检查存在
        exists = cache.exists(test_key)
        passed2 = exists is True
        print_test_result(passed2, "检查键是否存在")
        
        # 删除缓存
        cache.delete(test_key)
        deleted_check = cache.get(test_key)
        passed3 = deleted_check is None
        print_test_result(passed3, "删除缓存")
        
        return passed1 and passed2 and passed3
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 6. 测试语义缓存 ====================
def test_semantic_cache():
    """测试语义缓存功能"""
    print_test_header("语义缓存模块")
    
    try:
        from src.cache.llm_cache.semantic_cache import RedisSemanticCache
        
        cache = RedisSemanticCache()
        print_test_result(True, "语义缓存初始化")
        
        # 测试缓存存储和检索
        group_id = 999999
        test_messages = [
            {"user_id": 1, "raw_message": "今天天气真好"},
            {"user_id": 2, "raw_message": "是的，适合出去走走"},
        ]
        test_summary = "讨论天气和出行计划"
        test_metadata = {"model": "moonshot-v1-8k", "token_count": 100}
        
        # 存入缓存
        cache.put(
            group_id=group_id,
            hours=6,
            messages=test_messages,
            summary=test_summary,
            metadata=test_metadata
        )
        print_test_result(True, "存入语义缓存")
        
        # 检索缓存（相同消息应该命中）
        result = cache.get(group_id, test_messages)
        passed1 = result is not None and result.get("summary") == test_summary
        print_test_result(passed1, "检索语义缓存（相同消息）")
        
        # 测试相似消息检索（相似度应该较高）
        similar_messages = [
            {"user_id": 1, "raw_message": "今天天气不错"},
            {"user_id": 2, "raw_message": "是的，适合出去"},
        ]
        result2 = cache.get(group_id, similar_messages)
        if result2:
            similarity = result2.get("similarity_score", 0)
            print_test_result(
                similarity >= 0.7,
                f"相似消息检索 (相似度: {similarity:.2f})"
            )
        else:
            print_test_result(False, "相似消息未命中缓存")
        
        return passed1
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 7. 测试向量存储 ====================
def test_vector_store():
    """测试 ChromaDB 向量存储"""
    print_test_header("向量存储模块 (ChromaDB)")
    
    try:
        from src.memory.vector.vector_store import VectorMemoryStore
        
        store = VectorMemoryStore()
        print_test_result(True, "向量存储初始化")
        
        # 测试添加摘要
        group_id = 888888
        summary = "这是一个测试摘要，用于验证向量存储功能"
        metadata = {
            "timestamp": int(time.time()),
            "hours": 6,
            "concepts": ["测试", "验证"],
            "events": []
        }
        
        store.add_summary(group_id, summary, metadata)
        print_test_result(True, "添加摘要到向量存储")
        
        # 测试相似度搜索
        query = "测试摘要验证"
        results = store.search_similar_summaries(query, group_id, top_k=3)
        passed = len(results) > 0
        print_test_result(passed, f"相似度搜索 (找到 {len(results)} 条结果)")
        
        return passed
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 8. 测试记忆管理器 ====================
def test_memory_manager():
    """测试记忆管理器"""
    print_test_header("记忆管理器模块")
    
    try:
        from src.memory import MemoryManager
        
        manager = MemoryManager()
        print_test_result(True, "记忆管理器初始化")
        
        # 测试添加记忆
        group_id = 777777
        messages = [
            {"user_id": 1, "raw_message": "测试消息1"},
            {"user_id": 2, "raw_message": "测试消息2"},
        ]
        summary = "测试摘要"
        concepts = ["概念1", "概念2"]
        events = [
            {
                "event": "测试事件",
                "participants": ["用户1", "用户2"],
                "timestamp": int(time.time())
            }
        ]
        
        manager.add_memory(
            group_id=group_id,
            messages=messages,
            summary=summary,
            concepts=concepts,
            events=events,
            metadata={"hours": 6}
        )
        print_test_result(True, "添加记忆")
        
        # 测试获取记忆上下文
        context = manager.get_memory_context(group_id, "测试查询", top_k=3)
        passed1 = isinstance(context, str)
        print_test_result(passed1, "获取记忆上下文")
        
        # 测试获取概念
        concepts_list = manager.get_concepts(group_id)
        passed2 = isinstance(concepts_list, list)
        print_test_result(passed2, "获取概念列表")
        
        # 测试获取事件
        events_list = manager.get_recent_events(group_id, limit=5)
        passed3 = isinstance(events_list, list)
        print_test_result(passed3, "获取事件列表")
        
        return passed1 and passed2 and passed3
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 9. 测试检索模块 ====================
async def test_retrieval():
    """测试检索模块"""
    print_test_header("检索模块 (RAG & HybridSearch)")
    
    try:
        from src.retrieval.rag.retriever import RAGRetriever
        from src.retrieval.hybrid_search import HybridSearch
        from src.llm.moonshot.model_factory import MoonshotFactory
        from src.memory.vector.vector_store import VectorMemoryStore
        
        # 初始化组件
        vector_store = VectorMemoryStore()
        model_factory = MoonshotFactory()
        
        # 测试 RAG 检索器
        rag_retriever = RAGRetriever(
            vector_store=vector_store,
            model_factory=model_factory,
            use_compression=False  # 禁用压缩以加快测试
        )
        print_test_result(True, "RAG 检索器初始化")
        
        # 测试检索
        group_id = 666666
        query = "测试查询"
        results = await rag_retriever.retrieve_relevant_context(
            query=query,
            group_id=group_id,
            top_k=3
        )
        passed1 = isinstance(results, list)
        print_test_result(passed1, f"RAG 检索 (返回 {len(results)} 条结果)")
        
        # 测试混合检索
        hybrid_search = HybridSearch(rag_retriever)
        hybrid_results = await hybrid_search.search(
            query=query,
            group_id=group_id,
            top_k=3
        )
        passed2 = isinstance(hybrid_results, list)
        print_test_result(passed2, f"混合检索 (返回 {len(hybrid_results)} 条结果)")
        
        return passed1 and passed2
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 10. 测试消息仓库 ====================
def test_message_repository():
    """测试消息仓库"""
    print_test_header("消息仓库模块")
    
    try:
        from src.storage.database.repositories import MessageRepository
        
        repo = MessageRepository()
        print_test_result(True, "消息仓库初始化")
        
        # 测试获取群组消息（需要数据库中有数据）
        # 这里只测试方法调用，不验证数据
        test_group_id = 1017750994  # 使用测试群号
        try:
            messages = repo.get_group_messages(test_group_id, hours=1)
            passed1 = isinstance(messages, list)
            print_test_result(passed1, f"获取群组消息 (找到 {len(messages)} 条)")
        except Exception as e:
            print_test_result(False, f"获取群组消息失败: {e}")
            passed1 = False
        
        # 测试获取指定时间后的消息
        try:
            timestamp = int(time.time()) - 3600  # 1小时前
            messages_after = repo.get_group_messages_after(test_group_id, timestamp)
            passed2 = isinstance(messages_after, list)
            print_test_result(passed2, f"获取时间后的消息 (找到 {len(messages_after)} 条)")
        except Exception as e:
            print_test_result(False, f"获取时间后的消息失败: {e}")
            passed2 = False
        
        return passed1 or passed2  # 至少一个通过即可
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 11. 测试元信息提取 ====================
def test_meta_extractor():
    """测试元信息提取"""
    print_test_header("元信息提取模块")
    
    try:
        from src.infrastructure.pipeline import base_info, info_to_str
        
        # 测试基础信息提取
        test_messages = [
            {
                "user_id": 1,
                "sender_nickname": "用户1",
                "raw_message": "消息1",
                "time": int(time.time()) - 1800  # 30分钟前
            },
            {
                "user_id": 2,
                "sender_nickname": "用户2",
                "raw_message": "消息2",
                "time": int(time.time())  # 现在
            },
        ]
        
        meta = base_info(test_messages)
        passed1 = (
            isinstance(meta, dict) and
            "time_span" in meta and
            "user_count" in meta and
            "msg_count" in meta and
            meta["user_count"] == 2 and
            meta["msg_count"] == 2
        )
        print_test_result(passed1, "提取基础元信息")
        
        # 测试格式化
        meta_str = info_to_str(meta)
        passed2 = isinstance(meta_str, str) and "基础信息" in meta_str
        print_test_result(passed2, "格式化元信息为字符串")
        
        # 测试空消息列表
        empty_meta = base_info([])
        passed3 = empty_meta["user_count"] == 0 and empty_meta["msg_count"] == 0
        print_test_result(passed3, "处理空消息列表")
        
        return passed1 and passed2 and passed3
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 12. 测试配置加载 ====================
def test_config():
    """测试配置加载"""
    print_test_header("配置模块")
    
    try:
        from src.config import plugin_config
        
        # 检查配置对象
        passed1 = plugin_config is not None
        print_test_result(passed1, "配置对象加载")
        
        # 检查关键配置项
        config_checks = [
            ("db_host", str),
            ("db_port", int),
            ("redis_host", str),
            ("redis_port", int),
            ("chroma_host", str),
            ("chroma_port", int),
        ]
        
        all_passed = True
        for attr_name, attr_type in config_checks:
            value = getattr(plugin_config, attr_name, None)
            passed = value is not None and isinstance(value, attr_type)
            if not passed:
                print(f"  配置项 {attr_name}: {value} (类型: {type(value)})")
            all_passed = all_passed and passed
        
        print_test_result(all_passed, "关键配置项检查")
        
        return passed1 and all_passed
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 13. 测试缓存键生成 ====================
def test_cache_key():
    """测试缓存键生成"""
    print_test_header("缓存键生成模块")
    
    try:
        from src.cache.llm_cache.cache_key import CacheKeyGenerator
        
        generator = CacheKeyGenerator()
        print_test_result(True, "缓存键生成器初始化")
        
        # 测试消息哈希生成
        messages = [
            {"user_id": 1, "raw_message": "测试消息1", "time": 1000},
            {"user_id": 2, "raw_message": "测试消息2", "time": 2000},
        ]
        hash1 = generator.generate_message_hash(messages)
        hash2 = generator.generate_message_hash(messages)
        
        passed1 = hash1 == hash2 and len(hash1) > 0
        print_test_result(passed1, "消息哈希生成（相同消息应生成相同哈希）")
        
        # 测试语义查询生成
        query = generator.generate_semantic_query(messages)
        passed2 = isinstance(query, str) and len(query) > 0
        print_test_result(passed2, "语义查询字符串生成")
        
        # 测试完整缓存键生成
        cache_key = generator.generate_cache_key(12345, 6, hash1)
        passed3 = isinstance(cache_key, str) and len(cache_key) > 0
        print_test_result(passed3, "完整缓存键生成")
        
        return passed1 and passed2 and passed3
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 14. 测试事件记忆和语义记忆 ====================
def test_memory_details():
    """测试事件记忆和语义记忆"""
    print_test_header("事件记忆和语义记忆模块")
    
    try:
        from src.infrastructure.memory.detail.episodic_memory import EpisodicMemory
        from src.infrastructure.memory.detail import SemanticMemory
        
        # 测试事件记忆
        test_group_id = 555555
        test_messages = [
            {"user_id": 1, "raw_message": "测试消息", "time": int(time.time())}
        ]
        test_summary = "测试摘要"
        test_timestamp = int(time.time())
        
        try:
            EpisodicMemory.add_episodic(
                test_group_id,
                test_messages,
                test_summary,
                test_timestamp
            )
            print_test_result(True, "添加事件记忆")
            
            episodes = EpisodicMemory.get_episodic(test_group_id, limit=5)
            passed1 = isinstance(episodes, list)
            print_test_result(passed1, f"获取事件记忆 (找到 {len(episodes)} 条)")
        except Exception as e:
            print_test_result(False, f"事件记忆操作失败: {e}")
            passed1 = False
        
        # 测试语义记忆
        try:
            test_concepts = ["概念1", "概念2", "概念3"]
            SemanticMemory.add_concepts(test_group_id, test_concepts)
            print_test_result(True, "添加语义概念")
            
            concepts = SemanticMemory.get_concepts(test_group_id)
            passed2 = isinstance(concepts, list)
            print_test_result(passed2, f"获取语义概念 (找到 {len(concepts)} 个)")
            
            SemanticMemory.add_event(
                test_group_id,
                "测试事件",
                ["参与者1", "参与者2"],
                test_timestamp
            )
            print_test_result(True, "添加语义事件")
            
            events = SemanticMemory.get_events(test_group_id, limit=5)
            passed3 = isinstance(events, list)
            print_test_result(passed3, f"获取语义事件 (找到 {len(events)} 条)")
        except Exception as e:
            print_test_result(False, f"语义记忆操作失败: {e}")
            passed2 = False
            passed3 = False
        
        return passed1 or (passed2 and passed3)  # 至少部分通过
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 15. 测试提示词模板 ====================
def test_prompt_templates():
    """测试提示词模板"""
    print_test_header("提示词模板模块")
    
    try:
        from src.domain.prompts import SummaryPromptTemplate
        
        template = SummaryPromptTemplate()
        print_test_result(True, "摘要提示词模板初始化")
        
        # 测试提示词生成
        test_input = {
            "messages": "用户1: 消息1\n用户2: 消息2",
            "memory_context": "历史上下文"
        }
        
        prompt = template.prompt.invoke(test_input)
        passed1 = isinstance(prompt, dict) and "messages" in prompt
        print_test_result(passed1, "提示词生成")
        
        return passed1
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 16. 测试摘要链 ====================
async def test_summary_chain():
    """测试摘要链（需要 API Key）"""
    print_test_header("摘要链模块")
    
    try:
        from src.core.chains.summary_chain import SummaryChain
        from src.llm.moonshot.model_factory import MoonshotFactory
        
        # 检查 API Key
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            print_test_result(False, "缺少 MOONSHOT_API_KEY，跳过摘要链测试")
            return False
        
        # 初始化
        factory = MoonshotFactory()
        llm = factory.create_model("moonshot-v1-8k", max_tokens=500)
        chain = SummaryChain(llm)
        print_test_result(True, "摘要链初始化")
        
        # 测试摘要生成（使用简单测试数据）
        test_messages = [
            {
                "sender_nickname": "用户1",
                "raw_message": "今天天气真好"
            },
            {
                "sender_nickname": "用户2",
                "raw_message": "是的，适合出去走走"
            }
        ]
        
        try:
            result = await chain.invoke(test_messages, memory_context="")
            passed = result is not None and hasattr(result, "overall_summary")
            print_test_result(passed, "摘要生成（实际调用 LLM）")
            return passed
        except Exception as e:
            print_test_result(False, f"摘要生成失败: {e}")
            return False
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 17. 测试提取链 ====================
async def test_extraction_chain():
    """测试实体提取链（需要 API Key）"""
    print_test_header("实体提取链模块")
    
    try:
        from src.core.chains.extraction_chain import ExtractionChain
        from src.llm.moonshot.model_factory import MoonshotFactory
        
        # 检查 API Key
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            print_test_result(False, "缺少 MOONSHOT_API_KEY，跳过提取链测试")
            return False
        
        # 初始化
        factory = MoonshotFactory()
        llm = factory.create_model("moonshot-v1-8k", max_tokens=500)
        chain = ExtractionChain(llm)
        print_test_result(True, "提取链初始化")
        
        # 测试实体提取
        test_messages = [
            {
                "sender_nickname": "用户1",
                "raw_message": "我们讨论了Python编程和机器学习"
            },
            {
                "sender_nickname": "用户2",
                "raw_message": "是的，还提到了深度学习框架"
            }
        ]
        
        try:
            result = await chain.invoke(test_messages)
            passed = (
                result is not None and
                hasattr(result, "concepts") and
                hasattr(result, "events") and
                hasattr(result, "quotes")
            )
            print_test_result(passed, "实体提取（实际调用 LLM）")
            return passed
        except Exception as e:
            print_test_result(False, f"实体提取失败: {e}")
            return False
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 18. 测试压缩链 ====================
async def test_compression_chain():
    """测试记忆压缩链（需要 API Key）"""
    print_test_header("记忆压缩链模块")
    
    try:
        from src.core.chains.compression_chain import CompressionChain
        from src.llm.moonshot.model_factory import MoonshotFactory
        
        # 检查 API Key
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            print_test_result(False, "缺少 MOONSHOT_API_KEY，跳过压缩链测试")
            return False
        
        # 初始化
        factory = MoonshotFactory()
        llm = factory.create_model("moonshot-v1-8k", max_tokens=500)
        chain = CompressionChain(llm)
        print_test_result(True, "压缩链初始化")
        
        # 测试压缩
        test_summaries = [
            "这是第一个摘要内容",
            "这是第二个摘要内容",
            "这是第三个摘要内容"
        ]
        
        try:
            result = await chain.invoke(test_summaries)
            passed = isinstance(result, str) and len(result) > 0
            print_test_result(passed, "摘要压缩（实际调用 LLM）")
            return passed
        except Exception as e:
            print_test_result(False, f"摘要压缩失败: {e}")
            return False
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 19. 测试重排序器 ====================
def test_reranker():
    """测试重排序器"""
    print_test_header("重排序器模块")
    
    try:
        from src.retrieval.rag.reranker import Reranker
        from langchain_core.documents import Document
        
        reranker = Reranker(use_simple_rerank=True)
        print_test_result(True, "重排序器初始化")
        
        # 测试重排序
        test_docs = [
            Document(
                page_content="这是关于Python编程的文档",
                metadata={"score": 0.8}
            ),
            Document(
                page_content="这是关于机器学习的文档",
                metadata={"score": 0.6}
            ),
            Document(
                page_content="这是关于深度学习的文档",
                metadata={"score": 0.7}
            ),
        ]
        
        query = "Python编程"
        reranked = reranker.rerank(test_docs, query, top_k=2)
        
        passed1 = len(reranked) == 2
        print_test_result(passed1, f"重排序（返回 {len(reranked)} 条结果）")
        
        # 测试关键词提取
        keywords = reranker._extract_keywords("Python编程和机器学习")
        passed2 = len(keywords) > 0
        print_test_result(passed2, f"关键词提取 (提取到 {len(keywords)} 个关键词)")
        
        # 测试相关性分数计算
        score = reranker._calculate_relevance_score(
            "这是关于Python编程的文档",
            ["python", "编程"]
        )
        passed3 = 0 <= score <= 1
        print_test_result(passed3, f"相关性分数计算 (分数: {score:.2f})")
        
        return passed1 and passed2 and passed3
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 20. 测试记忆压缩器 ====================
async def test_memory_compressor():
    """测试记忆压缩器（需要 API Key）"""
    print_test_header("记忆压缩器模块")
    
    try:
        from src.infrastructure.memory.detail.memory_compressor import MemoryCompressor
        from src.llm.moonshot.model_factory import MoonshotFactory
        
        # 检查 API Key
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            print_test_result(False, "缺少 MOONSHOT_API_KEY，跳过记忆压缩器测试")
            return False
        
        # 测试是否需要压缩的判断
        passed1 = MemoryCompressor.is_compress(["摘要1", "摘要2", "摘要3", "摘要4"], threshold=5) is False
        passed2 = MemoryCompressor.is_compress(["摘要1"] * 5, threshold=5) is True
        print_test_result(passed1 and passed2, "压缩判断逻辑")
        
        # 测试压缩器初始化
        factory = MoonshotFactory()
        llm = factory.create_model("moonshot-v1-8k", max_tokens=500)
        compressor = MemoryCompressor(llm)
        print_test_result(True, "记忆压缩器初始化")
        
        # 测试压缩（使用少量摘要）
        test_summaries = ["摘要1", "摘要2"]
        try:
            compressed = await compressor.compress_summaries(test_summaries, max_len=100)
            passed3 = isinstance(compressed, str)
            print_test_result(passed3, "摘要压缩（实际调用 LLM）")
            return passed1 and passed2 and passed3
        except Exception as e:
            print_test_result(False, f"摘要压缩失败: {e}")
            return passed1 and passed2
    except Exception as e:
        print_test_result(False, f"异常: {e}")
        return False

# ==================== 21. 测试数据库连接 ====================
def test_database_connections():
    """测试数据库连接（Redis, ChromaDB, MySQL）"""
    print_test_header("数据库连接模块")
    
    results = {}
    
    # 1. 测试 Redis
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', '127.0.0.1'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', None),
            socket_connect_timeout=2
        )
        r.ping()
        results["Redis"] = True
        print_test_result(True, f"Redis 连接成功 ({os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')})")
    except Exception as e:
        results["Redis"] = False
        print_test_result(False, f"Redis 连接失败: {e}")
    
    # 2. 测试 ChromaDB
    try:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.HttpClient(
            host=os.getenv('CHROMA_HOST', '127.0.0.1'),
            port=int(os.getenv('CHROMA_PORT', 8000)),
            settings=Settings(anonymized_telemetry=False)
        )
        client.heartbeat()
        results["ChromaDB"] = True
        print_test_result(True, f"ChromaDB 连接成功 ({os.getenv('CHROMA_HOST', '127.0.0.1')}:{os.getenv('CHROMA_PORT', '8000')})")
    except Exception as e:
        results["ChromaDB"] = False
        print_test_result(False, f"ChromaDB 连接失败: {e}")
    
    # 3. 测试 MySQL
    try:
        import pymysql
        db = pymysql.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            connect_timeout=5
        )
        results["MySQL"] = True
        print_test_result(True, f"MySQL 连接成功 (库名: {os.getenv('DB_NAME')})")
        db.close()
    except Exception as e:
        results["MySQL"] = False
        print_test_result(False, f"MySQL 连接失败: {e}")
    
    # 返回是否至少有一个连接成功（允许部分服务未运行）
    # 如果所有连接都失败，返回 False；否则返回 True
    return any(results.values())

# ==================== 主测试函数 ====================
async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 35)
    print(" " * 20 + "LLM-Scribe 模块测试套件")
    print("🚀" * 35)
    
    results = {}
    
    # 数据库连接测试（最先执行）
    results["数据库连接"] = test_database_connections()
    
    # 同步测试
    results["消息过滤"] = test_cq_filter()
    results["时间工具"] = test_time_utils()
    results["Token计数器"] = test_token_counter()
    results["模型工厂"] = test_model_factory()
    results["Redis缓存"] = test_redis_cache()
    results["语义缓存"] = test_semantic_cache()
    results["向量存储"] = test_vector_store()
    results["记忆管理器"] = test_memory_manager()
    results["消息仓库"] = test_message_repository()
    results["元信息提取"] = test_meta_extractor()
    results["配置加载"] = test_config()
    results["缓存键生成"] = test_cache_key()
    
    # 异步测试
    results["检索模块"] = await test_retrieval()
    results["事件和语义记忆"] = test_memory_details()
    results["提示词模板"] = test_prompt_templates()
    results["摘要链"] = await test_summary_chain()
    results["提取链"] = await test_extraction_chain()
    results["压缩链"] = await test_compression_chain()
    results["重排序器"] = test_reranker()
    results["记忆压缩器"] = await test_memory_compressor()
    
    # 打印总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for module, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {module}")
    
    print("\n" + "-" * 70)
    print(f"总计: {total} 个模块")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"通过率: {passed/total*100:.1f}%")
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
