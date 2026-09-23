"""Connect message and tone analysis to the app scraping workflow."""

import json
from datetime import datetime, timezone

from app.schemas.automation import FeatureSuggestions, ScrapedPage
from app.schemas.features import FeatureInput
from app.scraping import capture, cta_analysis, public_urls
from app.scraping.feature_labels import collected_feature_values

from .message_analysis import calculate_features, has_enough_content, render_page
from .message_analysis_config import MIN_WORDS


def scrape_message_page(campaign):
    """Adapt the original renderer to the application's saved evidence."""

    public_urls.validate_public_url(str(campaign.url))

    cta_metadata = {}

    def capture_with_cta(page):
        artifact_id = capture.capture_evidence_sync(page)
        try:
            cta_metadata["cta_features"] = json.dumps(
                cta_analysis.extract_loaded_cta_features_sync(page)
            )
        except Exception:
            cta_metadata["cta_warning"] = (
                "CTA extraction failed; review CTA fields manually."
            )
        return artifact_id

    source = render_page(str(campaign.url), capture=capture_with_cta)
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
            **cta_metadata,
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
