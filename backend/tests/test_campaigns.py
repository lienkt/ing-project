import os
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.main import app

@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Use a migrated database, never create_all. TEST_DATABASE_URL must be a disposable DB.
    url = os.getenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    engine = create_engine(url)
    monkeypatch.setattr("app.database.session.engine", engine)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    def override():
        with Session(engine) as session:
            yield session
    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    command.downgrade(config, "base")
    engine.dispose()

BASIC = {"bank_name": "KBC", "project": "credit_card", "campaign_url": "https://example.com/credit-card"}
SCORES = {"clarity_score": 4, "visual_score": 5, "benefit_score": 3, "cta_score": 4, "overall_score": 2, "evaluation_notes": "Strong visuals"}

def create(client):
    response = client.post("/api/campaigns", json=BASIC)
    assert response.status_code == 201
    return response.json()

def test_create_campaign(client):
    campaign = create(client)
    assert campaign["status"] == "Basic Info"
    assert campaign["details"] is None
    assert campaign["evaluation"] is None
    assert client.get(f"/api/campaigns/{campaign['id']}").json() == campaign

def test_get_campaigns_and_filters(client):
    assert client.get("/api/campaigns").json() == []
    create(client)
    assert len(client.get("/api/campaigns", params={"bank_name": "kbc", "project": "credit_card"}).json()) == 1
    assert client.get("/api/campaigns", params={"project": "mortgage"}).json() == []
    assert client.get("/api/campaigns", params={"bank_name": "ING"}).json() == []

def test_update_details(client):
    campaign = create(client)
    url = f"/api/campaigns/{campaign['id']}/details"
    response = client.put(url, json={"headline": "Value for you", "text_density": "medium"})
    assert response.status_code == 200
    assert response.json()["status"] == "Details Added"
    assert client.put(url, json={"notes": "Updated"}).json()["details"]["headline"] == "Value for you"
    response = client.put(url, json={"headline": None, "text_density": None, "notes": " "})
    assert response.json()["status"] == "Basic Info"

def test_save_evaluation_and_update(client):
    campaign = create(client)
    url = f"/api/campaigns/{campaign['id']}/evaluation"
    result = client.post(url, json=SCORES)
    assert result.status_code == 200
    assert result.json()["source"] == "manual"
    assert result.json()["overall_score"] == 2  # no automatic average
    updated = client.post(url, json={**SCORES, "overall_score": 5})
    assert updated.json()["id"] == result.json()["id"]
    saved = client.get(f"/api/campaigns/{campaign['id']}").json()
    assert saved["status"] == "Evaluated"
    assert saved["evaluation"]["overall_score"] == 5

@pytest.mark.parametrize("field,value", [("bank_name", "  "), ("project", "invalid"), ("campaign_url", "javascript:alert(1)")])
def test_invalid_campaign(client, field, value):
    assert client.post("/api/campaigns", json={**BASIC, field: value}).status_code == 422

@pytest.mark.parametrize("score", [0, 6, 2.5, True, "3"])
def test_invalid_scores(client, score):
    campaign = create(client)
    assert client.post(f"/api/campaigns/{campaign['id']}/evaluation", json={**SCORES, "clarity_score": score}).status_code == 422

def test_not_found_and_invalid_details(client):
    assert client.get("/api/campaigns/9999").status_code == 404
    assert client.put("/api/campaigns/9999/details", json={}).status_code == 404
    assert client.post("/api/campaigns/9999/evaluation", json=SCORES).status_code == 404
    campaign = create(client)
    assert client.put(f"/api/campaigns/{campaign['id']}/details", json={"text_density": "huge"}).status_code == 422

@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"])
def test_health_and_cors(client, origin):
    assert client.get("/health").json() == {"status": "ok"}
    response = client.options("/api/campaigns", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_unknown_origin(client):
    response = client.options("/api/campaigns", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_edit_basic_after_evaluation_preserves_work(client):
    campaign = create(client)
    url = f"/api/campaigns/{campaign['id']}"
    client.put(f"{url}/details", json={"headline": "Original headline"})
    evaluation = client.post(f"{url}/evaluation", json=SCORES).json()
    updated = client.put(url, json={"bank_name": "ING", "project": "mortgage", "campaign_url": "https://example.com/mortgage"})
    assert updated.status_code == 200
    saved = client.get(url).json()
    assert saved["bank_name"] == "ING"
    assert saved["project"] == "mortgage"
    assert saved["campaign_url"] == "https://example.com/mortgage"
    assert saved["created_at"] == campaign["created_at"]
    assert saved["updated_at"] != campaign["updated_at"]
    assert saved["details"]["headline"] == "Original headline"
    assert saved["evaluation"] == evaluation
    assert saved["status"] == "Evaluated"
    edited = client.put(f"{url}/details", json={"headline": "Revised headline"}).json()
    assert edited["details"]["headline"] == "Revised headline"
    assert edited["evaluation"] == evaluation
    assert client.put(url, json={**BASIC, "bank_name": " "}).status_code == 422
    assert client.get(url).json()["bank_name"] == "ING"
    assert client.put("/api/campaigns/9999", json=BASIC).status_code == 404


def test_catalog_options_and_custom_campaign(client):
    assert any(b["name"] == "ING" for b in client.get("/api/banks").json())
    bank = client.post("/api/banks", json={"name": " Argenta "})
    assert bank.status_code == 201
    assert bank.json()["name"] == "Argenta"
    assert client.post("/api/banks", json={"name": "argenta"}).status_code == 409
    project = client.post("/api/projects", json={"name": "Business Loan"})
    assert project.status_code == 201
    assert project.json()["key"] == "business_loan"
    assert client.post("/api/projects", json={"name": "business loan"}).status_code == 409
    response = client.post("/api/campaigns", json={**BASIC, "bank_name": "Argenta", "project": "business_loan"})
    assert response.status_code == 201
    assert client.get(f"/api/campaigns/{response.json()['id']}").json()["project"] == "business_loan"
    assert len(client.get("/api/campaigns", params={"project": "business_loan"}).json()) == 1
    assert any(p["key"] == "business_loan" for p in client.get("/api/projects").json())

@pytest.mark.parametrize("path", ["banks", "projects"])
def test_catalog_invalid_names(client, path):
    assert client.post(f"/api/{path}", json={"name": " "}).status_code == 422
    assert client.post(f"/api/{path}", json={"name": "x" * 121}).status_code == 422


def test_delete_campaign_removes_children(client):
    from sqlalchemy import select
    from app.models.campaign import CampaignDetails, Evaluation
    campaign = create(client)
    url = f"/api/campaigns/{campaign['id']}"
    client.put(f"{url}/details", json={"headline": "Hello"})
    client.post(f"{url}/evaluation", json=SCORES)
    response = client.delete(url)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(url).status_code == 404
    assert client.get("/api/campaigns").json() == []
    with next(app.dependency_overrides[get_db]()) as db:
        assert db.scalar(select(CampaignDetails)) is None
        assert db.scalar(select(Evaluation)) is None
    assert client.delete(url).status_code == 404


def test_bank_edit_delete_and_linked_campaigns(client):
    campaign = create(client)
    bank = next(b for b in client.get("/api/banks").json() if b["name"] == "KBC")
    url = f"/api/banks/{bank['id']}"
    assert client.delete(url).status_code == 409
    assert client.put(url, json={"name": "ING"}).status_code == 409
    assert client.get(f"/api/campaigns/{campaign['id']}").json()["bank_name"] == "KBC"
    assert client.put(url, json={"name": "KBC Bank"}).status_code == 200
    assert client.get(f"/api/campaigns/{campaign['id']}").json()["bank_name"] == "KBC Bank"
    assert client.delete(url).status_code == 409
    client.delete(f"/api/campaigns/{campaign['id']}")
    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 404
    assert client.put(url, json={"name": "Missing"}).status_code == 404


def test_project_edit_delete_and_linked_campaigns(client):
    campaign = create(client)
    campaign_url = f"/api/campaigns/{campaign['id']}"
    client.put(f"{campaign_url}/details", json={"headline": "Keep this"})
    client.post(f"{campaign_url}/evaluation", json=SCORES)
    assert client.delete("/api/projects/credit_card").status_code == 409
    assert client.put("/api/projects/credit_card", json={"name": "Mortgage"}).status_code == 409
    assert client.get(campaign_url).json()["project"] == "credit_card"
    assert client.put("/api/projects/credit_card", json={"name": "Premium Card"}).status_code == 200
    saved = client.get(campaign_url).json()
    assert saved["project"] == "premium_card"
    assert saved["details"]["headline"] == "Keep this"
    assert saved["evaluation"]["overall_score"] == SCORES["overall_score"]
    assert client.delete("/api/projects/premium_card").status_code == 409
    assert client.put(campaign_url, json={**BASIC, "project": "mortgage"}).status_code == 200
    assert client.delete("/api/projects/premium_card").status_code == 204
    assert client.delete("/api/projects/premium_card").status_code == 404
    assert client.put("/api/projects/premium_card", json={"name": "Missing"}).status_code == 404
    assert client.put("/api/projects/mortgage", json={"name": " "}).status_code == 422


def test_delete_preflight(client):
    response = client.options("/api/campaigns/1", headers={"Origin": "http://localhost:5174", "Access-Control-Request-Method": "DELETE"})
    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]
