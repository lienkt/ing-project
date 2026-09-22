import json
import pytest
from test_campaigns import client
from app.services.source_catalog import load_sources
from app.scraping.dispatcher import scraping_support
from app.scraping import message_scraper as main_messages

CASES = [s for s in load_sources() if "-messages-" in s.source_id]


def content(text=None):
    return dict(
        page_title="Product",
        headline="Your future",
        text=text if text is not None else "Your family enjoys flexible savings. " * 20,
        value_proposition="Save for your family.",
        headings=["Your future"],
        paragraphs=["Flexible savings."],
        bullet_lists=["Save today"],
        tables=["Fee 0"],
        artifact_id="test-artifact",
        final_url="https://example.com/",
    )


@pytest.mark.parametrize("source", CASES, ids=lambda s: s.source_id)
def test_message_capture_labels_and_compare(client, monkeypatch, source):
    data = content()
    monkeypatch.setattr(
        "app.scraping.public_urls.validate_public_url", lambda url: None
    )
    monkeypatch.setattr(main_messages, "render_page", lambda *a, **kw: data)
    assert scraping_support(source)["available"]
    assert not scraping_support(source.model_copy(update={"language": "Other"}))[
        "supported"
    ]
    payload = {"source_ids": [source.source_id], "mode": "scrape_and_label"}
    result = client.post("/api/scraping/run", json=payload).json()["results"][0]
    assert result["status"] == "success", result
    cid = result["campaign_id"]
    base = f"/api/campaigns/{cid}/features"
    values = client.get(base).json()["features"]
    expected = main_messages.calculate_features(data)
    for key in (
        "tone_formality",
        "tone_friendliness",
        "tone_persuasiveness",
        "emotional_vs_rational",
        "customer_vs_product_focus",
        "main_message",
        "value_proposition",
    ):
        assert values[key] == expected[key]
    assert (
        values["feature_vs_benefit_focus"] == 6 - expected["feature_vs_benefit_focus"]
    )
    assert (
        values["source"] == "automatic" and values["labeling_status"] == "In Progress"
    )
    captures = client.get(f"/api/scraping/campaigns/{cid}/captures").json()
    assert captures[0]["has_screenshot"]
    assert json.loads(captures[0]["page"]["metadata"]["message_source"]) == data
    pages = client.get(
        "/api/compare", params={"product_category": source.product_category}
    ).json()["pages"]
    assert (
        next(p for p in pages if p["campaign_id"] == cid)["features"]["tone_formality"]
        == expected["tone_formality"]
    )
    client.put(base, json={"tone_formality": 5})
    client.post(base + "/complete", json={"confirm_incomplete": True})
    before = client.get(base).json()["features"]
    assert (
        client.post("/api/scraping/run", json={**payload, "recapture": True}).json()[
            "results"
        ][0]["status"]
        == "success"
    )
    assert client.get(base).json()["features"] == before


def test_capture_only_and_short_text(client, monkeypatch):
    monkeypatch.setattr(
        "app.scraping.public_urls.validate_public_url", lambda url: None
    )
    monkeypatch.setattr(main_messages, "render_page", lambda *a, **kw: content("Short"))
    monkeypatch.setattr(
        main_messages, "calculate_features", lambda *a: pytest.fail("Must not score")
    )
    payload = {"source_ids": [CASES[0].source_id], "mode": "capture_only"}
    result = client.post("/api/scraping/run", json=payload).json()["results"][0]
    assert result["status"] == "success"
    base = f"/api/campaigns/{result['campaign_id']}/features"
    assert client.get(base).json()["features"] is None
    assert (
        client.post(
            "/api/scraping/run",
            json={**payload, "mode": "scrape_and_label", "recapture": True},
        ).json()["results"][0]["status"]
        == "success"
    )
    assert client.get(base).json()["features"] is None
