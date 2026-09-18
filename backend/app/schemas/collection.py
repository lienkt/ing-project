from datetime import datetime
from typing import Literal
from pydantic import Field
from app.schemas.campaign import Schema
from app.schemas.features import FeatureInput
from app.schemas.automation import SourceDefinition


class SourceView(SourceDefinition):
    scraping: dict[str, bool | str | None]
    import_status: str = "Ready"
    campaign_id: int | None = None
    error: str | None = None
    attempted_at: datetime | None = None


class CatalogResponse(Schema):
    sources: list[SourceView]
    banks: list[str]
    categories: list[str]
    data_mode: str


class ScrapeInput(Schema):
    recapture: bool = False
    source_ids: list[str] = Field(min_length=1, max_length=50)


class ImportResult(Schema):
    supported: bool = False
    message: str | None = None
    source_id: str
    status: Literal["success", "existing", "failed", "manual_required"]
    campaign_id: int | None = None
    error: str | None = None


class BatchResponse(Schema):
    results: list[ImportResult]


class ProposalRead(Schema):
    campaign_id: int
    token: str
    engine: str
    is_demo: bool
    values: dict[str, str | int | bool | None]
    warnings: list[str]
    reviewed: bool
    created_at: datetime


class ReviewInput(Schema):
    token: str
    values: FeatureInput
