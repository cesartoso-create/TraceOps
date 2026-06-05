from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "traceops",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks_health",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Lima",
    enable_utc=True,
)

