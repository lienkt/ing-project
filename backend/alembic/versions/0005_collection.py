"""Separate collection snapshots and automatic proposals from final features."""
from alembic import op
import sqlalchemy as sa
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("source_imports",
        sa.Column("source_id", sa.String(120), primary_key=True),
        sa.Column("source_url", sa.String(2048), nullable=False, unique=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), unique=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("engine", sa.String(100), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("page", sa.JSON()), sa.Column("error", sa.Text()),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("feature_proposals",
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("token", sa.String(36), nullable=False),
        sa.Column("engine", sa.String(100), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False), sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("baseline", sa.JSON(), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))


def downgrade():
    op.drop_table("feature_proposals")
    op.drop_table("source_imports")
