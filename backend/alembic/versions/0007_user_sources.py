"""Persist sources added from the scraping screen."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_sources",
        sa.Column("source_id", sa.String(120), primary_key=True),
        sa.Column("source_url", sa.String(2048), nullable=False, unique=True),
        sa.Column("definition", sa.JSON(), nullable=False),
    )


def downgrade():
    op.drop_table("user_sources")
