from abc import ABC, abstractmethod
from typing import Any


class DataSink(ABC):
    @abstractmethod
    async def write(self, record: dict[str, Any]) -> None:
        raise NotImplementedError
