from datetime import date
from typing import Literal
from app.schemas.campaign import Schema
from app.schemas.features import FeatureRead


class ComparisonPage(Schema):
    campaign_id: int
    bank_name: str
    bank_type: str | None
    product_name: str | None
    product_category: str
    page_url: str
    language: str | None
    capture_date: date | None
    labeling_status: Literal["Not Started", "In Progress", "Completed"]
    features: FeatureRead | None


class ComparisonRead(Schema):
    product_category: str
    pages: list[ComparisonPage]
