from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.application.security.jwt import JWTError, decode_access_token
from src.application.services.auth_service import AuthService
from src.application.services.metric_service import MetricService
from src.application.services.record_service import RecordService
from src.application.services.tag_service import TagService
from src.infrastructure.db.models import User
from src.infrastructure.db.session import async_session_maker
from src.infrastructure.db.uow import SqlAlchemyUnitOfWork
from src.infrastructure.redis.client import get_cache_client
from src.settings import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token/")


def get_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(async_session_maker)


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(uow_factory=get_uow, settings=settings)


def get_metric_service() -> MetricService:
    return MetricService(uow_factory=get_uow)


def get_tag_service() -> TagService:
    return TagService(uow_factory=get_uow)


def get_record_service(settings: Settings = Depends(get_settings)) -> RecordService:
    return RecordService(
        uow_factory=get_uow,
        cache_client=get_cache_client(),
        settings=settings,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token, settings.secret_key)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_error
        user_id = UUID(subject)
    except (JWTError, ValueError) as exc:
        raise credentials_error from exc

    async with get_uow() as uow:
        user = await uow.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise credentials_error
        return user
