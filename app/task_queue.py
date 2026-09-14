"""Celery application used by the private worker and scheduler services."""

from celery import Celery

from app.config import settings


if not settings.REDIS_URL:
    raise RuntimeError("REDIS_URL is required for background job processing")


celery_app = Celery(
    "kukekodes",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    enable_utc=True,
    result_expires=3600,
    task_acks_late=True,
    task_ignore_result=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    timezone="UTC",
    worker_prefetch_multiplier=1,
    beat_schedule={
        "weekly-progress-reminders": {"task": "kukekodes.process-weekly-reminders", "schedule": 86400.0},
        "process-outbox": {"task": "kukekodes.process-outbox", "schedule": 30.0},
    },
)
