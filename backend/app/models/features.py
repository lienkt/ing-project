from datetime import date, datetime
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base

class CampaignFeature(Base):
    __tablename__ = "campaign_features"
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True)
    bank_type: Mapped[str | None] = mapped_column(String(20))
    product_name: Mapped[str | None] = mapped_column(String(300))
    language: Mapped[str | None] = mapped_column(String(20))
    capture_date: Mapped[date | None] = mapped_column(Date)
    headline_length: Mapped[int | None] = mapped_column(Integer)

    @property
    def average_paragraph_length(self) -> float | None:
        if self.word_count is None or not self.paragraph_count:
            return None
        return self.word_count / self.paragraph_count

    word_count: Mapped[int | None] = mapped_column(Integer)
    heading_count: Mapped[int | None] = mapped_column(Integer)
    paragraph_count: Mapped[int | None] = mapped_column(Integer)
    bullet_list_count: Mapped[int | None] = mapped_column(Integer)
    text_density: Mapped[int | None] = mapped_column(Integer)
    text_style: Mapped[str | None] = mapped_column(String(300))
    information_complexity: Mapped[int | None] = mapped_column(Integer)
    tone_formality: Mapped[int | None] = mapped_column(Integer)
    tone_friendliness: Mapped[int | None] = mapped_column(Integer)
    tone_persuasiveness: Mapped[int | None] = mapped_column(Integer)
    emotional_vs_rational: Mapped[int | None] = mapped_column(Integer)
    customer_vs_product_focus: Mapped[int | None] = mapped_column(Integer)
    feature_vs_benefit_focus: Mapped[int | None] = mapped_column(Integer)
    message_focus: Mapped[str | None] = mapped_column(String(300))
    main_message: Mapped[str | None] = mapped_column(Text)
    value_proposition: Mapped[str | None] = mapped_column(Text)
    image_count: Mapped[int | None] = mapped_column(Integer)
    has_hero_image: Mapped[bool | None] = mapped_column(Boolean)
    hero_image_size: Mapped[str | None] = mapped_column(String(300))
    people_present: Mapped[bool | None] = mapped_column(Boolean)
    people_image_count: Mapped[int | None] = mapped_column(Integer)
    product_present: Mapped[bool | None] = mapped_column(Boolean)
    illustration_present: Mapped[bool | None] = mapped_column(Boolean)
    icon_count: Mapped[int | None] = mapped_column(Integer)
    video_count: Mapped[int | None] = mapped_column(Integer)
    animation_present: Mapped[bool | None] = mapped_column(Boolean)
    visual_style: Mapped[str | None] = mapped_column(String(300))
    visual_intensity: Mapped[int | None] = mapped_column(Integer)
    dominant_colour: Mapped[str | None] = mapped_column(String(300))
    number_of_major_colours: Mapped[int | None] = mapped_column(Integer)
    brand_colour_dominance: Mapped[int | None] = mapped_column(Integer)
    colour_contrast: Mapped[int | None] = mapped_column(Integer)
    design_complexity: Mapped[int | None] = mapped_column(Integer)
    visual_consistency: Mapped[int | None] = mapped_column(Integer)
    attention_focus: Mapped[str | None] = mapped_column(String(300))
    section_count: Mapped[int | None] = mapped_column(Integer)
    page_length: Mapped[str | None] = mapped_column(String(300))
    hero_section_present: Mapped[bool | None] = mapped_column(Boolean)
    content_pattern: Mapped[str | None] = mapped_column(String(300))
    card_layout_present: Mapped[bool | None] = mapped_column(Boolean)
    accordion_present: Mapped[bool | None] = mapped_column(Boolean)
    comparison_table_present: Mapped[bool | None] = mapped_column(Boolean)
    navigation_anchor_present: Mapped[bool | None] = mapped_column(Boolean)
    layout_clarity: Mapped[int | None] = mapped_column(Integer)
    scannability: Mapped[int | None] = mapped_column(Integer)
    cta_count: Mapped[int | None] = mapped_column(Integer)
    primary_cta_text: Mapped[str | None] = mapped_column(String(300))
    cta_above_fold: Mapped[bool | None] = mapped_column(Boolean)
    cta_repeated: Mapped[bool | None] = mapped_column(Boolean)
    cta_prominence: Mapped[int | None] = mapped_column(Integer)
    cta_type: Mapped[str | None] = mapped_column(String(300))
    price_visible: Mapped[bool | None] = mapped_column(Boolean)
    price_prominence: Mapped[int | None] = mapped_column(Integer)
    promotion_present: Mapped[bool | None] = mapped_column(Boolean)
    benefit_count: Mapped[int | None] = mapped_column(Integer)
    feature_count: Mapped[int | None] = mapped_column(Integer)
    trust_message_present: Mapped[bool | None] = mapped_column(Boolean)
    security_message_present: Mapped[bool | None] = mapped_column(Boolean)
    convenience_message_present: Mapped[bool | None] = mapped_column(Boolean)
    digital_message_present: Mapped[bool | None] = mapped_column(Boolean)
    sustainability_message_present: Mapped[bool | None] = mapped_column(Boolean)
    main_value_driver: Mapped[str | None] = mapped_column(String(300))
    labeling_notes: Mapped[str | None] = mapped_column(Text)
    labeling_status: Mapped[str] = mapped_column(String(20), default="Not Started", server_default="Not Started")
    source: Mapped[str] = mapped_column(String(20), default="manual", server_default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("bank_type IN ('Traditional', 'Challenger', 'Neobank')", name="ck_cf_bank_type"),
        CheckConstraint("language IN ('Dutch', 'French', 'English', 'Other')", name="ck_cf_language"),
        CheckConstraint("headline_length >= 0", name="ck_cf_headline_length"),
        CheckConstraint('word_count >= 0', name="ck_cf_word_count"),
        CheckConstraint('heading_count >= 0', name="ck_cf_heading_count"),
        CheckConstraint('paragraph_count >= 0', name="ck_cf_paragraph_count"),
        CheckConstraint('bullet_list_count >= 0', name="ck_cf_bullet_list_count"),
        CheckConstraint('text_density BETWEEN 1 AND 5', name="ck_cf_text_density"),
        CheckConstraint("text_style IN ('Concise', 'Balanced', 'Detailed')", name="ck_cf_text_style"),
        CheckConstraint('information_complexity BETWEEN 1 AND 5', name="ck_cf_information_complexity"),
        CheckConstraint('tone_formality BETWEEN 1 AND 5', name="ck_cf_tone_formality"),
        CheckConstraint('tone_friendliness BETWEEN 1 AND 5', name="ck_cf_tone_friendliness"),
        CheckConstraint('tone_persuasiveness BETWEEN 1 AND 5', name="ck_cf_tone_persuasiveness"),
        CheckConstraint('emotional_vs_rational BETWEEN 1 AND 5', name="ck_cf_emotional_vs_rational"),
        CheckConstraint('customer_vs_product_focus BETWEEN 1 AND 5', name="ck_cf_customer_vs_product_focus"),
        CheckConstraint('feature_vs_benefit_focus BETWEEN 1 AND 5', name="ck_cf_feature_vs_benefit_focus"),
        CheckConstraint("message_focus IN ('Product', 'Feature', 'Benefit', 'Lifestyle', 'Price')", name="ck_cf_message_focus"),
        CheckConstraint('image_count >= 0', name="ck_cf_image_count"),
        CheckConstraint("hero_image_size IN ('None', 'Small', 'Medium', 'Large', 'Full-width')", name="ck_cf_hero_image_size"),
        CheckConstraint('people_image_count >= 0', name="ck_cf_people_image_count"),
        CheckConstraint('icon_count >= 0', name="ck_cf_icon_count"),
        CheckConstraint('video_count >= 0', name="ck_cf_video_count"),
        CheckConstraint("visual_style IN ('Photography', 'Illustration', '3D', 'UI-Product', 'Mixed')", name="ck_cf_visual_style"),
        CheckConstraint('visual_intensity BETWEEN 1 AND 5', name="ck_cf_visual_intensity"),
        CheckConstraint('number_of_major_colours >= 0', name="ck_cf_number_of_major_colours"),
        CheckConstraint('brand_colour_dominance BETWEEN 1 AND 5', name="ck_cf_brand_colour_dominance"),
        CheckConstraint('colour_contrast BETWEEN 1 AND 5', name="ck_cf_colour_contrast"),
        CheckConstraint('design_complexity BETWEEN 1 AND 5', name="ck_cf_design_complexity"),
        CheckConstraint('visual_consistency BETWEEN 1 AND 5', name="ck_cf_visual_consistency"),
        CheckConstraint("attention_focus IN ('Text', 'Image', 'CTA', 'Product', 'Mixed')", name="ck_cf_attention_focus"),
        CheckConstraint('section_count >= 0', name="ck_cf_section_count"),
        CheckConstraint("page_length IN ('Short', 'Medium', 'Long')", name="ck_cf_page_length"),
        CheckConstraint("content_pattern IN ('Text-first', 'Image-first', 'Alternating', 'Cards', 'Mixed')", name="ck_cf_content_pattern"),
        CheckConstraint('layout_clarity BETWEEN 1 AND 5', name="ck_cf_layout_clarity"),
        CheckConstraint('scannability BETWEEN 1 AND 5', name="ck_cf_scannability"),
        CheckConstraint('cta_count >= 0', name="ck_cf_cta_count"),
        CheckConstraint('cta_prominence BETWEEN 1 AND 5', name="ck_cf_cta_prominence"),
        CheckConstraint("cta_type IN ('Apply', 'Buy', 'Open', 'Learn', 'Contact', 'Calculate', 'Other')", name="ck_cf_cta_type"),
        CheckConstraint('price_prominence BETWEEN 1 AND 5', name="ck_cf_price_prominence"),
        CheckConstraint('benefit_count >= 0', name="ck_cf_benefit_count"),
        CheckConstraint('feature_count >= 0', name="ck_cf_feature_count"),
        CheckConstraint("main_value_driver IN ('Price', 'Convenience', 'Security', 'Flexibility', 'Lifestyle', 'Digital', 'Service', 'Other')", name="ck_cf_main_value_driver"),
        CheckConstraint("labeling_status IN ('Not Started', 'In Progress', 'Completed')", name="ck_cf_labeling_status"),
        CheckConstraint("source IN ('manual', 'automatic', 'manual_override')", name="ck_cf_source"),
    )


FEATURE_FIELDS = tuple(column.name for column in CampaignFeature.__table__.columns
                       if column.name not in {"campaign_id", "labeling_notes", "labeling_status", "source", "created_at", "updated_at"}) + ("average_paragraph_length",)


def missing_fields(record: CampaignFeature | None) -> list[str]:
    return [key for key in FEATURE_FIELDS if getattr(record, key, None) in (None, "")]
