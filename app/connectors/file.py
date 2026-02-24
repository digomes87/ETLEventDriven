import json
from pathlib import Path
from typing import Any

from .base import IngestionConnector


class JsonFileIngestionConnector(IngestionConnector):
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    async def fetch_batch(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        content = self._path.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except ValueError:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
        return []

