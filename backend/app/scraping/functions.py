"""Scraping functions receive SourceDefinition and return ScrapedPage.

Input includes campaign_id (None before import), bank, product_category,
product_name, language, URL, and stable source ID. Keep page.source unchanged.
Return success=False with error, or raise, on failure. Do not write to the DB.
Only finished functions belong in config.py; placeholders remain unregistered.
"""

from datetime import datetime, timezone
from app.schemas.automation import SourceDefinition, ScrapedPage


def scrape_demo_page(campaign: SourceDefinition) -> ScrapedPage:
    """DEMO ONLY: synthetic content, no website access. Config limits supported cases."""
    paragraphs = [
        f"Demo content for {campaign.bank}. This is not collected website evidence.",
        "Explore example account features and everyday banking benefits.",
    ]
    return ScrapedPage(
        source=campaign,
        title=f"Demo {campaign.product_name}",
        text="\n".join(paragraphs),
        paragraphs=paragraphs,
        headings=[campaign.product_name, "Example benefits"],
        buttons=["Open account", "Learn more"],
        sections=["Overview", "Benefits"],
        scraped_at=datetime.now(timezone.utc),
        is_demo=True,
        warnings=["DEMO ONLY: synthetic content; no webpage was fetched."],
    )


def scrape_ing_current_account_lion_en(campaign: SourceDefinition) -> ScrapedPage:
    """TODO: teammate implements collection. Register only after tests pass."""
    raise NotImplementedError("ING Lion Account scraping is not implemented")
