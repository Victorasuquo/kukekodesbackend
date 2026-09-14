"""Add Phase 2 assessments and persisted certificates.

Revision ID: 20260913_0003
Revises: 20260912_0002
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260913_0003"
down_revision = "20260912_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Phase 2 adds resumable/offline progress fields to the existing table.
    # Keep this additive and idempotent so upgrades never recreate learner data.
    if "user_progress" in tables:
        columns = {column["name"] for column in inspect(bind).get_columns("user_progress")}
        if "resume_position_seconds" not in columns:
            op.add_column(
                "user_progress",
                sa.Column("resume_position_seconds", sa.Integer(), nullable=False, server_default="0"),
            )
        if "last_idempotency_key" not in columns:
            op.add_column("user_progress", sa.Column("last_idempotency_key", sa.String(length=128), nullable=True))
        indexes = {index["name"] for index in inspect(bind).get_indexes("user_progress")}
        if "idx_progress_user_idempotency" not in indexes:
            op.create_index("idx_progress_user_idempotency", "user_progress", ["user_id", "last_idempotency_key"])

    for table_name in ("courses", "modules", "lessons"):
        if table_name in tables:
            columns = {column["name"] for column in inspect(bind).get_columns(table_name)}
            if "version" not in columns:
                op.add_column(table_name, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    for table_name in ("courses", "modules", "lessons"):
        columns = {column["name"] for column in inspect(bind).get_columns(table_name)}
        if "version" not in columns:
            op.add_column(table_name, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    progress_columns = {column["name"] for column in inspect(bind).get_columns("user_progress")}
    if "resume_position_seconds" not in progress_columns:
        op.add_column("user_progress", sa.Column("resume_position_seconds", sa.Integer(), nullable=False, server_default="0"))
    if "last_idempotency_key" not in progress_columns:
        op.add_column("user_progress", sa.Column("last_idempotency_key", sa.String(length=128), nullable=True))
        op.create_index("idx_progress_user_idempotency", "user_progress", ["user_id", "last_idempotency_key"])

    if "quizzes" not in tables:
        op.create_table(
            "quizzes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("passing_score", sa.Integer(), nullable=False, server_default="70"),
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("idx_quiz_course_published", "quizzes", ["course_id", "is_published"])

    if "quiz_questions" not in tables:
        op.create_table(
            "quiz_questions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("order", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("quiz_id", "order", name="uq_quiz_question_order"),
        )
        op.create_index(op.f("ix_quiz_questions_quiz_id"), "quiz_questions", ["quiz_id"])

    if "quiz_answers" not in tables:
        op.create_table(
            "quiz_answers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("answer_text", sa.Text(), nullable=False),
            sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index(op.f("ix_quiz_answers_question_id"), "quiz_answers", ["question_id"])

    if "quiz_attempts" not in tables:
        op.create_table(
            "quiz_attempts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("submitted_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("idx_quiz_attempt_user_quiz", "quiz_attempts", ["user_id", "quiz_id", "submitted_at"])
        op.create_index(op.f("ix_quiz_attempts_passed"), "quiz_attempts", ["passed"])

    if "certificates" not in tables:
        op.create_table(
            "certificates",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
            sa.Column("certificate_id", sa.String(length=64), nullable=False),
            sa.Column("verification_code", sa.String(length=32), nullable=False),
            sa.Column("file_key", sa.String(length=500), nullable=True),
            sa.Column("issued_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("user_id", "course_id", name="uq_certificate_user_course"),
            sa.UniqueConstraint("certificate_id"),
            sa.UniqueConstraint("verification_code"),
        )
        op.create_index("idx_certificate_course_issued", "certificates", ["course_id", "issued_at"])
        op.create_index(op.f("ix_certificates_certificate_id"), "certificates", ["certificate_id"])
        op.create_index(op.f("ix_certificates_verification_code"), "certificates", ["verification_code"])


def downgrade() -> None:
    for table_name in ("certificates", "quiz_attempts", "quiz_answers", "quiz_questions", "quizzes"):
        if table_name in set(inspect(op.get_bind()).get_table_names()):
            op.drop_table(table_name)
    progress_columns = {column["name"] for column in inspect(op.get_bind()).get_columns("user_progress")}
    if "last_idempotency_key" in progress_columns:
        op.drop_index("idx_progress_user_idempotency", table_name="user_progress")
        op.drop_column("user_progress", "last_idempotency_key")
    if "resume_position_seconds" in progress_columns:
        op.drop_column("user_progress", "resume_position_seconds")
    for table_name in ("lessons", "modules", "courses"):
        columns = {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}
        if "version" in columns:
            op.drop_column(table_name, "version")
