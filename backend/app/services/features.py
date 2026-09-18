from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.campaign import Campaign
from app.models.features import CampaignFeature, FEATURE_FIELDS, missing_fields
from app.schemas.features import FeatureInput, FeatureRead
from app.services.campaigns import get_campaign


def feature_response(db: Session, campaign_id: int):
    campaign = get_campaign(db, campaign_id)
    record = campaign.features
    missing = missing_fields(record)
    return {
        "campaign": campaign,
        "features": record,
        "labeling_status": record.labeling_status if record else "Not Started",
        "progress": round(
            100 * (len(FEATURE_FIELDS) - len(missing)) / len(FEATURE_FIELDS)
        ),
        "missing_fields": missing,
    }


def locked_campaign(db: Session, campaign_id: int):
    # Serialize saves for a campaign, including the first insert on PostgreSQL.
    campaign = db.scalar(
        select(Campaign).where(Campaign.id == campaign_id).with_for_update()
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def save_features(db: Session, campaign_id: int, data: FeatureInput):
    campaign = locked_campaign(db, campaign_id)
    if campaign.features is None:
        campaign.features = CampaignFeature()
    record = campaign.features
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, None if value == "" else value)
    record.labeling_status = "In Progress"
    record.source = (
        "manual_override"
        if record.source in ("automatic", "manual_override")
        else "manual"
    )
    record.updated_at = campaign.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(campaign)
    return feature_response(db, campaign_id)


def complete_features(db: Session, campaign_id: int, confirm_incomplete: bool):
    campaign = locked_campaign(db, campaign_id)
    record = campaign.features
    if record is None or len(missing_fields(record)) == len(FEATURE_FIELDS):
        raise HTTPException(
            status_code=422, detail="Label at least one feature before completing."
        )
    FeatureRead.model_validate(record)
    if missing_fields(record) and not confirm_incomplete:
        raise HTTPException(
            status_code=422,
            detail="Some features are unset. Confirm incomplete labeling to complete this record.",
        )
    record.labeling_status = "Completed"
    record.updated_at = campaign.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(campaign)
    return feature_response(db, campaign_id)
