from typing import Any

from app.sinks.base import DataSink


class DynamoSink(DataSink):
    def __init__(self) -> None:
        self._disabled = True

    async def write(self, record: dict[str, Any]) -> None:
        if self._disabled:
            return
