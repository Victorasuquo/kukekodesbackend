"""Durable outbox events for reminders and provider integrations."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20260914_0005"
down_revision = "20260914_0004"
branch_labels = None
depends_on = None

def upgrade():
    if "outbox_events" not in inspect(op.get_bind()).get_table_names():
        u = postgresql.UUID(as_uuid=True)
        op.create_table(
            "outbox_events",
            sa.Column("id", u, primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("event_type", sa.String(120), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("available_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("processed_at", sa.DateTime()),
            sa.Column("last_error", sa.Text()),
            sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("idx_outbox_ready", "outbox_events", ["status", "available_at"])

def downgrade():
    op.drop_index("idx_outbox_ready", table_name="outbox_events")
    op.drop_table("outbox_events")
