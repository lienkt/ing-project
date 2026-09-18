from datetime import datetime
from enum import Enum
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

from app.schemas.automation import campaign_information, stored_page
from app.scraping.dispatcher import scraping_support
from app.auto_labeling.dispatcher import auto_label_support
from app.models.collection import SourceImport, FeatureProposal
from app.models.features import CampaignFeature, FEATURE_FIELDS, missing_fields


class Project(str, Enum):
    credit_card = "credit_card"
    savings_account = "savings_account"
    current_account = "current_account"
    personal_loan = "personal_loan"
    mortgage = "mortgage"
    insurance = "insurance"
    investment = "investment"
    other = "other"


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    bank_name: Mapped[str] = mapped_column(String(120), index=True)
    project: Mapped[str] = mapped_column(String(40), index=True)
    campaign_url: Mapped[str] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    details: Mapped["CampaignDetails | None"] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )
    evaluation: Mapped["Evaluation | None"] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )

    features: Mapped["CampaignFeature | None"] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )

    source_import: Mapped["SourceImport | None"] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )
    proposal: Mapped["FeatureProposal | None"] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )

    @property
    def automation(self):
        info = campaign_information(self)
        return {
            "scraping": scraping_support(info),
            "auto_labeling": auto_label_support(info, stored_page(self)),
        }

    @property
    def collection(self):
        record = self.source_import
        if not record:
            return None
        source = (record.page or {}).get("source", {})
        return {
            "source_id": record.source_id,
            "status": record.status,
            "scraped_at": (record.page or {}).get("scraped_at"),
            "is_demo": record.is_demo,
            "engine": record.engine,
            "product_name": source.get("product_name"),
            "language": source.get("language"),
        }

    @property
    def has_suggestions(self) -> bool:
        return self.proposal is not None and not self.proposal.reviewed

    @property
    def labeling_status(self) -> str:
        return self.features.labeling_status if self.features else "Not Started"

    @property
    def labeling_progress(self) -> int:
        return round(
            100
            * (len(FEATURE_FIELDS) - len(missing_fields(self.features)))
            / len(FEATURE_FIELDS)
        )

    @property
    def labeling_updated_at(self) -> datetime | None:
        return self.features.updated_at if self.features else None

    @property
    def status(self) -> str:
        if self.evaluation:
            return "Evaluated"
        if self.details and any(getattr(self.details, key) for key in DETAIL_FIELDS):
            return "Details Added"
        return "Basic Info"


DETAIL_FIELDS = [
    "campaign_name",
    "headline",
    "subheadline",
    "main_message",
    "cta_text",
    "notes",
    "text_density",
    "tone",
    "feature_vs_benefit",
    "emotional_vs_rational",
    "customer_vs_product_focus",
]


class CampaignDetails(Base):
    __tablename__ = "campaign_details"
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True
    )
    campaign_name: Mapped[str | None] = mapped_column(String(300))
    headline: Mapped[str | None] = mapped_column(Text)
    subheadline: Mapped[str | None] = mapped_column(Text)
    main_message: Mapped[str | None] = mapped_column(Text)
    cta_text: Mapped[str | None] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    text_density: Mapped[str | None] = mapped_column(String(40))
    tone: Mapped[str | None] = mapped_column(String(120))
    feature_vs_benefit: Mapped[str | None] = mapped_column(String(40))
    emotional_vs_rational: Mapped[str | None] = mapped_column(String(40))
    customer_vs_product_focus: Mapped[str | None] = mapped_column(String(40))


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = tuple(
        CheckConstraint(f"{field} BETWEEN 1 AND 5", name=f"ck_{field}")
        for field in [
            "clarity_score",
            "visual_score",
            "benefit_score",
            "cta_score",
            "overall_score",
        ]
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), unique=True
    )
    source: Mapped[str] = mapped_column(
        String(40), default="manual", server_default="manual"
    )
    clarity_score: Mapped[int]
    visual_score: Mapped[int]
    benefit_score: Mapped[int]
    cta_score: Mapped[int]
    overall_score: Mapped[int]
    evaluation_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
