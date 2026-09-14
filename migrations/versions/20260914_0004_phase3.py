"""Phase 3 community refs, live sessions, and exercises."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
revision="20260914_0004"; down_revision="20260913_0003"; branch_labels=None; depends_on=None
def upgrade():
    b=op.get_bind(); tables=set(inspect(b).get_table_names()); u=lambda:postgresql.UUID(as_uuid=True)
    if "community_reports" not in tables:
        op.create_table("community_reports",sa.Column("id",u(),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("reporter_id",u(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("content_id",sa.String(128),nullable=False),sa.Column("reason",sa.String(500),nullable=False),sa.Column("status",sa.String(32),nullable=False,server_default="open"),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")))
        op.create_index("idx_community_reports_content","community_reports",["content_id"]); op.create_index("idx_community_reports_status","community_reports",["status"])
    if "community_blocks" not in tables:
        op.create_table("community_blocks",sa.Column("id",u(),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("blocker_id",u(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("blocked_user_id",u(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")),sa.UniqueConstraint("blocker_id","blocked_user_id",name="uq_community_block"))
    if "live_sessions" not in tables:
        op.create_table("live_sessions",sa.Column("id",u(),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("course_id",u(),sa.ForeignKey("courses.id",ondelete="CASCADE"),nullable=False),sa.Column("instructor_id",u(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("title",sa.String(255),nullable=False),sa.Column("description",sa.Text()),sa.Column("external_url",sa.String(1000),nullable=False),sa.Column("recording_url",sa.String(1000)),sa.Column("starts_at",sa.DateTime(),nullable=False),sa.Column("ends_at",sa.DateTime()),sa.Column("timezone",sa.String(64),nullable=False,server_default="UTC"),sa.Column("capacity",sa.Integer()),sa.Column("status",sa.String(32),nullable=False,server_default="scheduled"),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")))
        op.create_index("idx_live_sessions_course_start","live_sessions",["course_id","starts_at"])
    if "live_session_attendance" not in tables:
        op.create_table("live_session_attendance",sa.Column("id",u(),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("session_id",u(),sa.ForeignKey("live_sessions.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",u(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("joined_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")),sa.Column("left_at",sa.DateTime()),sa.UniqueConstraint("session_id","user_id",name="uq_live_session_attendee"))
    if "code_exercises" not in tables:
        op.create_table("code_exercises",sa.Column("id",u(),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("lesson_id",u(),sa.ForeignKey("lessons.id",ondelete="CASCADE"),nullable=False),sa.Column("title",sa.String(255),nullable=False),sa.Column("prompt",sa.Text(),nullable=False),sa.Column("runtime",sa.String(20),nullable=False,server_default="javascript"),sa.Column("starter_code",sa.Text()),sa.Column("expected_output",sa.Text()),sa.Column("is_published",sa.Boolean(),nullable=False,server_default=sa.false()))
    if "code_submissions" not in tables:
        op.create_table("code_submissions",sa.Column("id",u(),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("exercise_id",u(),sa.ForeignKey("code_exercises.id",ondelete="CASCADE"),nullable=False),sa.Column("user_id",u(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("source_code",sa.Text(),nullable=False),sa.Column("status",sa.String(32),nullable=False),sa.Column("output",sa.Text()),sa.Column("score",sa.Integer()),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")))
def downgrade():
    for t in ("code_submissions","code_exercises","live_session_attendance","live_sessions","community_blocks","community_reports"): op.drop_table(t)
