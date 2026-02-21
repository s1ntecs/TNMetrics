from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models import Metric


class MetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: UUID, name: str, description: str | None) -> Metric:
        metric = Metric(user_id=user_id, name=name, description=description)
        self._session.add(metric)
        await self._session.flush()
        return metric

    async def list_by_user(self, user_id: UUID) -> list[Metric]:
        query = select(Metric).where(Metric.user_id == user_id).order_by(Metric.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_owned_metric(self, metric_id: UUID, user_id: UUID) -> Metric | None:
        query = select(Metric).where(Metric.id == metric_id, Metric.user_id == user_id)
        result = await self._session.scalar(query)
        return result  # type: ignore[return-value]
