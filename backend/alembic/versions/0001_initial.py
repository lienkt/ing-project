"""Initial campaign workflow tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bank_name", sa.String(120), nullable=False),
        sa.Column("project", sa.String(40), nullable=False),
        sa.Column("campaign_url", sa.String(2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_campaigns_bank_name", "campaigns", ["bank_name"])
    op.create_index("ix_campaigns_project", "campaigns", ["project"])
    op.create_table("campaign_details",
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True),
        *[sa.Column(name, kind, nullable=True) for name, kind in [
            ("campaign_name", sa.String(300)), ("headline", sa.Text()), ("subheadline", sa.Text()),
            ("main_message", sa.Text()), ("cta_text", sa.String(300)), ("notes", sa.Text()),
            ("text_density", sa.String(40)), ("tone", sa.String(120)),
            ("feature_vs_benefit", sa.String(40)), ("emotional_vs_rational", sa.String(40)),
            ("customer_vs_product_focus", sa.String(40))]])
    scores = ["clarity_score", "visual_score", "benefit_score", "cta_score", "overall_score"]
    op.create_table("evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("source", sa.String(40), nullable=False, server_default="manual"),
        *[sa.Column(name, sa.Integer(), nullable=False) for name in scores],
        sa.Column("evaluation_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *[sa.CheckConstraint(f"{name} BETWEEN 1 AND 5", name=f"ck_{name}") for name in scores])

def downgrade():
    op.drop_table("evaluations")
    op.drop_table("campaign_details")
    op.drop_index("ix_campaigns_project", table_name="campaigns")
    op.drop_index("ix_campaigns_bank_name", table_name="campaigns")
    op.drop_table("campaigns")
