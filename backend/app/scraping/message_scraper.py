"""Connect message and tone analysis to the app scraping workflow."""

import json
from .message_analysis_config import MIN_WORDS
from .message_analysis import calculate_features, has_enough_content, render_page


def scrape_message_page(campaign):
    """Adapt the original renderer to the application's saved evidence."""
    from datetime import datetime, timezone
    from app.schemas.automation import ScrapedPage
    from app.scraping.capture import capture_evidence_sync
    from app.scraping.public_urls import validate_public_url

    validate_public_url(str(campaign.url))
    source = render_page(str(campaign.url), capture=capture_evidence_sync)
    return ScrapedPage(
        source=campaign,
        title=source["page_title"],
        headline=source["headline"],
        text=source["text"],
        headings=source["headings"],
        paragraphs=source["paragraphs"],
        bullets=source["bullet_lists"],
        bullet_list_count=len(source["bullet_lists"]),
        tables=source.get("tables", []),
        metadata={
            "collector": "function_messages",
            "artifact_id": source["artifact_id"],
            "final_url": source["final_url"],
            "message_source": json.dumps(source, ensure_ascii=False),
        },
        scraped_at=datetime.now(timezone.utc),
        warnings=["Keyword-based message and tone suggestions require human review."]
        + (
            []
            if has_enough_content(source)
            else [
                f"Fewer than {MIN_WORDS} words; no message or tone scores calculated."
            ]
        ),
    )


def label_message_page(campaign, scraped_data):
    """Map original scores to existing fields; retain the original formulas."""
    from app.schemas.automation import FeatureSuggestions
    from app.schemas.features import FeatureInput
    from app.scraping.feature_labels import collected_feature_values

    source = json.loads(scraped_data.metadata["message_source"])
    values = collected_feature_values(scraped_data).model_dump(exclude_unset=True)
    if has_enough_content(source):
        features = calculate_features(source)
        features.pop("raw_scores")
        values["word_count"] = features.pop("words")
        # Script: high = feature-focused. App: high = benefit-focused.
        features["feature_vs_benefit_focus"] = 6 - features["feature_vs_benefit_focus"]
        if features["message_focus"] == "None":
            features["message_focus"] = None
        values.update(features)
    return FeatureSuggestions(
        values=FeatureInput(**values),
        warnings=scraped_data.warnings,
    )
