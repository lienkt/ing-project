"""Persist bank and project options, preserving existing campaigns."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade():
    banks = op.create_table("banks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("normalized_name", sa.String(120), nullable=False, unique=True))
    projects = op.create_table("projects",
        sa.Column("key", sa.String(40), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False))
    op.bulk_insert(banks, [{"name": name, "normalized_name": name.lower()} for name in ["ING", "KBC", "Belfius", "BNP Paribas Fortis"]])
    op.bulk_insert(projects, [{"key": key, "name": key.replace("_", " ").title()} for key in ["credit_card", "savings_account", "current_account", "personal_loan", "mortgage", "insurance", "investment", "other"]])
    op.execute("INSERT INTO banks (name, normalized_name) SELECT MIN(bank_name), LOWER(bank_name) FROM campaigns WHERE LOWER(bank_name) NOT IN (SELECT normalized_name FROM banks) GROUP BY LOWER(bank_name)")
    op.execute("INSERT INTO projects (key, name) SELECT DISTINCT project, project FROM campaigns WHERE project NOT IN (SELECT key FROM projects)")

def downgrade():
    op.drop_table("projects")
    op.drop_table("banks")
