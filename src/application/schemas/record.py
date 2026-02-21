from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.application.schemas.tag import TagRead


class RecordCreate(BaseModel):
    value: Decimal
    timestamp: datetime
    tag_ids: list[UUID] = Field(default_factory=list)


class RecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    metric_id: UUID
    value: Decimal
    timestamp: datetime
    created_at: datetime
    tags: list[TagRead] = Field(default_factory=list)
