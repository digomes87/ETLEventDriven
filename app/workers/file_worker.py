import argparse
import asyncio
import logging
from pathlib import Path

from app.connectors import JsonFileIngestionConnector
from app.db import AsyncSessionLocal
from app.repositories import SqlAlchemyEventRepository
from app.services import etl as etl_services
from app.sinks import PostgresSink, RedisSink


logger = logging.getLogger(__name__)


async def process_file_once(path: str, source_name: str) -> None:
    connector = JsonFileIngestionConnector(path)
    batch = await connector.fetch_batch()
    if not batch:
        return
    async with AsyncSessionLocal() as session:
        repository = SqlAlchemyEventRepository(session=session)
        pg_sink = PostgresSink(repository)
        redis_sink = RedisSink()
        for payload in batch:
            raw_event = await etl_services.ingest_event(
                repository=repository,
                source_name=source_name,
                payload=payload,
            )
            record = {
                "raw_event": raw_event,
                "status": "SUCCESS",
                "payload": payload,
            }
            await pg_sink.write(record)
            cache_key = f"worker:processed:{raw_event.id}"
            await redis_sink.write(
                {
                    "cache_key": cache_key,
                    "id": raw_event.id,
                    "status": "SUCCESS",
                },
            )
        await session.commit()


async def run_file_worker(
    path: str,
    source_name: str,
    interval_seconds: int,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> None:
    file_path = Path(path)
    failures = 0
    while True:
        try:
            await process_file_once(str(file_path), source_name)
            failures = 0
        except Exception:
            failures += 1
            logger.exception(
                "File worker iteration failed",
                extra={
                    "source_name": source_name,
                    "path": str(file_path),
                    "attempt": failures,
                },
            )
            if failures > max_retries:
                raise
            delay = backoff_seconds * failures
            await asyncio.sleep(delay)
            continue
        await asyncio.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--interval", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(run_file_worker(args.path, args.source, args.interval))


if __name__ == "__main__":  # pragma: no cover
    main()
