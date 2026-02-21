import os
import sys
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("SUPERUSER_EMAIL", "admin@example.com")
os.environ.setdefault("SUPERUSER_PASSWORD", "admin12345")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.application.schemas.record import RecordRead  # noqa: E402
from src.application.schemas.tag import TagRead  # noqa: E402
from src.domain.exceptions import NotFoundError, ValidationError  # noqa: E402
from src.infrastructure.db.models import User  # noqa: E402
from src.main_api import app  # noqa: E402
from src.presentation.api.deps import get_current_user, get_record_service  # noqa: E402


class FakeRecordService:
    def __init__(self, owner_metric_id: UUID, allowed_tag_id: UUID) -> None:
        self.owner_metric_id = owner_metric_id
        self.allowed_tag_id = allowed_tag_id
        self.created: list[RecordRead] = []

    async def create_record(  # type: ignore[no-untyped-def]
        self,
        user_id: UUID,
        metric_id: UUID,
        data,
    ):
        _ = user_id
        if metric_id != self.owner_metric_id:
            raise NotFoundError("Metric not found")

        for tag_id in data.tag_ids:
            if tag_id != self.allowed_tag_id:
                raise ValidationError("Some tags were not found")

        tags = []
        if data.tag_ids:
            tags = [TagRead(id=self.allowed_tag_id, name="important", created_at=datetime.now(UTC))]

        result = RecordRead(
            id=uuid4(),
            metric_id=metric_id,
            value=data.value,
            timestamp=data.timestamp,
            created_at=datetime.now(UTC),
            tags=tags,
        )
        self.created.append(result)
        return result


@dataclass
class TestContext:
    client: AsyncClient
    service: FakeRecordService
    user: User
    owner_metric_id: UUID
    foreign_metric_id: UUID
    tag_id: UUID


@pytest.fixture()
async def ctx() -> AsyncIterator[TestContext]:
    user = User(
        id=uuid4(),
        email="owner@example.com",
        hashed_password="hashed",
        is_superuser=False,
        is_active=True,
    )
    owner_metric_id = uuid4()
    foreign_metric_id = uuid4()
    tag_id = uuid4()
    fake_service = FakeRecordService(owner_metric_id=owner_metric_id, allowed_tag_id=tag_id)

    async def override_get_current_user() -> User:
        return user

    def override_get_record_service() -> FakeRecordService:
        return fake_service

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_record_service] = override_get_record_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield TestContext(
            client=async_client,
            service=fake_service,
            user=user,
            owner_metric_id=owner_metric_id,
            foreign_metric_id=foreign_metric_id,
            tag_id=tag_id,
        )

    app.dependency_overrides.clear()


@pytest.fixture()
async def unauth_client() -> AsyncIterator[AsyncClient]:
    """Client without auth overrides — requests should get 401."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
    app.dependency_overrides.clear()
