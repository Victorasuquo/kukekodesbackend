"""Introduce learner ids and remove unique email constraint.

Revision ID: 20260912_0001
Revises:
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260912_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("learner_id", sa.String(length=32), nullable=True))
    op.create_index("ix_users_learner_id", "users", ["learner_id"], unique=True)
    op.create_index("idx_user_learner_id_active", "users", ["learner_id", "is_active"], unique=False)

    # Constraint names differ across historical metadata-create deployments. The
    # PostgreSQL default for a unique Column("email") is users_email_key.
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key")


def downgrade() -> None:
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.drop_index("idx_user_learner_id_active", table_name="users")
    op.drop_index("ix_users_learner_id", table_name="users")
    op.drop_column("users", "learner_id")
