import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

from src.infrastructure.celery.celery_app import celery_app
from src.infrastructure.db.models import Metric, MetricRecord
from src.infrastructure.db.session import async_session_maker
from src.settings import get_settings


@celery_app.task(name="src.infrastructure.celery.tasks.reporting.generate_fake_report")
def generate_fake_report() -> None:
    asyncio.run(_generate_fake_report())


async def _generate_fake_report() -> None:
    async with async_session_maker() as session:
        metrics_count = await session.scalar(select(func.count()).select_from(Metric))
        records_count = await session.scalar(select(func.count()).select_from(MetricRecord))

    settings = get_settings()
    reports_dir = Path(settings.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / "fake_report.txt"
    updated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    report_path.write_text(
        "\n".join(
            [
                f"total_metrics={metrics_count or 0}",
                f"total_records={records_count or 0}",
                f"updated_at={updated_at}",
            ]
        ),
        encoding="utf-8",
    )
