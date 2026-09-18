from datetime import date, datetime
from typing import Annotated, Literal
from pydantic import Field
from app.schemas.campaign import CampaignRead, Schema

Scale = Annotated[int, Field(strict=True, ge=1, le=5)]
Count = Annotated[int, Field(strict=True, ge=0, le=2147483647)]


class FeatureInput(Schema):
    bank_type: Literal["Traditional", "Challenger", "Neobank"] | None = None
    product_name: str | None = Field(default=None, max_length=300)
    language: Literal["Dutch", "French", "English", "Other"] | None = None
    capture_date: date | None = None
    headline_length: Count | None = None
    word_count: Count | None = None
    heading_count: Count | None = None
    paragraph_count: Count | None = None
    bullet_list_count: Count | None = None
    text_density: Scale | None = None
    text_style: Literal["Concise", "Balanced", "Detailed"] | None = None
    information_complexity: Scale | None = None
    tone_formality: Scale | None = None
    tone_friendliness: Scale | None = None
    tone_persuasiveness: Scale | None = None
    emotional_vs_rational: Scale | None = None
    customer_vs_product_focus: Scale | None = None
    feature_vs_benefit_focus: Scale | None = None
    message_focus: (
        Literal["Product", "Feature", "Benefit", "Lifestyle", "Price"] | None
    ) = None
    main_message: str | None = Field(default=None, max_length=10000)
    value_proposition: str | None = Field(default=None, max_length=10000)
    image_count: Count | None = None
    has_hero_image: Annotated[bool, Field(strict=True)] | None = None
    hero_image_size: (
        Literal["None", "Small", "Medium", "Large", "Full-width"] | None
    ) = None
    people_present: Annotated[bool, Field(strict=True)] | None = None
    people_image_count: Count | None = None
    product_present: Annotated[bool, Field(strict=True)] | None = None
    illustration_present: Annotated[bool, Field(strict=True)] | None = None
    icon_count: Count | None = None
    video_count: Count | None = None
    animation_present: Annotated[bool, Field(strict=True)] | None = None
    visual_style: (
        Literal["Photography", "Illustration", "3D", "UI-Product", "Mixed"] | None
    ) = None
    visual_intensity: Scale | None = None
    dominant_colour: str | None = Field(default=None, max_length=300)
    number_of_major_colours: Count | None = None
    brand_colour_dominance: Scale | None = None
    colour_contrast: Scale | None = None
    design_complexity: Scale | None = None
    visual_consistency: Scale | None = None
    attention_focus: Literal["Text", "Image", "CTA", "Product", "Mixed"] | None = None
    section_count: Count | None = None
    page_length: Literal["Short", "Medium", "Long"] | None = None
    hero_section_present: Annotated[bool, Field(strict=True)] | None = None
    content_pattern: (
        Literal["Text-first", "Image-first", "Alternating", "Cards", "Mixed"] | None
    ) = None
    card_layout_present: Annotated[bool, Field(strict=True)] | None = None
    accordion_present: Annotated[bool, Field(strict=True)] | None = None
    comparison_table_present: Annotated[bool, Field(strict=True)] | None = None
    navigation_anchor_present: Annotated[bool, Field(strict=True)] | None = None
    layout_clarity: Scale | None = None
    scannability: Scale | None = None
    cta_count: Count | None = None
    primary_cta_text: str | None = Field(default=None, max_length=300)
    cta_above_fold: Annotated[bool, Field(strict=True)] | None = None
    cta_repeated: Annotated[bool, Field(strict=True)] | None = None
    cta_prominence: Scale | None = None
    cta_type: (
        Literal["Apply", "Buy", "Open", "Learn", "Contact", "Calculate", "Other"] | None
    ) = None
    price_visible: Annotated[bool, Field(strict=True)] | None = None
    price_prominence: Scale | None = None
    promotion_present: Annotated[bool, Field(strict=True)] | None = None
    benefit_count: Count | None = None
    feature_count: Count | None = None
    trust_message_present: Annotated[bool, Field(strict=True)] | None = None
    security_message_present: Annotated[bool, Field(strict=True)] | None = None
    convenience_message_present: Annotated[bool, Field(strict=True)] | None = None
    digital_message_present: Annotated[bool, Field(strict=True)] | None = None
    sustainability_message_present: Annotated[bool, Field(strict=True)] | None = None
    main_value_driver: (
        Literal[
            "Price",
            "Convenience",
            "Security",
            "Flexibility",
            "Lifestyle",
            "Digital",
            "Service",
            "Other",
        ]
        | None
    ) = None
    labeling_notes: str | None = Field(default=None, max_length=10000)


class FeatureRead(FeatureInput):
    average_paragraph_length: float | None
    campaign_id: int
    labeling_status: Literal["Not Started", "In Progress", "Completed"]
    source: Literal["manual", "automatic", "manual_override"]
    created_at: datetime
    updated_at: datetime


class CompleteInput(Schema):
    confirm_incomplete: bool = False


class FeatureResponse(Schema):
    campaign: CampaignRead
    features: FeatureRead | None
    labeling_status: Literal["Not Started", "In Progress", "Completed"]
    progress: int
    missing_fields: list[str]
