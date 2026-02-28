from abc import ABC, abstractmethod
from typing import Any


class IngestionConnector(ABC):
    @abstractmethod
    async def fetch_batch(self) -> list[dict[str, Any]]:
        raise NotImplementedError
