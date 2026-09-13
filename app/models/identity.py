"""Identity, credentials, sessions, recovery, and consent models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.postgres import Base


class Credential(Base):
    """Password credential for a user."""

    __tablename__ = "credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    hash_version = Column(String(32), default="bcrypt-12", nullable=False)
    credential_version = Column(Integer, default=1, nullable=False)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="credential")


class SessionAudience(str, PyEnum):
    LEARNER = "learner"
    ADMIN = "admin"


class RefreshSession(Base):
    """Server-side refresh session for revocation and rotation."""

    __tablename__ = "refresh_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    token_family = Column(String(64), nullable=False, index=True)
    audience = Column(Enum(SessionAudience), default=SessionAudience.LEARNER, nullable=False, index=True)
    credential_version = Column(Integer, default=1, nullable=False)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(64), nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_used_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_sessions")

    __table_args__ = (
        Index("idx_refresh_user_audience_active", "user_id", "audience", "revoked_at"),
    )


class PasswordRecoveryToken(Base):
    """Single-use password reset token scoped to an account."""

    __tablename__ = "password_recovery_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")


class GuardianRelationship(Base):
    """Guardian authority for a learner, used for minor provisioning."""

    __tablename__ = "guardian_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    learner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_name = Column(String(255), nullable=False)
    guardian_email = Column(String(255), nullable=True, index=True)
    relationship = Column(String(100), nullable=False)
    verification_status = Column(String(50), default="pending", nullable=False)
    permissions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ConsentPurpose(str, PyEnum):
    ACCOUNT_CREATION = "account_creation"
    LEARNING_ACCESS = "learning_access"
    EMAIL_COMMUNICATION = "email_communication"
    COMMUNITY_PARTICIPATION = "community_participation"


class ConsentRecord(Base):
    """Consent granted by a guardian or organization authority."""

    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    learner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    authority_type = Column(String(50), nullable=False)
    authority_id = Column(String(100), nullable=True)
    policy_version = Column(String(50), nullable=False)
    purpose = Column(Enum(ConsentPurpose), nullable=False)
    source = Column(String(100), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_consent_learner_purpose_active", "learner_user_id", "purpose", "revoked_at"),
    )
