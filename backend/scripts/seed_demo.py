"""Insert clearly marked synthetic demo campaigns; run from backend/."""

import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import Field, TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.core.config import settings
from app.models.campaign import Campaign, CampaignDetails
from app.models.catalog import Bank, ProjectOption
from app.models.features import CampaignFeature
from app.models.collection import SourceImport, FeatureProposal
from app.schemas.automation import SourceDefinition
from app.scraping.functions import scrape_demo_page
from app.auto_labeling.functions import label_demo_page
from app.schemas.campaign import CampaignCreate
from app.schemas.features import FeatureInput


class DemoCampaign(CampaignCreate):
    auto_stage: Literal["pending", "reviewed"] | None = None
    campaign_name: str = Field(max_length=300)
    labeling_status: Literal["Not Started", "In Progress", "Completed"]
    features: FeatureInput | None


def seed_demo(db: Session, rows: list[DemoCampaign]) -> int:
    """Add missing demo URLs, preserving all existing records and edits."""
    added = 0
    for row in rows:
        url = str(row.campaign_url)
        if (
            db.scalar(select(Campaign.id).where(Campaign.campaign_url == url))
            is not None
        ):
            continue
        if db.get(ProjectOption, row.project) is None:
            db.add(
                ProjectOption(
                    key=row.project, name=row.project.replace("_", " ").title()
                )
            )
        if (
            db.scalar(
                select(Bank.id).where(Bank.normalized_name == row.bank_name.lower())
            )
            is None
        ):
            db.add(Bank(name=row.bank_name, normalized_name=row.bank_name.lower()))
        campaign = Campaign(
            bank_name=row.bank_name, project=row.project, campaign_url=url
        )
        campaign.details = CampaignDetails(
            campaign_name=row.campaign_name,
            notes="Synthetic demo record. The source URL is a placeholder, not a bank webpage.",
        )
        if row.features is not None:
            campaign.features = CampaignFeature(
                **row.features.model_dump(),
                labeling_status=row.labeling_status,
                source="manual",
            )
        if row.auto_stage:
            source = SourceDefinition(
                source_id=f"demo-auto-{url.rsplit('/', 1)[-1]}",
                bank=row.bank_name,
                bank_type="Neobank" if row.bank_name == "Revolut" else "Traditional",
                product_name=row.campaign_name,
                product_category=row.project,
                language="English",
                page_type="Product Page",
                url=url,
                is_example=True,
            )
            page = scrape_demo_page(source)
            suggestions = label_demo_page(source, page)
            reviewed = row.auto_stage == "reviewed"
            if reviewed:
                values = {
                    **suggestions.values.model_dump(exclude_unset=True),
                    **(
                        row.features.model_dump(exclude_unset=True)
                        if row.features
                        else {}
                    ),
                }
                campaign.features = CampaignFeature(
                    **values,
                    labeling_status=row.labeling_status,
                    source="manual_override",
                )
            else:
                campaign.features = None
            campaign.source_import = SourceImport(
                source_id=source.source_id,
                source_url=url,
                status="Scraped",
                engine="demo",
                is_demo=True,
                page=page.model_dump(mode="json"),
                attempted_at=page.scraped_at,
            )
            campaign.proposal = FeatureProposal(
                token=str(uuid4()),
                engine="demo",
                is_demo=True,
                values=suggestions.values.model_dump(mode="json", exclude_unset=True),
                warnings=suggestions.warnings,
                baseline={"url": url, "features": None},
                reviewed=reviewed,
            )
        db.add(campaign)
        db.flush()
        added += 1
    return added


def main():
    if settings.data_mode != "demo":
        raise SystemExit(
            "Demo seeding requires DATA_MODE=demo. The real database was not modified."
        )
    path = Path(__file__).resolve().parents[1] / "data" / "demo_campaigns.json"
    rows = TypeAdapter(list[DemoCampaign]).validate_python(json.loads(path.read_text()))
    with SessionLocal.begin() as db:
        added = seed_demo(db, rows)
    print(f"Added {added} synthetic demo campaign(s). Existing records preserved.")
    print("Open Compare → Current Account. Demo values are not research evidence.")


if __name__ == "__main__":
    main()
