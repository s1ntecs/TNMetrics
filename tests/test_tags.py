"""Tests for /api/tags/ endpoint."""

import os
import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("SUPERUSER_EMAIL", "admin@example.com")
os.environ.setdefault("SUPERUSER_PASSWORD", "admin12345")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.infrastructure.db.models import Tag, User  # noqa: E402
from src.main_api import app  # noqa: E402
from src.presentation.api.deps import get_current_user, get_tag_service  # noqa: E402


class FakeTagService:
    def __init__(self, tags: list[Tag]) -> None:
        self._tags = tags

    async def list_tags(self) -> list[Tag]:
        return self._tags


@pytest.fixture()
async def tag_client_with_data() -> AsyncIterator[AsyncClient]:
    user = User(
        id=uuid4(),
        email="tag-test@example.com",
        hashed_password="h",
        is_superuser=False,
        is_active=True,
    )
    tags = [
        Tag(id=uuid4(), name="important", created_at=datetime.now(UTC)),
        Tag(id=uuid4(), name="urgent", created_at=datetime.now(UTC)),
    ]
    fake = FakeTagService(tags)

    async def override_user() -> User:
        return user

    def override_service() -> FakeTagService:
        return fake

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_tag_service] = override_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
async def tag_client_empty() -> AsyncIterator[AsyncClient]:
    user = User(
        id=uuid4(),
        email="tag-empty@example.com",
        hashed_password="h",
        is_superuser=False,
        is_active=True,
    )

    async def override_user() -> User:
        return user

    def override_service() -> FakeTagService:
        return FakeTagService([])

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_tag_service] = override_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


async def test_list_tags_returns_data(tag_client_with_data: AsyncClient) -> None:
    resp = await tag_client_with_data.get("/api/tags/")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    names = {t["name"] for t in body}
    assert names == {"important", "urgent"}


async def test_list_tags_empty(tag_client_empty: AsyncClient) -> None:
    resp = await tag_client_empty.get("/api/tags/")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_tags_no_auth() -> None:
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        resp = await c.get("/api/tags/")
    assert resp.status_code == 401
    app.dependency_overrides.clear()
