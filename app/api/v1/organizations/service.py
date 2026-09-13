"""Organization service layer with tenant checks."""

import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.dependencies import ConflictError, NotFoundError, UnauthorizedError
from app.models.organization import (
    AssignmentState,
    Cohort,
    CohortMembership,
    CourseAssignment,
    MembershipStatus,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationRole,
)
from app.models.user import User, UserRole


ADMIN_OR_OWNER = {OrganizationRole.OWNER, OrganizationRole.ADMIN}


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class OrganizationService:
    @staticmethod
    def _is_platform_admin(current_user: dict) -> bool:
        return current_user.get("role") == UserRole.ADMIN.value and current_user.get("aud") == "admin"

    @staticmethod
    def require_org_role(db: Session, current_user: dict, organization_id: str, allowed_roles: set[OrganizationRole]) -> OrganizationMembership:
        if OrganizationService._is_platform_admin(current_user):
            membership = db.query(OrganizationMembership).filter(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == current_user.get("sub"),
            ).first()
            if membership:
                return membership
            return OrganizationMembership(
                organization_id=organization_id,
                user_id=current_user.get("sub"),
                role=OrganizationRole.OWNER,
                status=MembershipStatus.ACTIVE,
            )

        membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == current_user.get("sub"),
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        ).first()
        if not membership or membership.role not in allowed_roles:
            raise UnauthorizedError("Organization access required")
        return membership

    @staticmethod
    def create_organization(db: Session, current_user: dict, name: str, slug: str, timezone: str) -> Organization:
        if not OrganizationService._is_platform_admin(current_user):
            raise UnauthorizedError("Platform administrator access required")
        if db.query(Organization).filter(Organization.slug == slug).first():
            raise ConflictError("Organization slug already exists")
        organization = Organization(
            name=name,
            slug=slug,
            timezone=timezone,
            owner_user_id=current_user.get("sub"),
        )
        db.add(organization)
        db.flush()
        db.add(
            OrganizationMembership(
                organization_id=organization.id,
                user_id=current_user.get("sub"),
                role=OrganizationRole.OWNER,
                status=MembershipStatus.ACTIVE,
            )
        )
        db.commit()
        db.refresh(organization)
        return organization

    @staticmethod
    def list_organizations(db: Session, current_user: dict) -> list[Organization]:
        if OrganizationService._is_platform_admin(current_user):
            return db.query(Organization).order_by(Organization.created_at.desc()).all()
        memberships = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == current_user.get("sub"),
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        ).all()
        organization_ids = [m.organization_id for m in memberships]
        if not organization_ids:
            return []
        return db.query(Organization).filter(Organization.id.in_(organization_ids)).all()

    @staticmethod
    def add_membership(db: Session, current_user: dict, organization_id: str, user_id: UUID, role: OrganizationRole) -> OrganizationMembership:
        OrganizationService.require_org_role(db, current_user, organization_id, ADMIN_OR_OWNER)
        learner = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        if not learner:
            raise NotFoundError("User", str(user_id))
        existing = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
        ).first()
        if existing:
            existing.role = role
            existing.status = MembershipStatus.ACTIVE
            db.commit()
            db.refresh(existing)
            return existing
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            status=MembershipStatus.ACTIVE,
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership

    @staticmethod
    def add_membership_by_learner_id(
        db: Session,
        current_user: dict,
        organization_id: str,
        learner_id: str,
        role: OrganizationRole,
    ) -> OrganizationMembership:
        learner = db.query(User).filter(
            User.learner_id == learner_id.strip().upper(),
            User.is_active.is_(True),
        ).first()
        if not learner:
            raise NotFoundError("Learner", learner_id)
        return OrganizationService.add_membership(db, current_user, organization_id, learner.id, role)

    @staticmethod
    def list_memberships(db: Session, current_user: dict, organization_id: str) -> list[OrganizationMembership]:
        OrganizationService.require_org_role(db, current_user, organization_id, {OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.INSTRUCTOR})
        return db.query(OrganizationMembership).filter(OrganizationMembership.organization_id == organization_id).all()

    @staticmethod
    def create_invitation(db: Session, current_user: dict, organization_id: str, recipient_email: str | None, role: OrganizationRole, expires_in_days: int) -> tuple[OrganizationInvitation, str]:
        OrganizationService.require_org_role(db, current_user, organization_id, ADMIN_OR_OWNER)
        raw_token = secrets.token_urlsafe(32)
        invitation = OrganizationInvitation(
            organization_id=organization_id,
            recipient_email=recipient_email.lower() if recipient_email else None,
            role=role,
            issuer_user_id=current_user.get("sub"),
            token_hash=hash_token(raw_token),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation, raw_token

    @staticmethod
    def create_cohort(db: Session, current_user: dict, organization_id: str, name: str, description: str | None) -> Cohort:
        OrganizationService.require_org_role(db, current_user, organization_id, ADMIN_OR_OWNER)
        cohort = Cohort(organization_id=organization_id, name=name, description=description)
        db.add(cohort)
        db.commit()
        db.refresh(cohort)
        return cohort

    @staticmethod
    def list_cohorts(db: Session, current_user: dict, organization_id: str) -> list[Cohort]:
        OrganizationService.require_org_role(db, current_user, organization_id, {OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.INSTRUCTOR})
        return db.query(Cohort).filter(Cohort.organization_id == organization_id).order_by(Cohort.created_at.desc()).all()

    @staticmethod
    def add_cohort_member(db: Session, current_user: dict, organization_id: str, cohort_id: str, user_id: UUID) -> CohortMembership:
        OrganizationService.require_org_role(db, current_user, organization_id, ADMIN_OR_OWNER)
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id, Cohort.organization_id == organization_id).first()
        if not cohort:
            raise NotFoundError("Cohort", cohort_id)
        membership = CohortMembership(cohort_id=cohort.id, user_id=user_id)
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership

    @staticmethod
    def assign_course(db: Session, current_user: dict, organization_id: str, course_id: UUID, cohort_id: UUID | None, user_id: UUID | None, due_at) -> CourseAssignment:
        OrganizationService.require_org_role(db, current_user, organization_id, ADMIN_OR_OWNER)
        assignment = CourseAssignment(
            organization_id=organization_id,
            course_id=course_id,
            cohort_id=cohort_id,
            user_id=user_id,
            due_at=due_at,
            assigned_by_user_id=current_user.get("sub"),
            state=AssignmentState.ACTIVE,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
