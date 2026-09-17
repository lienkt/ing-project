"""Algorithm boundary: no HTTP clients or persistence here."""
from datetime import datetime
from typing import Literal
from pydantic import Field, HttpUrl
from app.schemas.campaign import Schema


class SourceDefinition(Schema):
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


class ScrapedPage(Schema):
    source: SourceDefinition
    title: str
    text: str
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
