from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload, raiseload
from app.models.campaign import Campaign
from app.schemas.compare import ComparisonPage, ComparisonRead
from app.schemas.features import FeatureRead


def compare_campaigns(db: Session, product_category: str,
                      campaign_ids: list[int] | None = None,
                      bank_names: list[str] | None = None) -> ComparisonRead:
    # Always constrain category, even when IDs from other categories are supplied.
    query = (select(Campaign)
             .options(raiseload("*"), selectinload(Campaign.features))
             .where(Campaign.project == product_category)
             .order_by(func.lower(Campaign.bank_name), Campaign.id))
    if campaign_ids:
        query = query.where(Campaign.id.in_(campaign_ids))
    if bank_names:
        query = query.where(func.lower(Campaign.bank_name).in_(
            [name.strip().lower() for name in bank_names]))
    pages = []
    for campaign in db.scalars(query):
        feature = campaign.features
        pages.append(ComparisonPage(
            campaign_id=campaign.id,
            bank_name=campaign.bank_name,
            bank_type=feature.bank_type if feature else None,
            product_name=feature.product_name if feature else None,
            product_category=campaign.project,
            page_url=campaign.campaign_url,
            language=feature.language if feature else None,
            capture_date=feature.capture_date if feature else None,
            labeling_status=campaign.labeling_status,
            features=FeatureRead.model_validate(feature) if feature else None,
        ))
    return ComparisonRead(product_category=product_category, pages=pages)
