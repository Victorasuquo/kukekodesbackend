"""Durable background tasks for reminders and provider delivery."""

from app.task_queue import celery_app
from app.db.postgres import get_db_session
from app.models.outbox import OutboxEvent
from datetime import datetime
from sqlalchemy import select
from sqlalchemy import func


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
        from app.models.user import User
        from app.services.email_service import email_service
        for event in events:
            event.attempts += 1
            try:
                user = db.query(User).filter(User.id == event.payload.get("user_id")).first()
                recipient = (user.contact_email or user.email) if user else event.payload.get("email")
                if event.event_type == "welcome_email" and recipient:
                    sent = email_service.send_email(recipient, "Welcome to KukeKodes", "<p>Welcome to KukeKodes. Your learning journey starts now.</p>")
                elif event.event_type == "weekly_progress_reminder" and recipient:
                    sent = email_service.send_email(recipient, "Your weekly KukeKodes progress", "<p>Keep your learning streak going this week.</p>")
                else:
                    sent = True
                if sent:
                    event.status = "processed"; event.processed_at = datetime.utcnow(); event.last_error = None
                else:
                    event.status = "pending" if event.attempts < 3 else "dead_letter"; event.last_error = "Provider did not accept the message"
            except Exception as exc:
                event.status = "pending" if event.attempts < 3 else "dead_letter"; event.last_error = str(exc)
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

@celery_app.task(name="kukekodes.match-accountability-learners")
def match_accountability_learners() -> int:
    """Create full groups, or seven-day groups with at least three learners."""
    from app.models.accountability import AccountabilityCluster, AccountabilityClusterMembership, AccountabilityMatchQueue, QueueStatus
    from app.api.v1.accountability import unique_name
    db = get_db_session()
    try:
        queue = db.execute(select(AccountabilityMatchQueue).where(AccountabilityMatchQueue.status == QueueStatus.WAITING).order_by(AccountabilityMatchQueue.queued_at).with_for_update(skip_locked=True)).scalars().all()
        if len(queue) < 15:
            cutoff = datetime.utcnow().timestamp() - 7 * 86400
            if len(queue) < 3 or queue[0].queued_at.timestamp() > cutoff: return 0
        selected = queue[:15]
        cluster = AccountabilityCluster(name=unique_name(db)); db.add(cluster); db.flush()
        for item in selected:
            db.add(AccountabilityClusterMembership(cluster_id=cluster.id,user_id=item.user_id)); item.status=QueueStatus.MATCHED; item.matched_cluster_id=cluster.id
        db.commit(); return len(selected)
    finally:
        db.close()
