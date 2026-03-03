from typing import Optional, List, Dict
import redis, json, time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.llm.embedding.embedding_model import get_embeddings
from src.cache.llm_cache.cache_key import CacheKeyGenerator
from src.config import plugin_config as config


class RedisSemanticCache:
    """基于 Redis 的语义缓存实现"""

    def __init__(
            self,
            namespace: str = "llm_cache"
    ):
        password = config.redis_password.get_secret_value() \
            if config.redis_password else None

        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=password,
            decode_responses=True
        )

        self.similarity_threshold = config.cache_similarity_threshold
        self.namespace = namespace
        self.cache_key_gen = CacheKeyGenerator()

        self.embedding_model = get_embeddings()
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本的 Embedding"""
        vector = self.embedding_model.embed_query(text)
        return np.array(vector)
    
    def _generate_key(self, group_id: int, query_hash: str) -> str:
        """生成 Redis key"""
        return f"{self.namespace}:group:{group_id}:{query_hash}"
    
    def _messages_to_query(self, messages: List[Dict]) -> str:
        """将消息转换为查询字符串"""
        return self.cache_key_gen.generate_semantic_query(messages)
    
    def _get_all_cached_queries(self, group_id: int) -> List[tuple]:
        """获取群组的所有缓存查询"""
        pattern = f"{self.namespace}:group:{group_id}:*"
        keys = self.redis.keys(pattern)
        
        results = []
        for key in keys:
            data = self.redis.get(key)
            if data:
                cache_data = json.loads(data)
                results.append((
                    cache_data.get("query_embedding"),
                    cache_data.get("summary"),
                    cache_data.get("metadata", {})
                ))
        return results
    
    def get(
        self,
        group_id: int,
        messages: List[Dict]
    ) -> Optional[Dict]:
        """语义检索缓存"""
        query_text = self._messages_to_query(messages)
        query_embedding = self._get_embedding(query_text)

        cached_queries = self._get_all_cached_queries(group_id)
        
        if not cached_queries:
            return None
        
        # 计算相似度
        best_match = None
        best_similarity = 0.0
        
        for cached_embedding_str, summary, metadata in cached_queries:
            cached_embedding = np.array(json.loads(cached_embedding_str))
            
            # 计算余弦相似度
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                cached_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (summary, metadata)
        
        # 如果相似度超过阈值，返回缓存结果
        if best_similarity >= self.similarity_threshold and best_match:
            return {
                "summary": best_match[0],
                "metadata": best_match[1],
                "cached": True,
                "similarity_score": float(best_similarity)
            }
        
        return None
    
    def put(
        self,
        group_id: int,
        hours: int,
        messages: List[Dict],
        summary: str,
        metadata: Dict = None,
        ttl: int = 86400  # 24 小时过期
    ):
        """存入缓存"""
        query_text = self._messages_to_query(messages)
        query_embedding = self._get_embedding(query_text)
        query_hash = self.cache_key_gen.generate_message_hash(messages)
        
        cache_data = {
            "query_embedding": json.dumps(query_embedding.tolist()),
            "summary": summary,
            "metadata": metadata or {},
            "group_id": group_id,
            "hours": hours,
            "timestamp": int(time.time())
        }
        
        key = self._generate_key(group_id, query_hash)
        self.redis.setex(
            key,
            ttl,
            json.dumps(cache_data, ensure_ascii=False)
        )
