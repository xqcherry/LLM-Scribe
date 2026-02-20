import redis
import json
from typing import Optional, Any
from ...config import get_config


class RedisDataCache:
    """Redis 数据缓存"""
    
    def __init__(self):
        config = get_config()
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=config.redis_password,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        try:
            self.redis.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            self.redis.delete(key)
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
