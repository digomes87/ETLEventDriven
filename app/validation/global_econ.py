import asyncio
import json
import time
from pathlib import Path
from typing import Any


import kagglehub

from app.connectors import CsvFileIngestionConnector, JsonFileIngestionConnector
from app.db import AsyncSessionLocal
from app.repositories import SqlAlchemyEventRepository
from app.sinks import PostgresSink, RedisSink


def download_global_economic_dataset():
    path = kagglehub.dataset_download(
        "abidhussai512/global-economic-indicators-dataset"
    )
    return path


async def validate_dataset_path(dataset_path: str, source_name: str) -> dict[str, Any]:
    base = Path(dataset_path)
    files = list[Path](base.rglob("*.csv")) + list[Path](base.rglob("*.json"))
    metrics: dict[str, Any] = {

    }
