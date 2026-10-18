import asyncio
import time
from typing import Dict, Any, Optional
from loguru import logger


class SimpleMemoryCache:
    def __init__(self, ttl_seconds: int = 3600):

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()  # Shared Lock for concurrency safety
        self.ttl = ttl_seconds

    async def get(self, key: str) -> Optional[Any]:

        async with self._lock:
            item = self._cache.get(key)
            if not item:
                return None

            
            if time.time() > item["expires_at"]:
                del self._cache[key]
                logger.info(f"[CACHE EXPIRED] Key: {key}")
                return None

            logger.info(f"[CACHE HIT] Key: {key}")
            return item["data"]

    async def set(self, key: str, value: Any):

        async with self._lock:
            self._cache[key] = {"data": value, "expires_at": time.time() + self.ttl}
            logger.info(f"[CACHE SET] Key: {key}")

    async def clear(self):
  
        async with self._lock:
            self._cache.clear()


scrape_cache = SimpleMemoryCache(ttl_seconds=3600)
