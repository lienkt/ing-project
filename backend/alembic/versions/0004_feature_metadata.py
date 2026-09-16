"""Extend labeling metadata and headline counts; average length is derived."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("campaign_features") as batch:
        batch.add_column(sa.Column("bank_type", sa.String(20), nullable=True))
        batch.add_column(sa.Column("product_name", sa.String(300), nullable=True))
        batch.add_column(sa.Column("language", sa.String(20), nullable=True))
        batch.add_column(sa.Column("capture_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("headline_length", sa.Integer(), nullable=True))
        batch.create_check_constraint("ck_cf_bank_type", "bank_type IN ('Traditional', 'Challenger', 'Neobank')")
        batch.create_check_constraint("ck_cf_language", "language IN ('Dutch', 'French', 'English', 'Other')")
        batch.create_check_constraint("ck_cf_headline_length", "headline_length >= 0")


def downgrade():
    with op.batch_alter_table("campaign_features") as batch:
        for name in ("bank_type", "language", "headline_length"):
            batch.drop_constraint(f"ck_cf_{name}", type_="check")
        for name in ("bank_type", "product_name", "language", "capture_date", "headline_length"):
            batch.drop_column(name)
