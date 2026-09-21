"""One latest import attempt per source, and one current proposal per campaign."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class SourceImport(Base):
    __tablename__ = "source_imports"
    source_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[str] = mapped_column(String(20))
    engine: Mapped[str] = mapped_column(String(100))
    is_demo: Mapped[bool] = mapped_column(Boolean)
    page: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FeatureProposal(Base):
    __tablename__ = "feature_proposals"
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True
    )
    token: Mapped[str] = mapped_column(String(36))
    engine: Mapped[str] = mapped_column(String(100))
    is_demo: Mapped[bool] = mapped_column(Boolean)
    values: Mapped[dict] = mapped_column(JSON)
    warnings: Mapped[list] = mapped_column(JSON)
    baseline: Mapped[dict] = mapped_column(JSON)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PageCapture(Base):
    """Immutable evidence for one successful capture; labels remain separate."""

    __tablename__ = "page_captures"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserSource(Base):
    """User-added source metadata, retained independently of capture attempts."""

    __tablename__ = "user_sources"
    source_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True)
    definition: Mapped[dict] = mapped_column(JSON)


class DeletedSource(Base):
    """Remove configured sources from the active list without deleting evidence."""

    __tablename__ = "deleted_sources"
    source_id: Mapped[str] = mapped_column(String(120), primary_key=True)
