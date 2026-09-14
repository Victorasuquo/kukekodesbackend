"""Verified provider webhooks."""
import hashlib
import hmac
import json
from fastapi import APIRouter, Header, HTTPException, Request, status
from app.config import settings
from app.db.postgres import get_db_session
from app.models.outbox import OutboxEvent

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])

@router.post("/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend_webhook(request: Request, x_webhook_signature: str | None = Header(default=None)):
    body = await request.body()
    secret = settings.RESEND_WEBHOOK_SECRET
    if not secret:
        raise HTTPException(status_code=503, detail="Webhook integration is not configured")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not x_webhook_signature or not hmac.compare_digest(expected, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc
    event_id = str(payload.get("id") or hashlib.sha256(body).hexdigest())
    db = get_db_session()
    try:
        if not db.query(OutboxEvent).filter_by(idempotency_key=f"resend:{event_id}").first():
            db.add(OutboxEvent(event_type=f"resend.{payload.get('type', 'event')}", payload=payload, idempotency_key=f"resend:{event_id}"))
            db.commit()
    finally:
        db.close()
    return {"accepted": True}
