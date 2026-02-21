from pathlib import Path
from typing import Any

from sqladmin import BaseView, expose
from sqlalchemy import func, select
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.db.models import Metric, MetricRecord, Tag, User
from src.infrastructure.db.session import async_session_maker
from src.settings import get_settings


class DashboardAdmin(BaseView):
    name = "Dashboard"
    identity = "dashboard"
    icon = "fa-solid fa-gauge-high"

    @expose("/dashboard", methods=["GET"], identity="dashboard")
    async def index(self, request: Request) -> Response:
        stats = await self._load_stats()
        recent_records = await self._load_recent_records(limit=15)
        report = self._read_report_status()
        return await self.templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "title": "Dashboard",
                "subtitle": "Operational overview",
                "stats": stats,
                "recent_records": recent_records,
                "report": report,
            },
        )

    async def _load_stats(self) -> dict[str, int]:
        async with async_session_maker() as session:
            users_count = await session.scalar(select(func.count()).select_from(User))
            metrics_count = await session.scalar(select(func.count()).select_from(Metric))
            records_count = await session.scalar(select(func.count()).select_from(MetricRecord))
            tags_count = await session.scalar(select(func.count()).select_from(Tag))

        return {
            "users": int(users_count or 0),
            "metrics": int(metrics_count or 0),
            "records": int(records_count or 0),
            "tags": int(tags_count or 0),
        }

    async def _load_recent_records(self, limit: int) -> list[dict[str, Any]]:
        stmt = (
            select(
                MetricRecord.id,
                MetricRecord.value,
                MetricRecord.timestamp,
                MetricRecord.created_at,
                Metric.name.label("metric_name"),
                User.email.label("user_email"),
            )
            .join(Metric, MetricRecord.metric_id == Metric.id)
            .join(User, Metric.user_id == User.id)
            .order_by(MetricRecord.created_at.desc())
            .limit(limit)
        )

        async with async_session_maker() as session:
            rows = (await session.execute(stmt)).all()

        return [
            {
                "id": str(row.id),
                "metric_name": str(row.metric_name),
                "user_email": str(row.user_email),
                "value": str(row.value),
                "timestamp": row.timestamp,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def _read_report_status(self) -> dict[str, str]:
        settings = get_settings()
        report_path = Path(settings.reports_dir) / "fake_report.txt"
        if not report_path.exists():
            return {
                "exists": "no",
                "path": str(report_path),
                "total_metrics": "-",
                "total_records": "-",
                "updated_at": "-",
            }

        payload: dict[str, str] = {}
        for line in report_path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            payload[key.strip()] = value.strip()

        return {
            "exists": "yes",
            "path": str(report_path),
            "total_metrics": payload.get("total_metrics", "-"),
            "total_records": payload.get("total_records", "-"),
            "updated_at": payload.get("updated_at", "-"),
        }
