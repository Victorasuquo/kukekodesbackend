"""Infrastructure-level Celery tasks.

Product email, analytics, and reminder tasks should be added here only after
their idempotency keys and retry behavior are defined.
"""

from app.task_queue import celery_app


@celery_app.task(name="kukekodes.healthcheck")
def healthcheck() -> str:
    """Provide a side-effect-free task for worker readiness checks."""
    return "ok"
