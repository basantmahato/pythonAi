import json
import logging
import time
from typing import Any, Optional
from redis import Redis
from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self):
        self.redis: Optional[Redis] = None
        self._memory_cache: dict[str, tuple[Any, float]] = {}
        self._init_redis()

    def _init_redis(self):
        try:
            client = Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            client.ping()
            self.redis = client
            logger.info("Connected to Redis cache.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}. Using in-memory fallback cache.")
            self.redis = None

    def get(self, key: str) -> Optional[Any]:
        if self.redis:
            try:
                val = self.redis.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")

        # In-memory fallback
        item = self._memory_cache.get(key)
        if item:
            value, expires_at = item
            if expires_at == 0 or expires_at > time.time():
                return value
            else:
                del self._memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        if self.redis:
            try:
                self.redis.setex(key, ttl_seconds, json.dumps(value))
                return True
            except Exception as e:
                logger.debug(f"Redis set error: {e}")

        # In-memory fallback
        expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else 0
        self._memory_cache[key] = (value, expires_at)
        return True

    def delete(self, key: str) -> bool:
        if self.redis:
            try:
                self.redis.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)
        return True

    def clear_pattern(self, pattern: str) -> int:
        count = 0
        if self.redis:
            try:
                keys = self.redis.keys(pattern)
                if keys:
                    count = self.redis.delete(*keys)
            except Exception:
                pass
        # Memory cache cleanup
        prefix = pattern.replace("*", "")
        keys_to_del = [k for k in self._memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            del self._memory_cache[k]
            count += 1
        return count


cache = CacheManager()
