from collections.abc import Callable
from uuid import UUID

from src.application.schemas.metric import MetricCreate
from src.domain.exceptions import ValidationError
from src.infrastructure.db.models import Metric
from src.infrastructure.db.uow import SqlAlchemyUnitOfWork


class MetricService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def create_metric(self, user_id: UUID, data: MetricCreate) -> Metric:
        if not data.name.strip():
            raise ValidationError("Metric name must not be empty")

        async with self._uow_factory() as uow:
            return await uow.metrics.create(
                user_id=user_id, name=data.name.strip(), description=data.description
            )

    async def list_metrics(self, user_id: UUID) -> list[Metric]:
        async with self._uow_factory() as uow:
            return await uow.metrics.list_by_user(user_id)
