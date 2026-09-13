"""Schemas for organizations and tenant-scoped access."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.organization import OrganizationRole


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    timezone: str = Field("UTC", max_length=64)


class OrganizationResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    owner_user_id: UUID
    status: str
    timezone: str
    created_at: datetime

    class Config:
        from_attributes = True


class MembershipCreateRequest(BaseModel):
    user_id: UUID
    role: OrganizationRole = OrganizationRole.STUDENT


class MembershipByLearnerIdRequest(BaseModel):
    learner_id: str = Field(..., min_length=3, max_length=32)
    role: OrganizationRole = OrganizationRole.STUDENT


class MembershipResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    status: str
    joined_at: datetime

    class Config:
        from_attributes = True


class InvitationCreateRequest(BaseModel):
    recipient_email: Optional[str] = None
    role: OrganizationRole = OrganizationRole.STUDENT
    expires_in_days: int = Field(7, ge=1, le=30)


class InvitationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    recipient_email: Optional[str]
    role: str
    expires_at: datetime
    accepted_at: Optional[datetime]
    created_at: datetime
    token: Optional[str] = None

    class Config:
        from_attributes = True


class CohortCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class CohortResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CohortMembershipCreateRequest(BaseModel):
    user_id: UUID


class CourseAssignmentCreateRequest(BaseModel):
    course_id: UUID
    cohort_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    due_at: Optional[datetime] = None


class CourseAssignmentResponse(BaseModel):
    id: UUID
    course_id: UUID
    organization_id: UUID
    cohort_id: Optional[UUID]
    user_id: Optional[UUID]
    due_at: Optional[datetime]
    state: str
    created_at: datetime

    class Config:
        from_attributes = True
