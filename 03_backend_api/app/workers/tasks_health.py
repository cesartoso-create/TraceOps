from app.workers.celery_app import celery_app


@celery_app.task(name="traceops.health.ping")
def ping() -> str:
    return "pong"

