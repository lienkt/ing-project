"""Create/migrate the demo database; optionally move the old seeded demo records."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from pydantic import TypeAdapter
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.campaign import Campaign, CampaignDetails, Evaluation
from app.models.catalog import Bank, ProjectOption
from app.models.features import CampaignFeature
from scripts.seed_demo import DemoCampaign, seed_demo


def engine_for(url):
    url = make_url(url)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    return create_engine(url)


def copy_columns(record, excluded):
    return {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
        if column.name not in excluded
    }


def move_existing(source_engine, demo_engine, demo_urls):
    """Copy only known legacy demo URLs with DEMO bank names, then remove originals.

    Commit the destination first: failure never removes the source copy.
    Refuse conflicting destination URLs rather than overwrite either version.
    """
    moved = 0
    with Session(source_engine) as source, source.begin():
        records = list(
            source.scalars(
                select(Campaign).where(
                    Campaign.campaign_url.in_(demo_urls),
                    Campaign.bank_name.startswith("DEMO — "),
                )
            )
        )
        if not records:
            return 0
        with Session(demo_engine) as destination, destination.begin():
            for original in records:
                if destination.scalar(
                    select(Campaign.id).where(
                        Campaign.campaign_url == original.campaign_url
                    )
                ):
                    raise RuntimeError(
                        "A demo URL already exists in the destination. No source records were removed; resolve the duplicate before moving."
                    )
                bank_name = original.bank_name.removeprefix("DEMO — ")
                project = original.project.removeprefix("demo_")
                if destination.get(ProjectOption, project) is None:
                    destination.add(
                        ProjectOption(
                            key=project, name=project.replace("_", " ").title()
                        )
                    )
                if (
                    destination.scalar(
                        select(Bank.id).where(Bank.normalized_name == bank_name.lower())
                    )
                    is None
                ):
                    destination.add(
                        Bank(name=bank_name, normalized_name=bank_name.lower())
                    )
                copied = Campaign(
                    **{
                        **copy_columns(original, {"id"}),
                        "bank_name": bank_name,
                        "project": project,
                    }
                )
                if original.details:
                    values = copy_columns(original.details, {"campaign_id"})
                    if values["campaign_name"]:
                        values["campaign_name"] = values["campaign_name"].removeprefix(
                            "DEMO — "
                        )
                    copied.details = CampaignDetails(**values)
                if original.features:
                    values = copy_columns(original.features, {"campaign_id"})
                    if values["product_name"]:
                        values["product_name"] = values["product_name"].removeprefix(
                            "DEMO — "
                        )
                    copied.features = CampaignFeature(**values)
                if original.evaluation:
                    copied.evaluation = Evaluation(
                        **copy_columns(original.evaluation, {"id", "campaign_id"})
                    )
                destination.add(copied)
                destination.flush()
        # Destination has committed successfully. Remove only those source records.
        old_banks = {row.bank_name.lower() for row in records}
        old_projects = {row.project for row in records}
        for original in records:
            source.delete(original)
        source.flush()
        for bank in source.scalars(
            select(Bank).where(Bank.normalized_name.in_(old_banks))
        ):
            if (
                source.scalar(
                    select(Campaign.id)
                    .where(func.lower(Campaign.bank_name) == bank.normalized_name)
                    .limit(1)
                )
                is None
            ):
                source.delete(bank)
        for project in old_projects:
            if (
                project.startswith("demo_")
                and source.scalar(
                    select(Campaign.id).where(Campaign.project == project).limit(1)
                )
                is None
            ):
                option = source.get(ProjectOption, project)
                if option:
                    source.delete(option)
        moved = len(records)
    return moved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--move-existing",
        action="store_true",
        help="Move legacy demo fixtures out of the real database, preserving edits.",
    )
    args = parser.parse_args()
    rows = TypeAdapter(list[DemoCampaign]).validate_python(
        json.loads(
            (
                Path(__file__).resolve().parents[1] / "data" / "demo_campaigns.json"
            ).read_text()
        )
    )
    url = make_url(settings.demo_database_url)
    if not url.drivername.startswith("postgresql") or not url.database:
        raise SystemExit("Demo setup requires a named PostgreSQL database.")
    admin = engine_for(url.set(database="postgres"))
    with admin.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        if not connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": url.database},
        ):
            quoted = connection.dialect.identifier_preparer.quote_identifier(
                url.database
            )
            connection.exec_driver_sql(f"CREATE DATABASE {quoted}")
    admin.dispose()
    env = {**os.environ, "DATA_MODE": "demo"}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env,
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    demo_engine = engine_for(settings.demo_database_url)
    if args.move_existing:
        real_engine = engine_for(settings.database_url)
        moved = move_existing(
            real_engine, demo_engine, [str(row.campaign_url) for row in rows]
        )
        real_engine.dispose()
        print(
            f"Moved {moved} legacy demo campaigns; existing research campaigns preserved."
        )
    with Session(demo_engine) as db, db.begin():
        added = seed_demo(db, rows)
    demo_engine.dispose()
    print(
        f"Added {added} demo campaigns. Set DATA_MODE=demo in backend/.env and restart the backend."
    )


if __name__ == "__main__":
    main()
