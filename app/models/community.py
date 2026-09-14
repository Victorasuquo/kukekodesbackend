"""Relational references for moderated Mongo-backed community content."""
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.db.postgres import Base

class CommunityReport(Base):
    __tablename__ = "community_reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_id = Column(String(128), nullable=False, index=True)
    reason = Column(String(500), nullable=False)
    status = Column(String(32), nullable=False, default="open", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class CommunityBlock(Base):
    __tablename__ = "community_blocks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blocked_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (Index("uq_community_block", "blocker_id", "blocked_user_id", unique=True),)
