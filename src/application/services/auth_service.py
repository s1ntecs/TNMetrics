from collections.abc import Callable

from src.application.security.jwt import create_access_token
from src.application.security.password import verify_password
from src.infrastructure.db.models import User
from src.infrastructure.db.uow import SqlAlchemyUnitOfWork
from src.settings import Settings


class AuthService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork], settings: Settings) -> None:
        self._uow_factory = uow_factory
        self._settings = settings

    async def authenticate(self, email: str, password: str) -> User | None:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if user is None:
                return None
            if not user.is_active:
                return None
            if not verify_password(password, user.hashed_password):
                return None
            return user

    def issue_token(self, user: User) -> str:
        return create_access_token(
            subject=str(user.id),
            secret_key=self._settings.secret_key,
            expires_minutes=self._settings.access_token_expire_minutes,
        )
