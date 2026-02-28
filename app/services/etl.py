import logging
from typing import Any

from app.interfaces.events import EventRepository
from app.models import ProcessedRecord, RawEvent

logger = logging.getLogger(__name__)


async def ingest_event(
    repository: EventRepository,
    source_name: str,
    payload: dict[str, Any],
) -> RawEvent:
    raw_event = await repository.ingest_event(source_name=source_name, payload=payload)
    logger.info(f"Ingested event {raw_event}", extra={"source_name": source_name})
    return raw_event


async def ingest_and_mark_success(
    repository: EventRepository,
    source_name: str,
    payload: dict[str, Any],
) -> tuple[RawEvent, ProcessedRecord]:
    raw_event = await ingest_event(
        repository=repository, source_name=source_name, payload=payload
    )
    record = await mark_processed(
        repository=repository,
        raw_event=raw_event,
        status="success",
        result_payload=payload,
    )
    return raw_event, record


async def mark_processed(
    repository: EventRepository,
    raw_event: RawEvent,
    status: str,
    result_payload: dict[str, Any] | None = None,
) -> ProcessedRecord:
    record = await repository.mark_processed(
        raw_event=raw_event,
        status=status,
        result_payload=result_payload,
    )
    logger.info(f"Processed event {raw_event}", extra={"status": status})
    return record
