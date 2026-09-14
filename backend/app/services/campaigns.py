from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.catalog import ProjectOption
from app.models.campaign import Campaign, CampaignDetails, Evaluation
from app.schemas.campaign import CampaignCreate, DetailsInput, EvaluationInput

def get_campaign(db: Session, campaign_id: int) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

def list_campaigns(db: Session, bank_name: str | None, project: str | None):
    query = select(Campaign).order_by(Campaign.created_at.desc(), Campaign.id.desc())
    if bank_name:
        query = query.where(func.lower(Campaign.bank_name) == bank_name.lower())
    if project:
        query = query.where(Campaign.project == project)
    return db.scalars(query).all()

def create_campaign(db: Session, data: CampaignCreate) -> Campaign:
    validate_project(db, data.project)
    campaign = Campaign(bank_name=data.bank_name, project=data.project, campaign_url=str(data.campaign_url))
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

def update_details(db: Session, campaign_id: int, data: DetailsInput) -> Campaign:
    campaign = get_campaign(db, campaign_id)
    if campaign.details is None:
        campaign.details = CampaignDetails()
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign.details, key, value or None)
    campaign.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(campaign)
    return campaign

def save_evaluation(db: Session, campaign_id: int, data: EvaluationInput) -> Evaluation:
    campaign = get_campaign(db, campaign_id)
    if campaign.evaluation is None:
        campaign.evaluation = Evaluation(source="manual")
    for key, value in data.model_dump().items():
        setattr(campaign.evaluation, key, value)
    campaign.updated_at = campaign.evaluation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(campaign)
    return campaign.evaluation


def update_basic(db: Session, campaign_id: int, data: CampaignCreate) -> Campaign:
    campaign = get_campaign(db, campaign_id)
    validate_project(db, data.project)
    campaign.bank_name = data.bank_name
    campaign.project = data.project
    campaign.campaign_url = str(data.campaign_url)
    campaign.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(campaign)
    return campaign


def validate_project(db: Session, key: str) -> None:
    if db.get(ProjectOption, key) is None:
        raise HTTPException(status_code=422, detail="Select an existing project or add it first.")
