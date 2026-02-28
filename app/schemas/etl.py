from datetime import datetime
import json


from pydantic import BaseModel, ConfigDict, field_validator


class IngestionSourceCreate(BaseModel):
    name: str
    description: str | None = None


class IngestionSourceRead(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RawEventCreate(BaseModel):
    source_name: str
    payload: dict

    @field_validator("source_name")
    @classmethod
    def validate_source_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("source_name must not be empty")
        return cleaned

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("payload must be a dict")
        if not value:
            raise ValueError("payload must not be empty")
        return value


class ProcessedRecordCreate(BaseModel):
    id: int
    raw_event_id: int
    status: str
    result_payload: dict | None
    processed_at: datetime

    @field_validator("result_payload", mode="before")
    @classmethod
    def parse_result_payload(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except ValueError:
                return None
        return value
