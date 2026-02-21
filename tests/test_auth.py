"""Tests for the /api/token/ authentication endpoint."""

import os
import sys
from collections.abc import AsyncIterator
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

from src.infrastructure.db.models import User  # noqa: E402
from src.main_api import app  # noqa: E402
from src.presentation.api.deps import get_auth_service  # noqa: E402


class FakeAuthService:
    """Stub that simulates AuthService without touching the database."""

    def __init__(self) -> None:
        self.valid_user = User(
            id=uuid4(),
            email="user@example.com",
            hashed_password="hashed",
            is_superuser=False,
            is_active=True,
        )

    async def authenticate(self, email: str, password: str) -> User | None:
        if email == self.valid_user.email and password == "correct-password":
            return self.valid_user
        return None

    def issue_token(self, user: User) -> str:
        return f"fake-token-for-{user.id}"


@pytest.fixture()
async def auth_client() -> AsyncIterator[AsyncClient]:
    fake = FakeAuthService()

    def override() -> FakeAuthService:
        return fake

    app.dependency_overrides[get_auth_service] = override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


async def test_token_success(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/api/token/",
        json={"email": "user@example.com", "password": "correct-password"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_token_wrong_password(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/api/token/",
        json={"email": "user@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


async def test_token_unknown_email(auth_client: AsyncClient) -> None:
    resp = await auth_client.post(
        "/api/token/",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


async def test_token_missing_fields(auth_client: AsyncClient) -> None:
    resp = await auth_client.post("/api/token/", json={})
    assert resp.status_code == 422
