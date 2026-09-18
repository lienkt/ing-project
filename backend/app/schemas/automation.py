"""Shared automation data shapes and exact normalization. No engines or registries."""

from datetime import datetime
from typing import Literal
from pydantic import Field, HttpUrl, ValidationError, field_validator, model_validator
from app.schemas.campaign import Schema
from app.schemas.features import FeatureInput


def build_case_key(
    bank: str, category: str, product: str, language: str
) -> tuple[str, str, str, str]:
    """Case/whitespace normalization only; never fuzzy-match products."""
    clean = lambda value: " ".join(value.strip().casefold().split())
    lang = clean(language)
    lang = {"english": "en", "dutch": "nl", "french": "fr"}.get(lang, lang)
    return clean(bank), clean(category.replace("_", " ")), clean(product), lang


class CampaignInformation(Schema):
    campaign_id: int | None = None  # Catalog sources have no Dataset ID before import.
    bank: str
    product_category: str
    product_name: str
    language: str
    url: HttpUrl = Field(max_length=2048)


def campaign_information(campaign) -> CampaignInformation:
    source = (
        (campaign.source_import.page or {}).get("source", {})
        if campaign.source_import
        else {}
    )
    features = campaign.features
    return CampaignInformation(
        campaign_id=campaign.id,
        bank=campaign.bank_name,
        product_category=campaign.project,
        product_name=(features.product_name if features else None)
        or source.get("product_name", ""),
        language=(features.language if features else None)
        or source.get("language", ""),
        url=campaign.campaign_url,
    )


class ManualRequired(Schema):
    supported: bool = False
    status: Literal["manual_required"] = "manual_required"
    message: str


class SourceDefinition(CampaignInformation):
    source_id: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9_-]+$")
    bank: str = Field(min_length=1, max_length=120)
    bank_type: Literal["Traditional", "Challenger", "Neobank"]
    country: str = "Belgium"
    product_name: str = Field(min_length=1, max_length=300)
    product_category: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9_]+$")
    language: Literal["Dutch", "French", "English", "Other"]
    page_type: str = Field(min_length=1, max_length=100)
    url: HttpUrl = Field(max_length=2048)
    is_example: bool = False

    @field_validator("language", mode="before")
    @classmethod
    def language_name(cls, value):
        if isinstance(value, str):
            return {
                "en": "English",
                "english": "English",
                "nl": "Dutch",
                "dutch": "Dutch",
                "fr": "French",
                "french": "French",
                "other": "Other",
            }.get(value.strip().casefold(), value)
        return value


class ScrapedPage(Schema):
    source: SourceDefinition
    title: str
    text: str
    headline: str | None = None
    bullets: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    bullet_list_count: int | None = Field(default=None, ge=0)
    headings: list[str] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    buttons: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    scraped_at: datetime
    success: bool = True
    is_demo: bool
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class FeatureSuggestions(Schema):
    values: FeatureInput
    is_demo: bool
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def observations_only(self):
        if "labeling_notes" in self.values.model_fields_set:
            raise ValueError("Suggestions must not replace analyst notes")
        if not any(
            v is not None for v in self.values.model_dump(exclude_unset=True).values()
        ):
            raise ValueError("At least one non-null suggestion is required")
        return self


def stored_page(campaign) -> ScrapedPage | None:
    record = campaign.source_import
    if not record or not record.page:
        return None
    try:
        return ScrapedPage.model_validate(record.page)
    except ValidationError:
        return None
