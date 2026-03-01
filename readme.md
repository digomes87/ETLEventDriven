Here's the English translation:

# EtlPay – Event-Driven ETL Pipeline

Event-driven ETL project using:

- FastAPI (HTTP API)
- PostgreSQL (persistence)
- Redis (cache)
- RabbitMQ (message queue)
- gRPC (ingestion service)
- Asynchronous workers (file and queue)

This README focuses on:

- Main development commands
- 5–10 minute demo script
- Expected results for each step

---

## 1. Prerequisites

- Python 3.11+
- Virtual environment created and activated (`.venv`)
- Dependencies installed (e.g., `pip install -r requirements.txt` or equivalent command used in the project)
- External services (for complete demo):
  - PostgreSQL accessible according to `Settings` variables (see `app/config/settings.py`)
  - Redis accessible
  - RabbitMQ accessible

---

## gRPC Code Generation

If you need to modify the `.proto` file in `protos/etlpay.proto`, **do not** use the `protoc` command directly, as it may generate code incompatible with recent versions of `grpcio`.

Use the utility script:

```bash
python tools/generate_proto.py
```

This ensures correct generation and applies automatic compatibility fixes.

---

## 2. Architecture

The project follows a layered architecture strongly influenced by **Ports & Adapters (Hexagonal)** applied to an event-driven ETL domain.

Overview:

- **Application/Services Core**  
  - `app/services/etl.py` orchestrates event ingestion and processing (`ingest_event`, `mark_processed`, `ingest_and_mark_success`).
  - Depends on interfaces (`EventRepository`, `CacheClient`, `MessageQueueClient`), not infrastructure details.

- **Ports (domain interfaces)**  
  - Defined in `app/interfaces/events.py`:
    - `EventRepository`
    - `CacheClient`
    - `MessageQueueClient`
    - `SessionFactory`
  - Serve as contracts for repositories, cache, and queue.

- **Input Adapters (driving adapters)**  
  - HTTP API: `app/routes/api.py` (FastAPI).
  - gRPC: `app/grpc/server.py`.
  - Workers: `app/workers/file_worker.py` and `app/workers/queue_worker.py`.
  - Batch validation: `app/validation/global_econ.py`.
  - These components expose the domain to the "outside world".

- **Output Adapters (driven adapters)**  
  - Persistence:
    - `app/repositories/events.py` – `SqlAlchemyEventRepository` (Postgres via SQLAlchemy).
    - `app/sinks/postgres.py` – writes processed records.
  - Cache:
    - `app/sinks/redis.py` and `app/utils/cache.py` – Redis read/write operations.
  - Messaging:
    - `app/utils/messaging.py` – `RabbitMQClient` for publishing/consuming messages.
  - Input data connectors:
    - `app/connectors/*.py` – file reading, CSV, etc.

During presentation, you can summarize it as:

> "We use a layered architecture in the Ports & Adapters (Hexagonal) style: business rules are in typed services and repositories, while HTTP API, gRPC, workers, database, Redis, and RabbitMQ are just pluggable adapters around the event-driven ETL domain."

---

## 3. Tests, Coverage, and Load Testing

### Running Tests

```bash
source .venv/bin/activate
pytest --maxfail=1
```

**Expected result**:

- Output similar to:

  ```text
  70 passed in 0.23s
  ```

### Running Tests with Coverage

```bash
source .venv/bin/activate
pytest --cov=app --cov-report=term-missing
```

**Expected result**:

- **100%** coverage in the `app` package, for example:

  ```text
  TOTAL                             668      0   100%
  ```

### Running a Simple HTTP Load Test

With the API running at `http://localhost:8000`, you can run a simple load test on the `/api/ingest` endpoint:

```bash
source .venv/bin/activate
python tools/load_test_ingest.py
```

Default parameters:

- 10 concurrent clients
- 10 requests per client (100 total requests)

Expected output (example):

```text
Total requests: 100
Average latency: 5.20 ms
Max latency: 12.34 ms
```

Use this to mention performance numbers in your presentation.

---

## 4. Database Initialization

Before running the API, gRPC server, or workers, run the database initialization:

```bash
source .venv/bin/activate
python -m app.db.migrate
```

**Expected result**:

- Initialization logs, for example:

  ```text
  [INFO] __main__ - Running database initialization
  [INFO] __main__ - Database initialization completed
  ```

---

## 5. Starting the HTTP API (FastAPI)

```bash
source .venv/bin/activate
python -m app.main
```

**Expected result**:

- Uvicorn running at `http://0.0.0.0:8000`:

  ```text
  INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
  INFO:     Application startup complete.
  ```

### View in Browser

- Open `http://localhost:8000/docs` to see interactive documentation (Swagger).

Main endpoints:

- `POST /api/ingest` – ingests a raw event and creates a processed record.
- `GET /api/sources` – lists registered ingestion sources.
- `GET /api/processed-records` – lists processed records written to the database.

### Quick Test via Swagger

1. In `/api/ingest`, click **Try it out**.
2. Send a body like:

   ```json
   {
     "source_name": "manual-demo",
     "payload": { "value": 123 }
   }
   ```

3. **Expected result**:
   - HTTP `201 Created`
   - Response body with fields like:

     ```json
     {
       "id": 1,
       "raw_event_id": 1,
       "status": "SUCCESS",
       "result_payload": { "value": 123 },
       "processed_at": "..."
     }
     ```

4. In `/api/sources`, execute the `GET`.

   - **Expected result**: list containing at least one source named `"manual-demo"`.

---

## 6. Starting the gRPC Server and Calling `Ingest`

### Start the gRPC Server

In another terminal:

```bash
source .venv/bin/activate
python -m app.grpc.server
```

**Expected result**:

- gRPC server running on `localhost:50051` without errors.

### Make an Example gRPC Call

In another terminal:

```bash
source .venv/bin/activate
python - << 'PY'
import grpc
from app.grpc import etlpay_pb2, etlpay_pb2_grpc

channel = grpc.insecure_channel("localhost:50051")
stub = etlpay_pb2_grpc.EtlServiceStub(channel)

request = etlpay_pb2.IngestRequest(
    source_name="grpc-demo",
    payload_json='{"value": 999}',
)

response = stub.Ingest(request)
print({"id": response.id, "status": response.status})
PY
```

**Expected result**:

- Output similar to:

  ```text
  {'id': 7, 'status': 'SUCCESS'}
  ```

- If you call `GET /api/sources` in the API, you should see the source `"grpc-demo"` listed.

---

## 7. Starting the File Worker

### Create an Events File

```bash
mkdir -p data
cat > data/events_file.json << 'JSON'
[
  { "value": 1 },
  { "value": 2 },
  { "value": 3 }
]
JSON
```

### Start the Worker

```bash
source .venv/bin/activate
python -m app.workers.file_worker \
  --path data/events_file.json \
  --source file-worker-demo \
  --interval 10
```

**Expected result**:

- Periodic processing logs (depending on log configuration).
- In the database, new `RawEvent` and `ProcessedRecord` associated with the `"file-worker-demo"` source.
- In `GET /api/sources`, the `"file-worker-demo"` source appears in the list.

### Update Events

- Edit `data/events_file.json` to add new objects.
- The worker will re-read the file every `interval` seconds and ingest the new events.

---

## 8. Starting the Queue Worker with RabbitMQ

> Requires RabbitMQ configured according to `Settings` (`rabbitmq_host`, `rabbitmq_port`, etc).

### Start the Queue Worker

```bash
source .venv/bin/activate
python -m app.workers.queue_worker \
  --queue etl-queue \
  --source queue-worker-demo \
  --interval 5 \
  --max-messages 10
```

### Publish Messages to the Queue via Python Code

```bash
source .venv/bin/activate
python - << 'PY'
import asyncio
from app.utils.messaging import RabbitMQClient

async def main() -> None:
  client = RabbitMQClient()
  for i in range(3):
      await client.publish("etl-queue", {"value": i + 1})

asyncio.run(main())
PY
```

**Expected result**:

- Worker consumes messages from the `etl-queue` and writes events/records to the database.
- In `GET /api/sources`, the `"queue-worker-demo"` source appears in the list.

> Note: The `etl-queue` must be bound to the `etlpay.events` exchange with routing key `"etl-queue"` in RabbitMQ.

---

## 9. Live Demo Script (5–10 minutes)

Suggested sequence for presentation:

1. **Quick Tests (optional, 1–2 min)**
   - Show:
     ```bash
     source .venv/bin/activate
     pytest --maxfail=1
     ```
   - Comment that there's 100% coverage (quickly show the coverage command).

2. **Start Database and API (2 min)**
   - In terminal:
     ```bash
     source .venv/bin/activate
     python -m app.db.migrate
     python -m app.main
     ```
   - Show Uvicorn logs in console.
   - Open `http://localhost:8000/docs` in browser.

3. **HTTP Demo: Ingestion and Listing (2–3 min)**
   - Use `/api/ingest` in Swagger to send an event (`source_name = "manual-demo"`).
   - Show 201 response and JSON with `status: "SUCCESS"`.
   - Call `/api/sources` and show `"manual-demo"` in the list.

4. **gRPC Demo (2–3 min)**
   - In another terminal, start the gRPC server:
     ```bash
     source .venv/bin/activate
     python -m app.grpc.server
     ```
   - In a third terminal, run the gRPC client script (section 5).
   - Show the output `{'id': ..., 'status': 'SUCCESS'}`.
   - Go back to `/api/sources` and show that the `"grpc-demo"` source appeared, proving the gRPC flow uses the same pipeline.

5. **File Worker Demo (2–3 min)**
   - Create `data/events_file.json` (if not already existing).
   - Start the file worker (section 6).
   - Show that after a few seconds, `GET /api/sources` now includes `"file-worker-demo"`.
   - Explain that events were read from the file, written to Postgres, and can be queried via API.

6. **(Optional) Queue Worker Demo with RabbitMQ (2–3 min)**
   - Start the queue worker.
   - Publish messages using `RabbitMQClient`.
   - Show in `/api/sources` that the `"queue-worker-demo"` source appears, and comment that the same repositories/sinks are used.

With this script, you demonstrate:

- HTTP API, gRPC, workers, and database integration.
- Uniform ingestion handling across multiple channels.
- Automated tests and high coverage ensuring safety for project evolution.