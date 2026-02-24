from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IngestionSource, ProcessedRecord, RawEvent


class EventRepository(ABC):
    @abstractmethod
    async def get_or_create_source(self, source_name: str) -> IngestionSource:
        raise NotImplementedError

    @abstractmethod
    async def ingest_event(self, source_name: str, payload: dict[str, Any]) -> RawEvent:
        raise NotImplementedError

    @abstractmethod
    async def mark_processed(
        self,
        raw_event: RawEvent,
        status: str,
        result_payload: dict[str, Any] | None = None,
    ) -> ProcessedRecord:
        raise NotImplementedError


class CacheClient(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError


class MessageQueueClient(ABC):
    @abstractmethod
    async def publish(self, routing_key: str, message: dict[str, Any]) -> None:
        raise NotImplementedError


class SessionFactory(ABC):
    @abstractmethod
    def create_session(self) -> AsyncSession:
        raise NotImplementedError
