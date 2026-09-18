"""Check config.py and dispatch the matching scraping function."""

from app.core.config import settings
from app.schemas.automation import (
    build_case_key,
    SourceDefinition,
    ScrapedPage,
    ManualRequired,
)
from app.scraping.functions import scrape_demo_page
from app.scraping import config


def scraping_support(campaign):
    function = config.SCRAPING_SUPPORT.get(
        build_case_key(
            campaign.bank,
            campaign.product_category,
            campaign.product_name,
            campaign.language,
        )
    )
    demo = function is scrape_demo_page
    available = function is not None and (not demo or settings.data_mode == "demo")
    return {
        "supported": function is not None,
        "available": available,
        "is_demo": demo,
        "message": "Manual scraping required"
        if function is None
        else "Switch to the demo database"
        if not available
        else None,
    }


def scrape_campaign(campaign: SourceDefinition) -> ScrapedPage | ManualRequired:
    function = config.SCRAPING_SUPPORT.get(
        build_case_key(
            campaign.bank,
            campaign.product_category,
            campaign.product_name,
            campaign.language,
        )
    )
    if function is None:
        return ManualRequired(
            message="Automatic scraping is not available. Manual scraping required."
        )
    if function is scrape_demo_page and settings.data_mode != "demo":
        raise ValueError("Demo scraping requires DATA_MODE=demo")
    if campaign.is_example and function is not scrape_demo_page:
        raise ValueError(
            "Replace example URLs with verified sources before real scraping"
        )
    result = ScrapedPage.model_validate(function(campaign).model_dump())
    if result.source != campaign or result.is_demo != (function is scrape_demo_page):
        raise ValueError(
            "Scraping function returned inconsistent source or demo provenance"
        )
    return result
