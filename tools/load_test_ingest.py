import asyncio
import time
from typing import Any

import httpx


async def worker(client: httpx.AsyncClient, requests_per_worker: int) -> list[float]:
    latencies: list[float] = []
    for _ in range(requests_per_worker):
        payload: dict[str, Any] = {
            "source_name": "load-test",
            "payload": {"value": 1},
        }
        start = time.perf_counter()
        response = await client.post("/api/ingest", json=payload)
        end = time.perf_counter()
        response.raise_for_status()
        latencies.append(end - start)
    return latencies


async def run_load_test(
    base_url: str = "http://localhost:8000",
    concurrent_clients: int = 10,
    requests_per_client: int = 10,
) -> None:
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        tasks = [worker(client, requests_per_client) for _ in range(concurrent_clients)]
        all_latencies_lists = await asyncio.gather(*tasks)

    latencies = [item for sublist in all_latencies_lists for item in sublist]
    total_requests = len(latencies)
    total_time = sum(latencies)
    avg_latency = total_time / total_requests if total_requests else 0.0
    max_latency = max(latencies) if latencies else 0.0

    print(f"Total requests: {total_requests}")
    print(f"Average latency: {avg_latency * 1000:.2f} ms")
    print(f"Max latency: {max_latency * 1000:.2f} ms")


def main() -> None:
    asyncio.run(run_load_test())


if __name__ == "__main__":
    main()
