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
        "dataset_path": str(base),
        "files_total": len(files),
        "files_processed": len(files),
        "rows_read": 0,
        "rows_valid": 0,
        "rows_invalid": 0,
        "rows_written_postgres": 0,
        "rows_written_redis": 0,
        "read_errors": 0,
        "write_errors": 0,
        "start_time": time.time(),
        "end_time": None,
        "duration_seconds": None,
    }
    async with AsyncSessionLocal() as session:
        repository = SqlAlchemyEventRepository(session=session)
        pg_sink = PostgresSink(repository)
        redis_sink = RedisSink()
        for path in files:
            try:
                connector: Any
                if path.suffix.lower() == ".csv":
                    connector = CsvFileIngestionConnector(str(path))
                else:
                    connector = JsonFileIngestionConnector(str(path))
                batch = await connector.fetch_batch()
                metrics["files_processed"] += 1
            except Exception:
                metrics["read_errors"] += 1
                continue
            for row in batch:
                metrics["rows_read"] += 1
                if not isinstance(row, dict) or not row:
                    metrics["rows_invalid"] += 1
                    continue
                metrics["rows_valid"] += 1
                try:
                    raw_event = await repository.ingest_event(
                        source_name=source_name, payload=row
                    )
                    record = {
                        "raw_event": raw_event,
                        "status": "SUCCESS",
                        "payload": row,
                    }
                    await pg_sink.write(record)
                    metrics["rows_written_postgres"] += 1
                    cache_key = f"kaggle:processed:{raw_event.id}"
                    await redis_sink.write(
                        {
                            "cache_key": cache_key,
                            "id": raw_event.id,
                            "status": "SUCCESS",
                        },
                    )
                    metrics["rows_written_redis"] += 1
                except Exception:
                    metrics["write_errors"] += 1
        await session.commit()
    metrics["end_time"] = time.time()
    metrics["duration_seconds"] = metrics["end_time"] - metrics["start_time"]
    return metrics


def write_validation_report(report_dir: str, metrics: dict[str, Any]) -> Path:
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    json_path = report_path / "global_econ_validation_report.json"
    json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    md_path = report_path / "global_econ_validation_report.md"
    lines = [
        "# Global Economic Indicators Worker Validation",
        "",
        f"- Dataset path: {metrics['dataset_path']}",
        f"- Files total: {metrics['files_total']}",
        f"- Files processed: {metrics['files_processed']}",
        f"- Rows read: {metrics['rows_read']}",
        f"- Rows valid: {metrics['rows_valid']}",
        f"- Rows invalid: {metrics['rows_invalid']}",
        f"- Rows written Postgres: {metrics['rows_written_postgres']}",
        f"- Rows written Redis: {metrics['rows_written_redis']}",
        f"- Read errors: {metrics['read_errors']}",
        f"- Write errors: {metrics['write_errors']}",
        f"- Duration seconds: {metrics['duration_seconds']}",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path


async def run_global_econ_validation(
    source_name: str = "kaggle-global-economic-indicators",
    report_dir: str = "reports",
) -> dict[str, Any]:
    dataset_path = download_global_economic_dataset()
    metrics = await validate_dataset_path(dataset_path, source_name)
    write_validation_report(report_dir, metrics)
    return metrics


def main() -> None:
    asyncio.run(run_global_econ_validation())


if __name__ == "__main__":  # pragma: no cover
    main()
