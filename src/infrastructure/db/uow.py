from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.repositories.metric_repo import MetricRepository
from src.infrastructure.repositories.record_repo import RecordRepository
from src.infrastructure.repositories.tag_repo import TagRepository
from src.infrastructure.repositories.user_repo import UserRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession
        self.users: UserRepository
        self.metrics: MetricRepository
        self.records: RecordRepository
        self.tags: TagRepository

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.users = UserRepository(self.session)
        self.metrics = MetricRepository(self.session)
        self.records = RecordRepository(self.session)
        self.tags = TagRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if exc:
            await self.rollback()
        else:
            await self.commit()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
