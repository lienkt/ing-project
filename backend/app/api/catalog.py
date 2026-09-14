import re
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import Field
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.catalog import Bank, ProjectOption
from app.models.campaign import Campaign
from datetime import datetime, timezone
from app.schemas.campaign import Schema

router = APIRouter(prefix="/api", tags=["catalog"])
DB = Annotated[Session, Depends(get_db)]

class CatalogInput(Schema):
    name: str = Field(min_length=1, max_length=120)

class BankRead(CatalogInput):
    id: int

class ProjectRead(CatalogInput):
    key: str

def persist(db: Session, record):
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This name already exists. Choose a different name.")
    db.refresh(record)
    return record

@router.get("/banks", response_model=list[BankRead])
def banks(db: DB):
    return db.scalars(select(Bank).order_by(Bank.name)).all()

@router.post("/banks", response_model=BankRead, status_code=201)
def add_bank(data: CatalogInput, db: DB):
    name = " ".join(data.name.split())
    return persist(db, Bank(name=name, normalized_name=name.lower()))

@router.get("/projects", response_model=list[ProjectRead])
def projects(db: DB):
    return db.scalars(select(ProjectOption).order_by(ProjectOption.name)).all()

@router.post("/projects", response_model=ProjectRead, status_code=201)
def add_project(data: CatalogInput, db: DB):
    name = " ".join(data.name.split())
    key = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not key or len(key) > 40:
        raise HTTPException(status_code=422, detail="Use a project name that produces 1–40 English letters, digits, or underscores.")
    return persist(db, ProjectOption(key=key, name=name))


def find_option(db: Session, model, identifier):
    record = db.get(model, identifier)
    if record is None:
        raise HTTPException(status_code=404, detail="Option not found")
    return record

@router.put("/banks/{bank_id}", response_model=BankRead)
def edit_bank(bank_id: int, data: CatalogInput, db: DB):
    bank = find_option(db, Bank, bank_id)
    old_name = bank.normalized_name
    name = " ".join(data.name.split())
    # Commit the option and linked campaign names together, including duplicate checks.
    with db.no_autoflush:
        db.execute(update(Campaign).where(func.lower(Campaign.bank_name) == old_name).values(bank_name=name, updated_at=datetime.now(timezone.utc)))
    bank.name = name
    bank.normalized_name = name.lower()
    return persist(db, bank)

@router.delete("/banks/{bank_id}", status_code=204)
def delete_bank(bank_id: int, db: DB):
    bank = find_option(db, Bank, bank_id)
    if db.scalar(select(Campaign.id).where(func.lower(Campaign.bank_name) == bank.normalized_name).limit(1)) is not None:
        raise HTTPException(status_code=409, detail="This bank is used by campaigns. Reassign or delete those campaigns first.")
    db.delete(bank)
    db.commit()
    return Response(status_code=204)

@router.put("/projects/{project_key}", response_model=ProjectRead)
def edit_project(project_key: str, data: CatalogInput, db: DB):
    project = find_option(db, ProjectOption, project_key)
    name = " ".join(data.name.split())
    key = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not key or len(key) > 40:
        raise HTTPException(status_code=422, detail="Use a project name that produces 1–40 English letters, digits, or underscores.")
    with db.no_autoflush:
        db.execute(update(Campaign).where(Campaign.project == project_key).values(project=key, updated_at=datetime.now(timezone.utc)))
    project.key = key
    project.name = name
    return persist(db, project)

@router.delete("/projects/{project_key}", status_code=204)
def delete_project(project_key: str, db: DB):
    project = find_option(db, ProjectOption, project_key)
    if db.scalar(select(Campaign.id).where(Campaign.project == project_key).limit(1)) is not None:
        raise HTTPException(status_code=409, detail="This project is used by campaigns. Reassign or delete those campaigns first.")
    db.delete(project)
    db.commit()
    return Response(status_code=204)
