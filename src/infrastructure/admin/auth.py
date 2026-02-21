from uuid import UUID

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.application.security.password import verify_password
from src.infrastructure.db.session import async_session_maker
from src.infrastructure.db.uow import SqlAlchemyUnitOfWork


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            return False

        async with SqlAlchemyUnitOfWork(async_session_maker) as uow:
            user = await uow.users.get_by_email(str(email))
            if user is None or not user.is_active or not user.is_superuser:
                return False
            if not verify_password(str(password), user.hashed_password):
                return False

            request.session.update({"admin_user_id": str(user.id)})
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("admin_user_id")
        if user_id is None:
            return False
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return False

        async with SqlAlchemyUnitOfWork(async_session_maker) as uow:
            user = await uow.users.get_by_id(user_uuid)
            if user is None:
                return False
            return bool(user.is_active and user.is_superuser)
