from datetime import datetime
import json


from pydantic import BaseModel, ConfigDict, field_validator

class IngestionSourceCreate(BaseModel):