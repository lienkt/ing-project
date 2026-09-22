"""Check scraping_config.py and dispatch the matching scraping function."""

from app.schemas.automation import (
    CampaignInformation,
    FeatureSuggestions,
    ManualRequired,
    ScrapedPage,
    SourceDefinition,
    build_case_key,
)
from app.scraping import scraping_config


def _handler(campaign, step):
    key = build_case_key(
        campaign.bank,
        campaign.product_category,
        campaign.product_name,
        campaign.language,
    )
    return scraping_config.AUTO_SUPPORT.get(key, {}).get(step)


def has_auto_labels(campaign):
    return _handler(campaign, "label") is not None


def scraping_support(campaign):
    function = _handler(campaign, "scrape")
    available = function is not None
    return {
        "supported": function is not None,
        "available": available,
        "message": "Manual scraping required" if function is None else None,
    }


def scrape_campaign(campaign: SourceDefinition) -> ScrapedPage | ManualRequired:
    function = _handler(campaign, "scrape")
    if function is None:
        return ManualRequired(
            message="Automatic scraping is not available. Manual scraping required."
        )
    result = ScrapedPage.model_validate(function(campaign).model_dump())
    if result.source != campaign:
        raise ValueError("Scraping function returned inconsistent source")
    return result


def auto_label_support(campaign: CampaignInformation, page: ScrapedPage | None):
    function = _handler(campaign, "label")
    ready = (
        page is not None
        and page.success
        and str(page.source.url).split("#")[0] == str(campaign.url).split("#")[0]
    )
    available = function is not None and ready
    message = (
        "Manual labeling required"
        if function is None
        else "Valid scraped data required"
        if not ready
        else None
    )
    return {
        "supported": function is not None,
        "available": available,
        "message": message,
    }


def auto_label_campaign(
    campaign: CampaignInformation, scraped_data: ScrapedPage | None
) -> FeatureSuggestions | ManualRequired:
    function = _handler(campaign, "label")
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
    return result
