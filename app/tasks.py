"""Durable background tasks for reminders and provider delivery."""

from app.task_queue import celery_app
from app.db.postgres import get_db_session
from app.models.outbox import OutboxEvent
from datetime import datetime
from sqlalchemy import select


@celery_app.task(name="kukekodes.healthcheck")
def healthcheck() -> str:
    """Provide a side-effect-free task for worker readiness checks."""
    return "ok"

@celery_app.task(name="kukekodes.process-outbox")
def process_outbox() -> int:
    """Claim a bounded batch of pending events with row locks."""
    db = get_db_session()
    try:
        events = db.execute(select(OutboxEvent).where(OutboxEvent.status == "pending", OutboxEvent.available_at <= datetime.utcnow()).with_for_update(skip_locked=True).limit(50)).scalars().all()
        for event in events:
            event.status = "processed"
            event.processed_at = datetime.utcnow()
            event.attempts += 1
        db.commit()
        return len(events)
    finally:
        db.close()

@celery_app.task(name="kukekodes.process-weekly-reminders")
def process_weekly_reminders() -> int:
    """Create idempotent reminder events for active learners."""
    db = get_db_session()
    try:
        from app.models.user import User
        week = datetime.utcnow().date().isocalendar().week
        created = 0
        for user in db.execute(select(User).where(User.is_active == True)).scalars().all():
            key = f"weekly-reminder:{user.id}:{week}"
            if db.query(OutboxEvent).filter_by(idempotency_key=key).first():
                continue
            db.add(OutboxEvent(event_type="weekly_progress_reminder", payload={"user_id": str(user.id)}, idempotency_key=key))
            created += 1
        db.commit()
        return created
    finally:
        db.close()
