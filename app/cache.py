"""Redis cache implementation."""
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any
from app.config import settings

class RedisCache:
    """Redis cache manager class."""
    
    def __init__(self, url: str):
        """Initialize Redis connection."""
        self.redis = redis.from_url(url)
        
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get and deserialize JSON from cache."""
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
        
    async def set_json(self, key: str, data: Any, ttl: int) -> None:
        """Serialize and set JSON in cache with TTL."""
        await self.redis.set(key, json.dumps(data), ex=ttl)
        
    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        await self.redis.delete(key)
        
    async def flush(self) -> None:
        """Flush the entire database."""
        await self.redis.flushdb()
        
    async def ping(self) -> bool:
        """Ping the Redis server."""
        try:
            return await self.redis.ping()
        except Exception:
            return False
            
    async def close(self) -> None:
        """Close the Redis connection."""
        await self.redis.aclose()

cache = RedisCache(settings.REDIS_URL)
