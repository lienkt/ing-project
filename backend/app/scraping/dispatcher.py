"""Check config.py and dispatch the matching scraping function."""

from app.core.config import settings
from app.schemas.automation import (
    CampaignInformation,
    FeatureSuggestions,
    ManualRequired,
    ScrapedPage,
    SourceDefinition,
    build_case_key,
)
from app.scraping import config
from app.scraping.functions import scrape_demo_page
from app.scraping.labels import label_demo_page


def _scraping_function(campaign):
    """Use the same exact case lookup for availability and execution."""
    return config.SCRAPING_SUPPORT.get(
        build_case_key(
            campaign.bank,
            campaign.product_category,
            campaign.product_name,
            campaign.language,
        )
    )


def scraping_support(campaign):
    function = _scraping_function(campaign)
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
    function = _scraping_function(campaign)
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


def auto_label_support(campaign: CampaignInformation, page: ScrapedPage | None):
    function = config.AUTO_LABEL_SUPPORT.get(
        build_case_key(
            campaign.bank,
            campaign.product_category,
            campaign.product_name,
            campaign.language,
        )
    )
    demo = function is label_demo_page or bool(page and page.is_demo)
    ready = (
        page is not None
        and page.success
        and str(page.source.url).split("#")[0] == str(campaign.url).split("#")[0]
    )
    available = (
        function is not None and ready and (not demo or settings.data_mode == "demo")
    )
    message = (
        "Manual labeling required"
        if function is None
        else "Valid scraped data required"
        if not ready
        else "Switch to the demo database"
        if demo and settings.data_mode != "demo"
        else None
    )
    return {
        "supported": function is not None,
        "available": available,
        "is_demo": demo,
        "message": message,
    }


def auto_label_campaign(
    campaign: CampaignInformation, scraped_data: ScrapedPage | None
) -> FeatureSuggestions | ManualRequired:
    function = config.AUTO_LABEL_SUPPORT.get(
        build_case_key(
            campaign.bank,
            campaign.product_category,
            campaign.product_name,
            campaign.language,
        )
    )
    if function is None:
        return ManualRequired(
            message="Automatic labeling is not available. Manual labeling required."
        )
    support = auto_label_support(campaign, scraped_data)
    if not support["available"]:
        return ManualRequired(supported=True, message=str(support["message"]))
    result = FeatureSuggestions.model_validate(
        function(campaign, scraped_data).model_dump(exclude_unset=True)
    )
    if result.is_demo != (function is label_demo_page):
        raise ValueError("Label function returned inconsistent demo provenance")
    return result
