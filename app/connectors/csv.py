import csv
from pathlib import Path
from typing import Any

from .base import IngestionConnector


class CsvFileIngestionConnector(IngestionConnector):
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    async def fetch_batch(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows: list[dict[str, Any]] = []
            for row in reader:
                cleaned = {k: v for k, v in row.items() if k is not None}
                if cleaned:
                    rows.append(cleaned)
        return rows

