from datetime import datetime, timezone
import pytest
from test_campaigns import client
from app.schemas.automation import ScrapedPage
from app.services.source_catalog import load_sources


def add_source(client, monkeypatch):
    monkeypatch.setattr(
        "app.scraping.public_urls.validate_public_url", lambda url: None
    )
    response = client.post(
        "/api/scraping/sources",
        json={
            "bank": "ING",
            "product_name": "New product",
            "product_category": "current_account",
            "language": "English",
            "url": "https://public.example/product",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def fake_capture(source):
    return ScrapedPage(
        source=source,
        title="Product",
        text="Public product content",
        headings=["Product"],
        paragraphs=["Public product content"],
        bullets=["Benefit"],
        tables=["Fee 0"],
        metadata={"artifact_id": "test-artifact"},
        scraped_at=datetime.now(timezone.utc),
        is_demo=False,
    )


def test_added_source_generic_capture_history_and_manual_labels(client, monkeypatch):
    source = add_source(client, monkeypatch)
    rows = client.get("/api/scraping/sources").json()["sources"]
    row = next(s for s in rows if s["source_id"] == source["source_id"])
    assert row["capture_available"] and not row["scraping"]["supported"]
    monkeypatch.setattr("app.scraping.functions.capture_generic_page", fake_capture)

    def no_labels(*args):
        pytest.fail("Capture-only must not generate labels")

    monkeypatch.setattr("app.services.collection.auto_label_campaign", no_labels)
    payload = {"source_ids": [source["source_id"]]}
    result = client.post("/api/scraping/run", json=payload).json()["results"][0]
    assert result["status"] == "success"
    base = f"/api/campaigns/{result['campaign_id']}"
    assert client.get(base + "/features").json()["features"] is None
    assert client.get(base).json()["labeling_status"] == "Not Started"
    assert client.get(base).json()["collection"]["engine"] == "generic"
    page = client.get("/api/compare?product_category=current_account").json()["pages"][
        0
    ]
    assert page["product_name"] == "New product" and page["language"] == "English"
    assert (
        client.post("/api/scraping/run", json=payload).json()["results"][0]["status"]
        == "existing"
    )
    client.put(base + "/features", json={"word_count": 42})
    client.post(base + "/features/complete", json={"confirm_incomplete": True})
    before = client.get(base + "/features").json()["features"]
    result2 = client.post(
        "/api/scraping/run", json={**payload, "recapture": True, "mode": "capture_only"}
    ).json()["results"][0]
    assert result2["campaign_id"] == result["campaign_id"]
    assert client.get(base + "/features").json()["features"] == before
    captures = client.get(
        f"/api/scraping/campaigns/{result['campaign_id']}/captures"
    ).json()
    assert len(captures) == 2 and captures[0]["has_screenshot"]
    assert captures[0]["page"]["metadata"]["capture_mode"] == "capture_only"

    def fail(source):
        raise ValueError("Browser failed")

    monkeypatch.setattr("app.scraping.functions.capture_generic_page", fail)
    assert (
        client.post("/api/scraping/run", json={**payload, "recapture": True}).json()[
            "results"
        ][0]["status"]
        == "failed"
    )
    assert (
        client.get(f"/api/scraping/campaigns/{result['campaign_id']}/captures").json()
        == captures
    )


def test_specialized_capture_only_skips_labels(client, monkeypatch):
    source = next(s for s in load_sources() if s.source_id == "ing-youth-account-en")
    monkeypatch.setattr("app.services.collection.scrape_campaign", fake_capture)
    monkeypatch.setattr(
        "app.scraping.functions.capture_generic_page",
        lambda s: pytest.fail("Must use specialized scraper"),
    )
    monkeypatch.setattr(
        "app.services.collection.auto_label_campaign",
        lambda *args: pytest.fail("Must skip labels"),
    )
    result = client.post(
        "/api/scraping/run",
        json={"source_ids": [source.source_id], "mode": "capture_only"},
    ).json()["results"][0]
    assert result["status"] == "success"
    assert (
        client.get(f"/api/campaigns/{result['campaign_id']}/features").json()[
            "features"
        ]
        is None
    )


def test_source_validation_duplicates_and_modes(client, monkeypatch):
    source = add_source(client, monkeypatch)
    fields = {
        k: source[k]
        for k in ("bank", "product_name", "product_category", "language", "url")
    }
    assert client.post("/api/scraping/sources", json=fields).status_code == 409
    assert (
        client.post(
            "/api/scraping/sources",
            json={**fields, "url": "https://public.example/other", "product_name": " "},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/scraping/sources", json={**fields, "bank": "Unknown"}
        ).status_code
        == 422
    )
    result = client.post(
        "/api/scraping/run",
        json={"source_ids": [source["source_id"]], "mode": "scrape_and_label"},
    ).json()["results"][0]
    assert result["status"] == "manual_required"
    assert (
        client.post(
            "/api/scraping/run",
            json={"source_ids": [source["source_id"]], "mode": "invalid"},
        ).status_code
        == 422
    )


@pytest.mark.parametrize("address", ["127.0.0.1", "10.1.2.3", "169.254.169.254", "::1"])
def test_public_capture_rejects_private_addresses(monkeypatch, address):
    from app.scraping.public_urls import validate_public_url

    monkeypatch.setattr(
        "socket.getaddrinfo", lambda *args, **kwargs: [(0, 0, 0, "", (address, 80))]
    )
    with pytest.raises(ValueError, match="public website"):
        validate_public_url("https://example.com")


def test_generic_adapter_allows_empty_text_evidence(monkeypatch):
    from app.scraping.functions import capture_generic_page

    source = next(
        s for s in load_sources() if s.source_id == "ing-youth-account-en"
    ).model_copy(update={"product_name": "Other"})
    monkeypatch.setattr(
        "app.scraping.public_urls.validate_public_url", lambda url: None
    )

    async def collect(source, config, extractor, allow_empty):
        assert allow_empty and config.public_only and not config.clean_page
        return fake_capture(source).model_copy(update={"text": ""})

    monkeypatch.setattr("app.scraping.functions._collect_page", collect)
    page = capture_generic_page(source)
    assert page.metadata["collector"] == "playwright-generic-v1"
    assert any("No readable text" in warning for warning in page.warnings)


@pytest.mark.parametrize("configured", [False, True])
def test_delete_source_preserves_dataset_evidence(client, monkeypatch, configured):
    source_id = (
        "ing-youth-account-en"
        if configured else add_source(client, monkeypatch)["source_id"]
    )
    monkeypatch.setattr("app.services.collection.scrape_campaign", fake_capture)
    monkeypatch.setattr("app.scraping.functions.capture_generic_page", fake_capture)
    result = client.post(
        "/api/scraping/run",
        json={"source_ids": [source_id], "mode": "capture_only"},
    ).json()["results"][0]
    assert result["status"] == "success"
    campaign_id = result["campaign_id"]
    base = f"/api/campaigns/{campaign_id}"
    client.put(base + "/features", json={"word_count": 42})
    client.post(base + "/features/complete", json={"confirm_incomplete": True})
    before = client.get(base).json()
    features = client.get(base + "/features").json()
    capture_url = f"/api/scraping/campaigns/{campaign_id}/captures"
    captures = client.get(capture_url).json()
    assert client.delete(f"/api/scraping/sources/{source_id}").status_code == 204
    assert source_id not in {
        s["source_id"] for s in client.get("/api/scraping/sources").json()["sources"]
    }
    assert client.get(base).json() == before
    assert client.get(base + "/features").json() == features
    assert client.get(capture_url).json() == captures
    assert client.delete(f"/api/scraping/sources/{source_id}").status_code == 404
