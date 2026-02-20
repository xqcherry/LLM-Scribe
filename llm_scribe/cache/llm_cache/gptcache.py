import json
import time
from typing import Optional, List, Dict
from gptcache import Cache, Config
from gptcache.manager import get_data_manager
from gptcache.embedding import Onnx as EmbeddingOnnx
from gptcache.similarity_evaluation import SearchDistanceEvaluation
from gptcache.adapter.api import get, put
from gptcache.processor.pre import get_prompt
from ...config import get_config


class LLMSemanticCache:
    """基于 GPTCache 的语义缓存"""

    def __init__(
        self,
        similarity_threshold: float = None,
        cache_dir: str = None,
    ):
        config = get_config()
        self.similarity_threshold = similarity_threshold or config.cache_similarity_threshold
        self.cache_dir = cache_dir or config.gptcache_dir

        self.embedding = EmbeddingOnnx()
        self.evaluation = SearchDistanceEvaluation()

        self.cache = Cache()
        self.data_manager = get_data_manager()
        cache_config = Config(similarity_threshold=self.similarity_threshold)
        self.cache.init(
            pre_embedding_func=get_prompt,
            embedding_func=self.embedding.get_embedding,
            data_manager=self.data_manager,
            similarity_evaluation=self.evaluation,
            config=cache_config,
            cache_enable_func=lambda x, y: True,
        )

    def messages_to_query(
        self,
        messages: List[Dict],
    )->str:
        """将消息转换为查询字符串"""
        participants = set(
            m.get("sender_nickname", "")
            for m in messages
            if m.get("sender_nickname")
        )

        if len(messages) < 10:
            message_text = "\n".join(
                m.get("raw_message", "")[:100]
                for m in messages
            )
        else:
            head = messages[:3]
            tail = messages[-3:]
            middle_idx = len(messages) // 2
            middle = messages[middle_idx:middle_idx+3]
            message_text = "\n".join(
                m.get("raw_message", "")[:100]
                for m in head + middle + tail
            )

        query = f"群组消息摘要：{len(participants)}人，{len(messages)}条消息\n{message_text}"
        return query

    def get(
        self,
        group_id: int,
        hours: int,
        messages: List[Dict]
    ) -> Optional[Dict]:
        """获取缓存"""
        query = self.messages_to_query(messages)

        try:
            cached_result = get(query, cache_obj=self.cache)
            if cached_result:
                result = json.loads(cached_result)
                # 检查群组和时间窗口是否匹配
                if result.get("group_id") == group_id and result.get("hours") == hours:
                    return {
                        "summary": result.get("summary"),
                        "metadata": result.get("metadata", {}),
                        "cached": True,
                        "similarity_score": result.get("similarity_score", 1.0)
                    }
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Cache get error: {e}")
        except Exception as e:
            print(f"Unexpected cache error: {e}")
        return None

    def put(
        self,
        group_id: int,
        hours: int,
        messages: List[Dict],
        summary: str,
        metadata: Dict = None
    ):
        """存入缓存"""
        query = self.messages_to_query(messages)

        cache_data = {
            "summary": summary,
            "metadata": metadata or {},
            "group_id": group_id,
            "hours": hours,
            "timestamp": int(time.time())
        }

        try:
            put(query, json.dumps(cache_data, ensure_ascii=False), cache_obj=self.cache)
        except Exception as e:
            print(f"Cache put error: {e}")