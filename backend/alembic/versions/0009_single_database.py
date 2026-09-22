"""Remove runtime data-mode flags without removing any research records."""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    for table_name, id_column, payload_column in (
        ("source_imports", "source_id", "page"),
        ("page_captures", "id", "page"),
        ("user_sources", "source_id", "definition"),
    ):
        table = sa.table(
            table_name,
            sa.column(id_column, sa.String),
            sa.column(payload_column, sa.JSON),
        )
        for identity, payload in connection.execute(
            sa.select(table.c[id_column], table.c[payload_column])
        ).all():
            if not isinstance(payload, dict):
                continue
            updated = dict(payload)
            updated.pop("is_demo", None)
            updated.pop("is_example", None)
            if isinstance(updated.get("source"), dict):
                updated["source"] = dict(updated["source"])
                updated["source"].pop("is_example", None)
            connection.execute(
                table.update()
                .where(table.c[id_column] == identity)
                .values({payload_column: updated})
            )
    for name in ("source_imports", "feature_proposals"):
        table = sa.table(name, sa.column("engine", sa.String))
        connection.execute(
            table.update().where(table.c.engine == "demo").values(engine="configured")
        )
        with op.batch_alter_table(name) as batch:
            batch.drop_column("is_demo")


def downgrade():
    for name in ("source_imports", "feature_proposals"):
        with op.batch_alter_table(name) as batch:
            batch.add_column(
                sa.Column(
                    "is_demo", sa.Boolean(), nullable=False, server_default=sa.false()
                )
            )
