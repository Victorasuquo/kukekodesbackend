"""Organization and tenant management API."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.organizations.schemas import (
    CohortCreateRequest,
    CohortMembershipCreateRequest,
    CohortResponse,
    CourseAssignmentCreateRequest,
    CourseAssignmentResponse,
    InvitationCreateRequest,
    InvitationResponse,
    MembershipByLearnerIdRequest,
    MembershipCreateRequest,
    MembershipResponse,
    OrganizationCreateRequest,
    OrganizationResponse,
)
from app.api.v1.organizations.service import OrganizationService
from app.models.organization import OrganizationRole, CourseAssignment
from app.dependencies import get_db
from app.security import get_current_user


router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: OrganizationCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.create_organization(db, current_user, request.name, request.slug, request.timezone)


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.list_organizations(db, current_user)


@router.get("/{organization_id}/memberships", response_model=list[MembershipResponse])
async def list_memberships(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.list_memberships(db, current_user, organization_id)


@router.post("/{organization_id}/memberships", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_membership(
    organization_id: str,
    request: MembershipCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.add_membership(db, current_user, organization_id, request.user_id, request.role)


@router.post("/{organization_id}/memberships/by-learner-id", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_membership_by_learner_id(
    organization_id: str,
    request: MembershipByLearnerIdRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.add_membership_by_learner_id(
        db,
        current_user,
        organization_id,
        request.learner_id,
        request.role,
    )


@router.post("/{organization_id}/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    organization_id: str,
    request: InvitationCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invitation, raw_token = OrganizationService.create_invitation(
        db, current_user, organization_id, request.recipient_email, request.role, request.expires_in_days
    )
    response = InvitationResponse.model_validate(invitation)
    response.token = raw_token
    return response


@router.get("/{organization_id}/cohorts", response_model=list[CohortResponse])
async def list_cohorts(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.list_cohorts(db, current_user, organization_id)


@router.post("/{organization_id}/cohorts", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
async def create_cohort(
    organization_id: str,
    request: CohortCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.create_cohort(db, current_user, organization_id, request.name, request.description)


@router.post("/{organization_id}/cohorts/{cohort_id}/members", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_cohort_member(
    organization_id: str,
    cohort_id: str,
    request: CohortMembershipCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = OrganizationService.add_cohort_member(db, current_user, organization_id, cohort_id, request.user_id)
    return {"id": str(membership.id), "cohort_id": str(membership.cohort_id), "user_id": str(membership.user_id)}


@router.post("/{organization_id}/assignments", response_model=CourseAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_course(
    organization_id: str,
    request: CourseAssignmentCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrganizationService.assign_course(
        db, current_user, organization_id, request.course_id, request.cohort_id, request.user_id, request.due_at
    )

@router.get("/{organization_id}/assignments", response_model=list[CourseAssignmentResponse])
async def list_assignments(organization_id: str, current_user: Dict[str, Any] = Depends(get_current_user), db: Session = Depends(get_db)):
    OrganizationService.require_org_role(db, current_user, organization_id, {OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.INSTRUCTOR})
    return db.query(CourseAssignment).filter(CourseAssignment.organization_id == organization_id).order_by(CourseAssignment.created_at.desc()).all()
