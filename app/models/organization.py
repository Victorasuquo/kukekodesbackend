"""Organization, membership, cohort, and assignment models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.postgres import Base


class OrganizationStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class OrganizationRole(str, PyEnum):
    OWNER = "owner"
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class MembershipStatus(str, PyEnum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"


class AssignmentState(str, PyEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE, nullable=False, index=True)
    branding = Column(JSONB, nullable=True)
    policy_config = Column(JSONB, nullable=True)
    timezone = Column(String(64), default="UTC", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", foreign_keys=[owner_user_id])
    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(OrganizationRole), default=OrganizationRole.STUDENT, nullable=False, index=True)
    status = Column(Enum(MembershipStatus), default=MembershipStatus.ACTIVE, nullable=False, index=True)
    invitation_id = Column(UUID(as_uuid=True), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="organization_memberships")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_organization_user_membership"),
        Index("idx_membership_user_status", "user_id", "status"),
    )


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=True, index=True)
    role = Column(Enum(OrganizationRole), default=OrganizationRole.STUDENT, nullable=False)
    issuer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    memberships = relationship("CohortMembership", back_populates="cohort", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_cohort_org_name"),
    )


class CohortMembership(Base):
    __tablename__ = "cohort_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    cohort_id = Column(UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cohort = relationship("Cohort", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("cohort_id", "user_id", name="uq_cohort_user"),
    )


class CourseAssignment(Base):
    __tablename__ = "course_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    cohort_id = Column(UUID(as_uuid=True), ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    due_at = Column(DateTime, nullable=True)
    state = Column(Enum(AssignmentState), default=AssignmentState.ACTIVE, nullable=False, index=True)
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_assignment_org_course_state", "organization_id", "course_id", "state"),
    )
