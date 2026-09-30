"""Load missing catalog defaults: python -m scripts.seed_catalog (from backend/)."""

import argparse
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.catalog import Bank, ProjectOption


Name = Annotated[str, Field(strict=True, min_length=1, max_length=120)]
DEFAULT_TAXONOMY = Path(__file__).resolve().parents[1] / "data" / "taxonomy.json"


class ProjectSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
    name: Name

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        return " ".join(value.split()) if isinstance(value, str) else value


class Taxonomy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    banks: list[Name]
    projects: list[ProjectSeed]

    @field_validator("banks", mode="before")
    @classmethod
    def normalize_banks(cls, values):
        if isinstance(values, list):
            return [
                " ".join(value.split()) if isinstance(value, str) else value
                for value in values
            ]
        return values


def seed_catalog(db: Session, taxonomy: Taxonomy) -> tuple[int, int]:
    """Stage missing entries; the caller commits the transaction."""
    bank_names = set(db.scalars(select(Bank.normalized_name)))
    project_keys = set(db.scalars(select(ProjectOption.key)))
    added_banks = added_projects = 0
    for name in taxonomy.banks:
        normalized = name.lower()
        if normalized not in bank_names:
            db.add(Bank(name=name, normalized_name=normalized))
            bank_names.add(normalized)
            added_banks += 1
    for project in taxonomy.projects:
        if project.key not in project_keys:
            db.add(ProjectOption(key=project.key, name=project.name))
            project_keys.add(project.key)
            added_projects += 1
    return added_banks, added_projects


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_TAXONOMY)
    args = parser.parse_args()
    try:
        taxonomy = Taxonomy.model_validate_json(args.file.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        parser.exit(1, f"Cannot load taxonomy: {exc}\n")
    try:
        with SessionLocal.begin() as db:
            banks, projects = seed_catalog(db, taxonomy)
    except SQLAlchemyError:
        parser.exit(
            1,
            "Catalog import failed; no changes committed. Check database connectivity and run alembic upgrade head.\n",
        )
    print(
        f"Added {banks} bank(s) and {projects} project(s). Existing entries preserved."
    )


if __name__ == "__main__":
    main()
