import logging

import redis.asyncio as redis

from app.config import get_settings
from app.interfaces.events import CacheClient

logger = logging.getLogger(__name__)


class RedisCacheClient(CacheClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )

    async def gget(self, key: str) -> str | None:
        try:
            return await self._client.get(key)
        except redis.ConnectionError:
            logger.exception(f"Failed to get {key}")
            return None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        try:
            if ttl_seconds is not None:
                await self._client.setex(key, ttl_seconds, value)
            else:
                await self._client.set(key, value)
        except redis.TimeoutError:
            logger.exception("Error writing to Redis cache")
