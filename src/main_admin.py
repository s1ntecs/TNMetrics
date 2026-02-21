from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from src.infrastructure.admin.auth import AdminAuth
from src.infrastructure.admin.bootstrap import ensure_superuser
from src.infrastructure.admin.dashboard import DashboardAdmin
from src.infrastructure.admin.views import MetricAdmin, MetricRecordAdmin, TagAdmin, UserAdmin
from src.infrastructure.db.session import engine
from src.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await ensure_superuser()
    yield


app = FastAPI(title="Metrics Admin", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

admin = Admin(
    app=app, engine=engine, authentication_backend=AdminAuth(secret_key=settings.secret_key)
)
admin.add_view(DashboardAdmin)
admin.add_view(UserAdmin)
admin.add_view(MetricAdmin)
admin.add_view(MetricRecordAdmin)
admin.add_view(TagAdmin)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
