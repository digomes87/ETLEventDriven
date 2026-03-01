from typing import Any

from app.interfaces import EventRepository
from app.sinks.base import DataSink


class PostgresSink(DataSink):
    def __init__(self, event_repository: EventRepository) -> None:
        self.repository = event_repository

    async def write(self, record: dict[str, Any]) -> None:
        await self.repository.mark_processed(
            raw_event=record["raw_event"],
            status=record.get("status", "Success"),
            result_payload=record.get("payload"),
        )
