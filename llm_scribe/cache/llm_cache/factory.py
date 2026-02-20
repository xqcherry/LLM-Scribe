from .semantic_cache import RedisSemanticCache


class LLMCacheFactory:
    """LLM 缓存工厂"""
    @staticmethod
    def create_cache(**kwargs):
        """创建 Redis 语义缓存实例"""
        return RedisSemanticCache(**kwargs)