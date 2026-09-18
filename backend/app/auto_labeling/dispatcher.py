"""Check config.py and dispatch the matching auto-label function."""

from app.core.config import settings
from app.schemas.automation import (
    build_case_key,
    CampaignInformation,
    ScrapedPage,
    FeatureSuggestions,
    ManualRequired,
)
from app.auto_labeling.functions import label_demo_page
from app.auto_labeling import config


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
