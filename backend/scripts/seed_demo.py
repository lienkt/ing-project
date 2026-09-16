"""Insert clearly marked synthetic demo campaigns; run from backend/."""
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.core.config import settings
from app.models.campaign import Campaign, CampaignDetails
from app.models.catalog import Bank, ProjectOption
from app.models.features import CampaignFeature
from app.schemas.campaign import CampaignCreate
from app.schemas.features import FeatureInput


class DemoCampaign(CampaignCreate):
    campaign_name: str = Field(max_length=300)
    labeling_status: Literal["Not Started", "In Progress", "Completed"]
    features: FeatureInput | None


def seed_demo(db: Session, rows: list[DemoCampaign]) -> int:
    """Add missing demo URLs, preserving all existing records and edits."""
    added = 0
    for row in rows:
        url = str(row.campaign_url)
        if db.scalar(select(Campaign.id).where(Campaign.campaign_url == url)) is not None:
            continue
        if db.get(ProjectOption, row.project) is None:
            db.add(ProjectOption(key=row.project, name=row.project.replace('_', ' ').title()))
        if db.scalar(select(Bank.id).where(Bank.normalized_name == row.bank_name.lower())) is None:
            db.add(Bank(name=row.bank_name, normalized_name=row.bank_name.lower()))
        campaign = Campaign(bank_name=row.bank_name, project=row.project, campaign_url=url)
        campaign.details = CampaignDetails(campaign_name=row.campaign_name,
            notes="Synthetic demo record. The source URL is a placeholder, not a bank webpage.")
        if row.features is not None:
            campaign.features = CampaignFeature(**row.features.model_dump(),
                labeling_status=row.labeling_status, source="manual")
        db.add(campaign)
        db.flush()
        added += 1
    return added


def main():
    if settings.data_mode != "demo":
        raise SystemExit("Demo seeding requires DATA_MODE=demo. The real database was not modified.")
    path = Path(__file__).resolve().parents[1] / 'data' / 'demo_campaigns.json'
    rows = TypeAdapter(list[DemoCampaign]).validate_python(json.loads(path.read_text()))
    with SessionLocal.begin() as db:
        added = seed_demo(db, rows)
    print(f'Added {added} synthetic demo campaign(s). Existing records preserved.')
    print('Open Compare → Current Account. Demo values are not research evidence.')


if __name__ == '__main__':
    main()
