"""Tests for /api/metrics/ endpoints."""

import os
import sys
from collections.abc import AsyncIterator
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
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("SUPERUSER_EMAIL", "admin@example.com")
os.environ.setdefault("SUPERUSER_PASSWORD", "admin12345")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.application.schemas.metric import MetricCreate  # noqa: E402
from src.domain.exceptions import ValidationError  # noqa: E402
from src.infrastructure.db.models import Metric, User  # noqa: E402
from src.main_api import app  # noqa: E402
from src.presentation.api.deps import get_current_user, get_metric_service  # noqa: E402


class FakeMetricService:
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        self.metrics: list[Metric] = []

    async def create_metric(self, user_id: UUID, data: MetricCreate) -> Metric:
        if not data.name.strip():
            raise ValidationError("Metric name must not be empty")
        metric = Metric(
            id=uuid4(),
            user_id=user_id,
            name=data.name.strip(),
            description=data.description,
            created_at=datetime.now(UTC),
        )
        self.metrics.append(metric)
        return metric

    async def list_metrics(self, user_id: UUID) -> list[Metric]:
        return [m for m in self.metrics if m.user_id == user_id]


@pytest.fixture()
async def metric_client() -> AsyncIterator[AsyncClient]:
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        is_superuser=False,
        is_active=True,
    )
    fake_service = FakeMetricService(user_id=user.id)

    async def override_user() -> User:
        return user

    def override_service() -> FakeMetricService:
        return fake_service

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_metric_service] = override_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


async def test_create_metric_success(metric_client: AsyncClient) -> None:
    resp = await metric_client.post(
        "/api/metrics/",
        json={"name": "CPU Usage", "description": "Server CPU metric"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "CPU Usage"
    assert body["description"] == "Server CPU metric"
    assert "id" in body
    assert "created_at" in body


async def test_create_metric_without_description(metric_client: AsyncClient) -> None:
    resp = await metric_client.post(
        "/api/metrics/",
        json={"name": "Memory"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Memory"
    assert body["description"] is None


async def test_create_metric_empty_name(metric_client: AsyncClient) -> None:
    resp = await metric_client.post(
        "/api/metrics/",
        json={"name": "   "},
    )
    assert resp.status_code == 400


async def test_list_metrics_empty(metric_client: AsyncClient) -> None:
    resp = await metric_client.get("/api/metrics/")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_metrics_after_create(metric_client: AsyncClient) -> None:
    await metric_client.post("/api/metrics/", json={"name": "Metric A"})
    await metric_client.post("/api/metrics/", json={"name": "Metric B"})

    resp = await metric_client.get("/api/metrics/")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    names = {m["name"] for m in body}
    assert names == {"Metric A", "Metric B"}


async def test_create_metric_no_auth() -> None:
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        resp = await c.post("/api/metrics/", json={"name": "X"})
    assert resp.status_code == 401
    app.dependency_overrides.clear()
