from typing import Protocol, Optional, List, Dict
from .gptcache import LLMSemanticCache
from .semantic_cache import RedisSemanticCache


class LLMCacheInterface(Protocol):
    """缓存接口协议"""
    def get(self, group_id: int, hours: int, messages: List[Dict]) -> Optional[Dict]:
        ...
    def put(self, group_id: int, hours: int, messages: List[Dict], summary: str, metadata: Dict = None):
        ...


class LLMCacheFactory:
    """缓存工厂"""
    @staticmethod
    def create_cache(cache_type: str = "gptcache", **kwargs):
        if cache_type == "gptcache":
            return LLMSemanticCache(**kwargs)
        elif cache_type == "redis":
            return RedisSemanticCache(**kwargs)
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")