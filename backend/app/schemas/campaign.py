from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")

class CampaignCreate(Schema):
    bank_name: str = Field(min_length=1, max_length=120)
    project: str = Field(min_length=1, max_length=40)
    campaign_url: HttpUrl = Field(max_length=2048)

class DetailsInput(Schema):
    campaign_name: str | None = Field(default=None, max_length=300)
    headline: str | None = Field(default=None, max_length=10000)
    subheadline: str | None = Field(default=None, max_length=10000)
    main_message: str | None = Field(default=None, max_length=10000)
    cta_text: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=10000)
    text_density: Literal["low", "medium", "high"] | None = None
    tone: str | None = Field(default=None, max_length=120)
    feature_vs_benefit: Literal["feature_focused", "balanced", "benefit_focused"] | None = None
    emotional_vs_rational: Literal["emotional", "balanced", "rational"] | None = None
    customer_vs_product_focus: Literal["customer_focused", "balanced", "product_focused"] | None = None

Score = Annotated[int, Field(strict=True, ge=1, le=5)]

class EvaluationInput(Schema):
    clarity_score: Score
    visual_score: Score
    benefit_score: Score
    cta_score: Score
    overall_score: Score
    evaluation_notes: str | None = Field(default=None, max_length=10000)

class EvaluationRead(EvaluationInput):
    id: int
    campaign_id: int
    source: str
    created_at: datetime
    updated_at: datetime

class CampaignRead(Schema):
    id: int
    bank_name: str
    project: str = Field(min_length=1, max_length=40)
    campaign_url: str
    created_at: datetime
    updated_at: datetime
    status: str
    details: DetailsInput | None
    evaluation: EvaluationRead | None
