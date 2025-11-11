"""
Cache Layer with Redis and In-Memory Fallback
Provides caching for expensive operations (Council analyses, persona enrichment).
"""
import os
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta
from logger import logger
from env_validator import get_config_bool, get_config

# Try to import Redis, fallback to in-memory cache if not available
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class InMemoryCache:
    """Simple in-memory cache fallback (not distributed)"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if key in self._cache:
            import time
            if self._expiry.get(key, 0) > time.time():
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._expiry[key]
        return None
    
    async def set(self, key: str, value: str, ttl: int):
        """Set value in cache with TTL"""
        import time
        self._cache[key] = value
        self._expiry[key] = time.time() + ttl
    
    async def delete(self, key: str):
        """Delete value from cache"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    async def close(self):
        """Close (no-op for in-memory)"""
        pass


class CacheManager:
    """
    Unified cache manager with Redis and in-memory fallback.
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache = InMemoryCache()
        self.redis_enabled = False
    
    async def initialize(self):
        """Initialize cache connection"""
        redis_enabled = get_config_bool("REDIS_ENABLED", False)
        redis_url = get_config("REDIS_URL", "")
        
        if redis_enabled and redis_url and REDIS_AVAILABLE:
            try:
                logger.info("Initializing Redis cache", url=redis_url)
                self.redis_client = await redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(
                    "Failed to connect to Redis, using in-memory cache",
                    error=str(e),
                )
                self.redis_enabled = False
        else:
            logger.info("Using in-memory cache (Redis not configured)")
            self.redis_enabled = False
    
    async def close(self):
        """Close cache connection"""
        if self.redis_client:
            logger.info("Closing Redis connection")
            await self.redis_client.close()
            self.redis_client = None
        
        await self.memory_cache.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        Returns None if not found or expired.
        """
        try:
            if self.redis_enabled and self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    logger.debug("Cache hit (Redis)", key=key)
                    return json.loads(value)
            else:
                value = await self.memory_cache.get(key)
                if value:
                    logger.debug("Cache hit (memory)", key=key)
                    return json.loads(value)
            
            logger.debug("Cache miss", key=key)
            return None
        
        except Exception as e:
            logger.warning("Cache get error", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time to live in seconds
        """
        try:
            serialized = json.dumps(value, default=str)
            
            if self.redis_enabled and self.redis_client:
                await self.redis_client.setex(key, ttl_seconds, serialized)
                logger.debug("Cache set (Redis)", key=key, ttl=ttl_seconds)
            else:
                await self.memory_cache.set(key, serialized, ttl_seconds)
                logger.debug("Cache set (memory)", key=key, ttl=ttl_seconds)
        
        except Exception as e:
            logger.warning("Cache set error", key=key, error=str(e))
    
    async def delete(self, key: str):
        """Delete value from cache"""
        try:
            if self.redis_enabled and self.redis_client:
                await self.redis_client.delete(key)
                logger.debug("Cache delete (Redis)", key=key)
            else:
                await self.memory_cache.delete(key)
                logger.debug("Cache delete (memory)", key=key)
        
        except Exception as e:
            logger.warning("Cache delete error", key=key, error=str(e))
    
    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.
        Only works with Redis (scan), in-memory will skip.
        """
        if not self.redis_enabled or not self.redis_client:
            logger.debug("Pattern invalidation skipped (in-memory cache)")
            return
        
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis_client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            
            logger.info("Cache pattern invalidated", pattern=pattern, deleted=deleted)
        
        except Exception as e:
            logger.warning("Cache pattern invalidation error", pattern=pattern, error=str(e))


# Global cache instance
cache_manager = CacheManager()


# Helper functions for common cache operations
def make_cache_key(prefix: str, *parts: str) -> str:
    """
    Create a cache key from parts.
    
    Args:
        prefix: Cache key prefix (e.g., 'council', 'persona')
        *parts: Additional parts to include in key
    
    Returns:
        Cache key string
    """
    key_parts = [prefix] + list(parts)
    return ":".join(key_parts)


def hash_data(data: Any) -> str:
    """
    Create a hash of data for cache key.
    Useful for caching based on request parameters.
    """
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


# TTL constants (in seconds)
TTL_COUNCIL_ANALYSIS = 60 * 60  # 1 hour
TTL_PERSONA_ENRICHED = 24 * 60 * 60  # 24 hours
TTL_EXPERT_RECOMMENDATIONS = 60 * 60  # 1 hour
TTL_SHORT = 5 * 60  # 5 minutes


__all__ = [
    "cache_manager",
    "make_cache_key",
    "hash_data",
    "TTL_COUNCIL_ANALYSIS",
    "TTL_PERSONA_ENRICHED",
    "TTL_EXPERT_RECOMMENDATIONS",
    "TTL_SHORT",
]

