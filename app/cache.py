"""Redis cache implementation with in-memory fallback."""
import json
import time
from typing import Optional, Dict, Any
from app.config import settings

class RedisCache:
    """Redis cache manager class with automatic in-memory fallback if Redis server is offline."""
    
    def __init__(self, url: str):
        """Initialize Redis connection and in-memory fallback store."""
        self.url = url
        self._memory_cache: dict[str, Any] = {}
        self._memory_ttl: dict[str, float] = {}
        try:
            import redis.asyncio as redis
            self.redis = redis.from_url(url, socket_connect_timeout=0.5)
            self._has_redis = True
        except Exception:
            self._has_redis = False
            self.redis = None
        
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get and deserialize JSON from cache."""
        if self._has_redis and self.redis:
            try:
                data = await self.redis.get(key)
                if data:
                    return json.loads(data)
                return None
            except Exception:
                # Redis not reachable or failed - fall back to memory
                pass
        
        now = time.time()
        if key in self._memory_cache:
            if key in self._memory_ttl and self._memory_ttl[key] < now:
                del self._memory_cache[key]
                del self._memory_ttl[key]
                return None
            return self._memory_cache[key]
        return None
        
    async def set_json(self, key: str, data: Any, ttl: int) -> None:
        """Serialize and set JSON in cache with TTL."""
        if self._has_redis and self.redis:
            try:
                await self.redis.set(key, json.dumps(data), ex=ttl)
                return
            except Exception:
                pass
        
        self._memory_cache[key] = data
        self._memory_ttl[key] = time.time() + ttl
        
    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        if self._has_redis and self.redis:
            try:
                await self.redis.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)
        self._memory_ttl.pop(key, None)
        
    async def flush(self) -> None:
        """Flush the entire database."""
        if self._has_redis and self.redis:
            try:
                await self.redis.flushdb()
            except Exception:
                pass
        self._memory_cache.clear()
        self._memory_ttl.clear()
        
    async def ping(self) -> bool:
        """Ping the Redis server."""
        if self._has_redis and self.redis:
            try:
                return await self.redis.ping()
            except Exception:
                return False
        return True
            
    async def close(self) -> None:
        """Close the Redis connection."""
        if self._has_redis and self.redis:
            try:
                await self.redis.aclose()
            except Exception:
                pass

cache = RedisCache(settings.REDIS_URL)
