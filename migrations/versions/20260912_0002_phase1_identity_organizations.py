"""Add Phase 1 identity, consent, and organization tables.

Revision ID: 20260912_0002
Revises: 20260912_0001
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


revision = "20260912_0002"
down_revision = "20260912_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    user_columns = {column["name"] for column in inspector.get_columns("users")} if "users" in tables else set()
    phase1_tables = {
        "credentials",
        "refresh_sessions",
        "password_recovery_tokens",
        "organizations",
        "organization_memberships",
        "organization_invitations",
        "cohorts",
        "cohort_memberships",
        "course_assignments",
    }
    if phase1_tables.issubset(tables) and "contact_email" in user_columns:
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    if "contact_email" not in user_columns:
        op.add_column("users", sa.Column("contact_email", sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET contact_email = lower(email) WHERE contact_email IS NULL")
    op.execute(
        "UPDATE users SET learner_id = upper(substring(replace(id::text, '-', '') from 1 for 10)) "
        "WHERE learner_id IS NULL"
    )
    op.alter_column("users", "learner_id", existing_type=sa.String(length=32), nullable=False)
    op.create_index("idx_user_contact_email_active", "users", ["contact_email", "is_active"], unique=False)

    session_audience = postgresql.ENUM("LEARNER", "ADMIN", name="sessionaudience")
    session_audience.create(op.get_bind(), checkfirst=True)
    consent_purpose = postgresql.ENUM(
        "ACCOUNT_CREATION",
        "LEARNING_ACCESS",
        "EMAIL_COMMUNICATION",
        "COMMUNITY_PARTICIPATION",
        name="consentpurpose",
    )
    consent_purpose.create(op.get_bind(), checkfirst=True)
    organization_status = postgresql.ENUM("ACTIVE", "SUSPENDED", "ARCHIVED", name="organizationstatus")
    organization_status.create(op.get_bind(), checkfirst=True)
    organization_role = postgresql.ENUM("OWNER", "ADMIN", "INSTRUCTOR", "STUDENT", name="organizationrole")
    organization_role.create(op.get_bind(), checkfirst=True)
    membership_status = postgresql.ENUM("ACTIVE", "INVITED", "SUSPENDED", name="membershipstatus")
    membership_status.create(op.get_bind(), checkfirst=True)
    assignment_state = postgresql.ENUM("ACTIVE", "CANCELLED", "COMPLETED", name="assignmentstate")
    assignment_state.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("hash_version", sa.String(length=32), nullable=False, server_default="bcrypt-12"),
        sa.Column("credential_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("password_changed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_credentials_user_id"), "credentials", ["user_id"], unique=False)

    op.create_table(
        "refresh_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("token_family", sa.String(length=64), nullable=False),
        sa.Column("audience", session_audience, nullable=False, server_default="LEARNER"),
        sa.Column("credential_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_refresh_sessions_token_hash"), "refresh_sessions", ["token_hash"], unique=False)
    op.create_index("idx_refresh_user_audience_active", "refresh_sessions", ["user_id", "audience", "revoked_at"], unique=False)

    op.create_table(
        "password_recovery_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_password_recovery_tokens_user_id"), "password_recovery_tokens", ["user_id"], unique=False)
    op.create_index(op.f("ix_password_recovery_tokens_token_hash"), "password_recovery_tokens", ["token_hash"], unique=False)

    op.create_table(
        "guardian_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("learner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guardian_name", sa.String(length=255), nullable=False),
        sa.Column("guardian_email", sa.String(length=255), nullable=True),
        sa.Column("relationship", sa.String(length=100), nullable=False),
        sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("permissions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_guardian_relationships_learner_user_id"), "guardian_relationships", ["learner_user_id"], unique=False)

    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("learner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("authority_type", sa.String(length=50), nullable=False),
        sa.Column("authority_id", sa.String(length=100), nullable=True),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
        sa.Column("purpose", consent_purpose, nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_consent_learner_purpose_active", "consent_records", ["learner_user_id", "purpose", "revoked_at"], unique=False)

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", organization_status, nullable=False, server_default="ACTIVE"),
        sa.Column("branding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("policy_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=False)

    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", organization_role, nullable=False, server_default="STUDENT"),
        sa.Column("status", membership_status, nullable=False, server_default="ACTIVE"),
        sa.Column("invitation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_user_membership"),
    )
    op.create_index("idx_membership_user_status", "organization_memberships", ["user_id", "status"], unique=False)

    op.create_table(
        "organization_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=True),
        sa.Column("role", organization_role, nullable=False, server_default="STUDENT"),
        sa.Column("issuer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("token_hash"),
    )

    op.create_table(
        "cohorts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "name", name="uq_cohort_org_name"),
    )

    op.create_table(
        "cohort_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("cohort_id", "user_id", name="uq_cohort_user"),
    )

    op.create_table(
        "course_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("state", assignment_state, nullable=False, server_default="ACTIVE"),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_assignment_org_course_state", "course_assignments", ["organization_id", "course_id", "state"], unique=False)

    op.execute(
        """
        INSERT INTO credentials (id, user_id, password_hash, hash_version, credential_version, password_changed_at, created_at, updated_at)
        SELECT gen_random_uuid(), id, password_hash, 'bcrypt-12', 1, COALESCE(updated_at, created_at, now()), now(), now()
        FROM users
        WHERE password_hash IS NOT NULL
        ON CONFLICT (user_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("idx_assignment_org_course_state", table_name="course_assignments")
    op.drop_table("course_assignments")
    op.drop_table("cohort_memberships")
    op.drop_table("cohorts")
    op.drop_table("organization_invitations")
    op.drop_index("idx_membership_user_status", table_name="organization_memberships")
    op.drop_table("organization_memberships")
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")
    op.drop_index("idx_consent_learner_purpose_active", table_name="consent_records")
    op.drop_table("consent_records")
    op.drop_index(op.f("ix_guardian_relationships_learner_user_id"), table_name="guardian_relationships")
    op.drop_table("guardian_relationships")
    op.drop_index(op.f("ix_password_recovery_tokens_token_hash"), table_name="password_recovery_tokens")
    op.drop_index(op.f("ix_password_recovery_tokens_user_id"), table_name="password_recovery_tokens")
    op.drop_table("password_recovery_tokens")
    op.drop_index("idx_refresh_user_audience_active", table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_token_hash"), table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
    op.drop_index(op.f("ix_credentials_user_id"), table_name="credentials")
    op.drop_table("credentials")
    op.drop_index("idx_user_contact_email_active", table_name="users")
    op.drop_column("users", "contact_email")

    postgresql.ENUM(name="assignmentstate").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="membershipstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="organizationrole").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="organizationstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="consentpurpose").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="sessionaudience").drop(op.get_bind(), checkfirst=True)
