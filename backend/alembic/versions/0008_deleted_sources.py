"""Persist removal of configured scraping sources."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "deleted_sources",
        sa.Column("source_id", sa.String(120), primary_key=True),
    )


def downgrade():
    op.drop_table("deleted_sources")
