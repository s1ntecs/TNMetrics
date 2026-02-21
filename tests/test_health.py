"""Tests for the /health endpoint."""

import os
import sys
from pathlib import Path

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

from src.main_api import app  # noqa: E402


async def test_healthcheck() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
