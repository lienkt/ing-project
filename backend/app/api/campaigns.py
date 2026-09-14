from typing import Annotated
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.campaign import Project
from app.schemas.campaign import CampaignCreate, CampaignRead, DetailsInput, EvaluationInput, EvaluationRead
from app.services import campaigns

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])
DB = Annotated[Session, Depends(get_db)]

@router.post("", response_model=CampaignRead, status_code=201)
def create(data: CampaignCreate, db: DB):
    return campaigns.create_campaign(db, data)

@router.get("", response_model=list[CampaignRead])
def list_all(db: DB, bank_name: str | None = None, project: str | None = None):
    return campaigns.list_campaigns(db, bank_name, project)

@router.get("/{campaign_id}", response_model=CampaignRead)
def get_one(campaign_id: int, db: DB):
    return campaigns.get_campaign(db, campaign_id)

@router.put("/{campaign_id}/details", response_model=CampaignRead)
def details(campaign_id: int, data: DetailsInput, db: DB):
    return campaigns.update_details(db, campaign_id, data)

@router.post("/{campaign_id}/evaluation", response_model=EvaluationRead)
def evaluate(campaign_id: int, data: EvaluationInput, db: DB):
    return campaigns.save_evaluation(db, campaign_id, data)


@router.put("/{campaign_id}", response_model=CampaignRead)
def update(campaign_id: int, data: CampaignCreate, db: DB):
    return campaigns.update_basic(db, campaign_id, data)


@router.delete("/{campaign_id}", status_code=204)
def delete(campaign_id: int, db: DB):
    campaign = campaigns.get_campaign(db, campaign_id)
    db.delete(campaign)
    db.commit()
    return Response(status_code=204)
