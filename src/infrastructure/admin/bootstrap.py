from src.application.security.password import hash_password
from src.infrastructure.db.session import async_session_maker
from src.infrastructure.db.uow import SqlAlchemyUnitOfWork
from src.settings import get_settings


async def ensure_superuser() -> None:
    settings = get_settings()

    async with SqlAlchemyUnitOfWork(async_session_maker) as uow:
        existing = await uow.users.get_by_email(settings.superuser_email)
        if existing is not None:
            return

        await uow.users.create(
            email=settings.superuser_email,
            hashed_password=hash_password(settings.superuser_password),
            is_superuser=True,
        )
