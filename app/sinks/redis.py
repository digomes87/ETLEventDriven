import json
from typing import Any

from app.sinks.base import DataSink
from app.utils.cache import RedisCacheClient


class RedisSink(DataSink):
    def __init__(self, client: RedisCacheClient | None = None) -> None:
        self.client = client or RedisCacheClient()

    async def write(self, record: dict[str, Any]) -> None:
        payload = {
            "id": record.get("id"),
            "status": record.get("status"),
        }
        key = record.get("cache_key")
        if not key:
            return
        await self.client.set(key, json.dumps(payload), ttl_seconds=3600)
