"""Introduce learner ids and remove unique email constraint.

Revision ID: 20260912_0001
Revises:
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260912_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("users"):
        from app.db.postgres import Base
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=bind)
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "learner_id" not in user_columns:
        op.add_column("users", sa.Column("learner_id", sa.String(length=32), nullable=True))

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_learner_id ON users (learner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_learner_id_active ON users (learner_id, is_active)")

    # Constraint names differ across historical metadata-create deployments. The
    # PostgreSQL default for a unique Column("email") is users_email_key.
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key")


def downgrade() -> None:
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.drop_index("idx_user_learner_id_active", table_name="users")
    op.drop_index("ix_users_learner_id", table_name="users")
    op.drop_column("users", "learner_id")
