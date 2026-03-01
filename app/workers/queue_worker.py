import argparse
import asyncio
import logging

from app.db import AsyncSessionLocal
from app.repositories import SqlAlchemyEventRepository
from app.services import etl as etl_services
from app.sinks import PostgresSink, RedisSink
from app.utils.messaging import RabbitMQClient


logger = logging.getLogger(__name__)


async def process_queue_once(
    queue_name: str,
    source_name: str,
    max_messages: int = 10,
) -> None:
    client = RabbitMQClient()
    messages = await client.pull_batch(queue_name, max_messages=max_messages)
    if not messages:
        return
    async with AsyncSessionLocal() as session:
        repository = SqlAlchemyEventRepository(session=session)
        pg_sink = PostgresSink(repository)
        redis_sink = RedisSink()
        for payload in messages:
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
            cache_key = f"queue:processed:{raw_event.id}"
            await redis_sink.write(
                {
                    "cache_key": cache_key,
                    "id": raw_event.id,
                    "status": "SUCCESS",
                },
            )
        await session.commit()


async def run_queue_worker(
    queue_name: str,
    source_name: str,
    interval_seconds: int,
    max_messages: int = 10,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> None:
    failures = 0
    while True:
        try:
            await process_queue_once(queue_name, source_name, max_messages=max_messages)
            failures = 0
        except Exception:
            failures += 1
            logger.exception(
                "Queue worker iteration failed",
                extra={
                    "queue_name": queue_name,
                    "source_name": source_name,
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
    parser.add_argument("--queue", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--max-messages", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(
        run_queue_worker(
            queue_name=args.queue,
            source_name=args.source,
            interval_seconds=args.interval,
            max_messages=args.max_messages,
        ),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
