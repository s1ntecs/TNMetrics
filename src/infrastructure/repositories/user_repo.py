from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self._session.scalar(query)
        return result  # type: ignore[return-value]

    async def get_by_id(self, user_id: UUID) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self._session.scalar(query)
        return result  # type: ignore[return-value]

    async def create(self, email: str, hashed_password: str, is_superuser: bool = False) -> User:
        user = User(
            email=email, hashed_password=hashed_password, is_superuser=is_superuser, is_active=True
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def count_all(self) -> int:
        query = select(func.count()).select_from(User)
        result = await self._session.execute(query)
        return int(result.scalar_one())
