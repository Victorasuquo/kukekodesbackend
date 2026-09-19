"""Individual learner accountability clusters."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
from app.db.postgres import Base

class ClusterStatus(str, PyEnum):
    MATCHING = "matching"
    ACTIVE = "active"
    ARCHIVED = "archived"

class QueueStatus(str, PyEnum):
    WAITING = "waiting"
    MATCHED = "matched"
    LEFT = "left"

class AccountabilityCluster(Base):
    __tablename__ = "accountability_clusters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), unique=True, nullable=False)
    status = Column(Enum(ClusterStatus), default=ClusterStatus.ACTIVE, nullable=False, index=True)
    capacity = Column(Integer, default=15, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AccountabilityClusterMembership(Base):
    __tablename__ = "accountability_cluster_memberships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("accountability_clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    left_at = Column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("cluster_id", "user_id", name="uq_accountability_cluster_user"), Index("uq_accountability_active_user", "user_id", unique=True, postgresql_where=left_at.is_(None)))

class AccountabilityMatchQueue(Base):
    __tablename__ = "accountability_match_queue"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(Enum(QueueStatus), default=QueueStatus.WAITING, nullable=False, index=True)
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    matched_cluster_id = Column(UUID(as_uuid=True), ForeignKey("accountability_clusters.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
