import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.repositories.events import SqlAlchemyEventRepository
from app.schemas.etl import IngestionSourceRead, ProcessedRecordRead, RawEventCreate
from app.services import etl as etl_services
from app.utils.cache import RedisCacheClient

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/ingest",
    response_model=ProcessedRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_event_endpoint(
    payload: RawEventCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ProcessedRecordRead:
    repository = SqlAlchemyEventRepository(session=session)
    cache_client = RedisCacheClient()
    try:
        _, processed = await etl_services.ingest_and_mark_success(
            repository=repository,
            source_name=payload.source_name,
            payload=payload.payload,
        )
        await session.commit()
        cache_key = f"processed_record:{processed.id}"
        cache_value = json.dumps(
            {
                "id": processed.id,
                "raw_event_id": processed.raw_event_id,
                "status": processed.status,
            },
        )
        await cache_client.set(cache_key, cache_value, ttl_seconds=3600)
        return ProcessedRecordRead.model_validate(processed, from_attributes=True)
    except Exception as exc:
        logger.exception("Error while ingesting event")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest event",
        ) from exc


@router.get(
    "/sources",
    response_model=list[IngestionSourceRead],
)
async def list_sources_endpoint(
    session: AsyncSession = Depends(get_db_session),
) -> list[IngestionSourceRead]:
    from sqlalchemy import select

    from app.models import IngestionSource

    result = await session.execute(select(IngestionSource))
    sources = result.scalars().all()
    return [IngestionSourceRead.model_validate(source) for source in sources]


@router.get(
    "/processed-records",
    response_model=list[ProcessedRecordRead],
)
async def list_processed_records_endpoint(
    session: AsyncSession = Depends(get_db_session),
) -> list[ProcessedRecordRead]:
    from sqlalchemy import select

    from app.models import ProcessedRecord

    result = await session.execute(select(ProcessedRecord))
    records = result.scalars().all()
    return [
        ProcessedRecordRead.model_validate(record, from_attributes=True)
        for record in records
    ]
