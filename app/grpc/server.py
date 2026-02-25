import asyncio
import json

import grpc

from app.db import AsyncSessionLocal
from app.repositories import SqlAlchemyEventRepository
from app.services import etl as etl_services

from . import etlpay_pb2, etlpay_pb2_grpc


class EtlServiceServicer(etlpay_pb2_grpc.EtlServiceServicer):
    async def Ingest(self, request, context):
        async with AsyncSessionLocal() as session:
            repository = SqlAlchemyEventRepository(session=session)
            payload = json.loads(request.payload_json or "{}")
            raw_event = await etl_services.ingest_event(
                repository=repository,
                source_name=request.source_name,
                payload=payload,
            )
            processed = await etl_services.mark_processed(
                repository=repository,
                raw_event=raw_event,
                status="SUCCESS",
                result_payload=payload,
            )
            await session.commit()
            return etlpay_pb2.IngestResponse(id=processed.id, status=processed.status)


async def serve(host: str = "0.0.0.0", port: int = 50051) -> None:
    server = grpc.aio.server()
    etlpay_pb2_grpc.add_EtlServiceServicer_to_server(EtlServiceServicer(), server)
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(serve())
