from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MetricCreate(BaseModel):
    name: str
    description: str | None = None


class MetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
