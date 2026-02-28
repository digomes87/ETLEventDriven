import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.events import EventRepository
from app.models import IngestionSource, ProcessedRecord, RawEvent


class SqlAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_source(self, source_name: str) -> IngestionSource:
        result = await self.session.execute(
            select(IngestionSource).where(IngestionSource.name == source_name)
        )
        source = result.scalar_one_or_none()
        if source is not None:
            return source

        source = IngestionSource(name=source_name)
        self.session.add(source)
        try:
            await self.session.flush()
            return source
        except IntegrityError:
            await self.session.rollback()
            result = await self.session.execute(
                select(IngestionSource).where(IngestionSource.name == source_name),
            )
            existing = result.scalar_one()
            return existing

    async def ingest_event(self, source_name: str, payload: dict[str, Any]) -> RawEvent:
        source = await self.get_or_create_source(source_name)
        raw_event = RawEvent(
            source_id=source.id,
            payload=json.dumps(payload),
        )
        self.session.add(raw_event)
        return raw_event

    async def mark_processed(
            self,
            raw_event: RawEvent,
            status: str,
            result_payload: dict[str, Any] | None =  None,
    ) -> ProcessedRecord:
        record = ProcessedRecord(
            raw_event_id=raw_event.id,
            status=status,
            result_payload=json.dumps(result_payload) if result_payload is not None else None,
        )
        self.session.add(record)
        await self.session.flush()
        return record

