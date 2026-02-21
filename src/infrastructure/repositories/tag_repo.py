from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models import Tag


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Tag]:
        query = select(Tag).order_by(Tag.name.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_ids(self, tag_ids: list[UUID]) -> list[Tag]:
        if not tag_ids:
            return []
        query = select(Tag).where(Tag.id.in_(tag_ids))
        result = await self._session.execute(query)
        return list(result.scalars().all())
