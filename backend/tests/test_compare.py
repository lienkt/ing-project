from test_campaigns import client


def add_page(client, bank, category="current_account"):
    response = client.post(
        "/api/campaigns",
        json={
            "bank_name": bank,
            "project": category,
            "campaign_url": f"https://example.com/{category}",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_comparison_multiple_pages_and_real_values(client):
    first = add_page(client, "ING")
    second = add_page(client, "KBC")
    client.put(
        f"/api/campaigns/{first}/features",
        json={
            "word_count": 120,
            "paragraph_count": 8,
            "text_density": 2,
            "price_visible": False,
            "cta_count": 0,
            "bank_type": "Traditional",
            "product_name": "Account A",
            "language": "Dutch",
            "capture_date": "2026-09-15",
        },
    )
    client.put(f"/api/campaigns/{second}/features", json={"text_density": 5})
    client.post(
        f"/api/campaigns/{second}/features/complete", json={"confirm_incomplete": True}
    )
    response = client.get(
        "/api/compare", params={"product_category": "current_account"}
    )
    assert response.status_code == 200
    pages = {page["campaign_id"]: page for page in response.json()["pages"]}
    assert set(pages) == {first, second}
    a = pages[first]
    assert a["product_name"] == "Account A"
    assert a["bank_type"] == "Traditional"
    assert a["language"] == "Dutch"
    assert a["capture_date"] == "2026-09-15"
    assert a["product_category"] == "current_account"
    assert a["page_url"] == "https://example.com/current_account"
    assert a["labeling_status"] == "In Progress"
    assert a["features"]["word_count"] == 120
    assert a["features"]["average_paragraph_length"] == 15
    assert a["features"]["price_visible"] is False
    assert a["features"]["cta_count"] == 0
    assert a["features"]["visual_intensity"] is None
    assert pages[second]["features"]["text_density"] == 5
    assert pages[second]["labeling_status"] == "Completed"


def test_comparison_filters_category_ids_and_banks(client):
    first = add_page(client, "ING")
    second = add_page(client, "ING")
    third = add_page(client, "KBC")
    other_category = add_page(client, "ING", "mortgage")
    params = [
        ("product_category", "current_account"),
        ("campaign_ids", first),
        ("campaign_ids", second),
        ("campaign_ids", third),
        ("campaign_ids", other_category),
        ("bank_names", "ing"),
    ]
    pages = client.get("/api/compare", params=params).json()["pages"]
    assert [page["campaign_id"] for page in pages] == [first, second]
    assert all(page["product_category"] == "current_account" for page in pages)
    assert (
        client.get(
            "/api/compare",
            params={
                "product_category": "current_account",
                "campaign_ids": other_category,
            },
        ).json()["pages"]
        == []
    )


def test_comparison_missing_features_and_empty_selection(client):
    campaign_id = add_page(client, "KBC")
    page = client.get(
        "/api/compare", params={"product_category": "current_account"}
    ).json()["pages"][0]
    assert page["campaign_id"] == campaign_id
    assert page["features"] is None
    assert page["labeling_status"] == "Not Started"
    assert page["product_name"] is None
    assert page["capture_date"] is None
    assert (
        client.get("/api/compare", params={"product_category": "mortgage"}).json()[
            "pages"
        ]
        == []
    )
    assert (
        client.get(
            "/api/compare",
            params={"product_category": "current_account", "campaign_ids": 999999},
        ).json()["pages"]
        == []
    )
    assert client.get("/api/compare").status_code == 422
    assert (
        client.get("/api/compare", params={"product_category": ""}).status_code == 422
    )
