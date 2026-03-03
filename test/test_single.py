"""
单独测试模块运行器
简单版本：直接调用 test_all_modules.py 中的测试函数

使用方法：
1. 在下面的 TEST_MODULES 列表中添加要测试的模块名
2. 运行: python test/test_single.py
"""
import sys
import asyncio
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 添加 test 目录到路径
test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, test_dir)

# 导入测试模块
import test_all_modules

# ==================== 配置：要测试的模块 ====================
# 在这里添加要测试的模块名（直接复制粘贴模块名即可）
TEST_MODULES = [
    # "数据库连接",
    "消息过滤",
    # "时间工具",
    # "Token计数器",
    # "模型工厂",
    # "Redis缓存",
    # "语义缓存",
    # "向量存储",
    # "记忆管理器",
    # "检索模块",
    # "消息仓库",
    # "元信息提取",
    # "配置加载",
    # "缓存键生成",
    # "事件和语义记忆",
    # "提示词模板",
    # "摘要链",
    # "提取链",
    # "压缩链",
    # "重排序器",
    # "记忆压缩器",
]

# 模块名到测试函数的映射
MODULE_MAP = {
    "数据库连接": (test_all_modules.test_database_connections, False),
    "消息过滤": (test_all_modules.test_cq_filter, False),
    "时间工具": (test_all_modules.test_time_utils, False),
    "Token计数器": (test_all_modules.test_token_counter, False),
    "模型工厂": (test_all_modules.test_model_factory, False),
    "Redis缓存": (test_all_modules.test_redis_cache, False),
    "语义缓存": (test_all_modules.test_semantic_cache, False),
    "向量存储": (test_all_modules.test_vector_store, False),
    "记忆管理器": (test_all_modules.test_memory_manager, False),
    "检索模块": (test_all_modules.test_retrieval, True),
    "消息仓库": (test_all_modules.test_message_repository, False),
    "元信息提取": (test_all_modules.test_meta_extractor, False),
    "配置加载": (test_all_modules.test_config, False),
    "缓存键生成": (test_all_modules.test_cache_key, False),
    "事件和语义记忆": (test_all_modules.test_memory_details, False),
    "提示词模板": (test_all_modules.test_prompt_templates, False),
    "摘要链": (test_all_modules.test_summary_chain, True),
    "提取链": (test_all_modules.test_extraction_chain, True),
    "压缩链": (test_all_modules.test_compression_chain, True),
    "重排序器": (test_all_modules.test_reranker, False),
    "记忆压缩器": (test_all_modules.test_memory_compressor, True),
}


async def run_tests():
    """运行测试"""
    print("\n" + "=" * 70)
    print("🧪 开始测试")
    print("=" * 70)
    
    results = {}
    
    for module_name in TEST_MODULES:
        if module_name not in MODULE_MAP:
            print(f"❌ 错误: 未找到模块 '{module_name}'")
            print(f"   可用模块: {', '.join(MODULE_MAP.keys())}")
            results[module_name] = False
            continue
        
        func, is_async = MODULE_MAP[module_name]
        
        print(f"\n🚀 测试: {module_name}")
        print("-" * 70)
        
        try:
            if is_async:
                result = await func()
            else:
                result = func()
            results[module_name] = result
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results[module_name] = False
    
    # 打印总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    for module, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {module}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print("\n" + "-" * 70)
    print(f"总计: {total} 个模块")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    if total > 0:
        print(f"通过率: {passed/total*100:.1f}%")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
