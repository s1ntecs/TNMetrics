from celery import Celery

from src.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "metrics",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.infrastructure.celery.tasks.reporting"],
)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "generate-fake-report": {
        "task": "src.infrastructure.celery.tasks.reporting.generate_fake_report",
        "schedule": 120.0,
    }
}
