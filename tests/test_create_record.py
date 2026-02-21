from datetime import UTC, datetime
from uuid import uuid4

from tests.conftest import TestContext


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def test_create_metric_record_success(ctx: TestContext) -> None:
    timestamp = _now_iso()

    response = await ctx.client.post(
        f"/api/metrics/{ctx.owner_metric_id}/records/",
        json={"value": "123.45", "timestamp": timestamp, "tag_ids": [str(ctx.tag_id)]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["metric_id"] == str(ctx.owner_metric_id)
    assert body["value"] == "123.45"
    assert len(body["tags"]) == 1
    assert len(ctx.service.created) == 1


async def test_create_metric_record_forbidden_foreign_metric(ctx: TestContext) -> None:
    response = await ctx.client.post(
        f"/api/metrics/{ctx.foreign_metric_id}/records/",
        json={
            "value": "7.7",
            "timestamp": _now_iso(),
            "tag_ids": [],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Metric not found"


async def test_create_metric_record_without_tags(ctx: TestContext) -> None:
    timestamp = _now_iso()

    response = await ctx.client.post(
        f"/api/metrics/{ctx.owner_metric_id}/records/",
        json={"value": "50.0", "timestamp": timestamp, "tag_ids": []},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tags"] == []
    assert body["value"] == "50.0"


async def test_create_metric_record_invalid_tags(ctx: TestContext) -> None:
    timestamp = _now_iso()
    nonexistent_tag_id = str(uuid4())

    response = await ctx.client.post(
        f"/api/metrics/{ctx.owner_metric_id}/records/",
        json={"value": "10.0", "timestamp": timestamp, "tag_ids": [nonexistent_tag_id]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Some tags were not found"


async def test_create_metric_record_invalid_data(ctx: TestContext) -> None:
    response = await ctx.client.post(
        f"/api/metrics/{ctx.owner_metric_id}/records/",
        json={"value": "not-a-number", "timestamp": "invalid-date", "tag_ids": []},
    )

    assert response.status_code == 422


async def test_create_metric_record_no_auth(unauth_client) -> None:  # type: ignore[no-untyped-def]
    metric_id = uuid4()

    response = await unauth_client.post(
        f"/api/metrics/{metric_id}/records/",
        json={
            "value": "1.0",
            "timestamp": _now_iso(),
            "tag_ids": [],
        },
    )

    assert response.status_code == 401
