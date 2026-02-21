from collections.abc import Callable
from uuid import UUID

from fastapi.encoders import jsonable_encoder

from src.application.schemas.record import RecordCreate, RecordRead
from src.domain.exceptions import NotFoundError, ValidationError
from src.infrastructure.db.uow import SqlAlchemyUnitOfWork
from src.infrastructure.redis.client import CacheClient
from src.settings import Settings


class RecordService:
    def __init__(
        self,
        uow_factory: Callable[[], SqlAlchemyUnitOfWork],
        cache_client: CacheClient,
        settings: Settings,
    ) -> None:
        self._uow_factory = uow_factory
        self._cache_client = cache_client
        self._settings = settings

    async def list_records(
        self,
        user_id: UUID,
        metric_id: UUID,
        limit: int,
        offset: int,
    ) -> list[RecordRead]:
        async with self._uow_factory() as uow:
            metric = await uow.metrics.get_owned_metric(metric_id=metric_id, user_id=user_id)
            if metric is None:
                raise NotFoundError("Metric not found")

            version = await self._cache_client.get_version(user_id=user_id, metric_id=metric_id)
            cache_key = f"records:{user_id}:{metric_id}:v{version}:limit{limit}:offset{offset}"
            cached = await self._cache_client.get_json(cache_key)
            if cached is not None:
                return [RecordRead.model_validate(item) for item in cached]

            records = await uow.records.list_by_metric(
                metric_id=metric_id, limit=limit, offset=offset
            )
            payload = [RecordRead.model_validate(item) for item in records]

        await self._cache_client.set_json(
            cache_key,
            jsonable_encoder([item.model_dump(mode="json") for item in payload]),
            ttl_seconds=self._settings.cache_ttl_seconds,
        )
        return payload

    async def get_record(self, user_id: UUID, metric_id: UUID, record_id: UUID) -> RecordRead:
        async with self._uow_factory() as uow:
            metric = await uow.metrics.get_owned_metric(metric_id=metric_id, user_id=user_id)
            if metric is None:
                raise NotFoundError("Metric not found")

            record = await uow.records.get_by_id(record_id)
            if record is None or record.metric_id != metric.id:
                raise NotFoundError("Record not found")

            return RecordRead.model_validate(record)

    async def create_record(self, user_id: UUID, metric_id: UUID, data: RecordCreate) -> RecordRead:
        async with self._uow_factory() as uow:
            metric = await uow.metrics.get_owned_metric(metric_id=metric_id, user_id=user_id)
            if metric is None:
                raise NotFoundError("Metric not found")

            tags = await uow.tags.get_by_ids(data.tag_ids)
            if len(tags) != len(set(data.tag_ids)):
                raise ValidationError("Some tags were not found")

            record = await uow.records.create(
                metric_id=metric.id, timestamp=data.timestamp, value=data.value
            )
            record.tags.extend(tags)
            await uow.session.flush()
            await uow.session.refresh(record, attribute_names=["tags"])

            response = RecordRead.model_validate(record)

        await self._cache_client.bump_version(user_id=user_id, metric_id=metric_id)
        return response
