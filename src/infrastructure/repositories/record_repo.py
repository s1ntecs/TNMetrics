from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.db.models import MetricRecord


class RecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_metric(self, metric_id: UUID, limit: int, offset: int) -> list[MetricRecord]:
        query = (
            select(MetricRecord)
            .where(MetricRecord.metric_id == metric_id)
            .options(selectinload(MetricRecord.tags))
            .order_by(MetricRecord.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, record_id: UUID) -> MetricRecord | None:
        query = (
            select(MetricRecord)
            .where(MetricRecord.id == record_id)
            .options(selectinload(MetricRecord.tags), selectinload(MetricRecord.metric))
        )
        result = await self._session.scalar(query)
        return result  # type: ignore[return-value]

    async def create(self, metric_id: UUID, timestamp: datetime, value: Decimal) -> MetricRecord:
        record = MetricRecord(metric_id=metric_id, timestamp=timestamp, value=value)
        self._session.add(record)
        return record
