"""Individual accountability clusters and matching queue."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
revision = "20260919_0006"
down_revision = "20260914_0005"
branch_labels = None
depends_on = None
def upgrade():
    b=op.get_bind(); tables=set(inspect(b).get_table_names()); u=postgresql.UUID(as_uuid=True)
    if "accountability_clusters" not in tables:
        op.create_table("accountability_clusters", sa.Column("id",u,primary_key=True,server_default=sa.text("gen_random_uuid()")), sa.Column("name",sa.String(120),unique=True,nullable=False), sa.Column("status",sa.String(20),nullable=False,server_default="active"), sa.Column("capacity",sa.Integer(),nullable=False,server_default="15"), sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")))
    if "accountability_cluster_memberships" not in tables:
        op.create_table("accountability_cluster_memberships", sa.Column("id",u,primary_key=True,server_default=sa.text("gen_random_uuid()")), sa.Column("cluster_id",u,sa.ForeignKey("accountability_clusters.id",ondelete="CASCADE"),nullable=False), sa.Column("user_id",u,sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False), sa.Column("joined_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")), sa.Column("left_at",sa.DateTime()), sa.UniqueConstraint("cluster_id","user_id",name="uq_accountability_cluster_user"))
        op.create_index("idx_accountability_members_cluster","accountability_cluster_memberships",["cluster_id"])
        op.create_index("idx_accountability_members_user","accountability_cluster_memberships",["user_id"])
    if "accountability_match_queue" not in tables:
        op.create_table("accountability_match_queue", sa.Column("id",u,primary_key=True,server_default=sa.text("gen_random_uuid()")), sa.Column("user_id",u,sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False,unique=True), sa.Column("status",sa.String(20),nullable=False,server_default="waiting"), sa.Column("queued_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")), sa.Column("matched_cluster_id",u,sa.ForeignKey("accountability_clusters.id",ondelete="SET NULL")), sa.Column("updated_at",sa.DateTime(),nullable=False,server_default=sa.text("now()")))
        op.create_index("idx_accountability_queue_status","accountability_match_queue",["status","queued_at"])
def downgrade():
    op.drop_table("accountability_match_queue"); op.drop_table("accountability_cluster_memberships"); op.drop_table("accountability_clusters")
