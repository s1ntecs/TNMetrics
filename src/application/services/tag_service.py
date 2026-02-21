from collections.abc import Callable

from src.infrastructure.db.models import Tag
from src.infrastructure.db.uow import SqlAlchemyUnitOfWork


class TagService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def list_tags(self) -> list[Tag]:
        async with self._uow_factory() as uow:
            return await uow.tags.list_all()
