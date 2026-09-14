"""Durable integration events for email and external providers."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(120), nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (Index("idx_outbox_ready", "status", "available_at"),)
