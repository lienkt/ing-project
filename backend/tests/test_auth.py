"""Authentication tests use local RSA keys; no Keycloak or network required."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import auth
from app.core.config import settings
from app.main import app


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "oidc_issuer", "https://identity.test/realms/banking")
    monkeypatch.setattr(settings, "oidc_audience", "banking-api")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        auth,
        "jwks_client",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key=key.public_key())
        ),
    )
    probe = FastAPI(dependencies=[Depends(auth.authorize)])

    @probe.api_route("/api/campaigns", methods=["GET", "POST"])
    def resource():
        return {"ok": True}

    def token(roles=None, **changes):
        now = datetime.now(timezone.utc)
        claims = {
            "sub": "user",
            "iss": settings.oidc_issuer,
            "aud": settings.oidc_audience,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "typ": "Bearer",
            "realm_access": {"roles": roles or []},
        }
        claims.update(changes)
        return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm='RS256')}"}

    return TestClient(probe), token


def test_missing_and_malformed_token(secured):
    client, _ = secured
    for headers in ({}, {"Authorization": "Bearer broken"}):
        response = client.get("/api/campaigns", headers=headers)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "changes",
    [
        {"aud": "wrong"},
        {"iss": "https://wrong.test"},
        {"exp": 1},
        {"typ": "ID"},
        {"sub": None},
    ],
)
def test_invalid_claims(secured, changes):
    client, token = secured
    assert (
        client.get("/api/campaigns", headers=token(["admin"], **changes)).status_code
        == 401
    )


def test_roles_and_methods(secured):
    client, token = secured
    assert client.get("/api/campaigns", headers=token()).status_code == 403
    assert client.get("/api/campaigns", headers=token(["viewer"])).status_code == 200
    for method in ("POST",):
        assert (
            client.request(
                method, "/api/campaigns", headers=token(["viewer"])
            ).status_code
            == 403
        )
        assert (
            client.request(
                method, "/api/campaigns", headers=token(["admin"])
            ).status_code
            == 200
        )


def test_all_application_api_routes_are_protected(secured):
    with TestClient(app) as client:
        for path, definition in app.openapi()["paths"].items():
            if path.startswith("/api/"):
                path = (
                    path.replace("{campaign_id}", "1")
                    .replace("{bank_id}", "1")
                    .replace("{project_key}", "test")
                    .replace("{source_id}", "test")
                    .replace("{capture_id}", "test")
                    .replace("{artifact}", "dom.json")
                )
                for method in definition:
                    assert client.request(method, path).status_code == 401, (
                        method,
                        path,
                    )
        assert client.get("/health").status_code == 200


def test_local_mode(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", False)
    probe = FastAPI(dependencies=[Depends(auth.authorize)])

    @probe.post("/api/campaigns")
    def resource():
        return {"ok": True}

    assert TestClient(probe).post("/api/campaigns").status_code == 200


def test_configured_role_and_direct_write_api(secured, monkeypatch):
    client, token = secured
    from app.core.permissions import load_policy

    policy = load_policy().model_copy(deep=True)
    policy.roles["editor"] = ["workspace.read", "campaigns.write"]
    monkeypatch.setattr(auth, "load_policy", lambda: policy)
    assert client.post("/api/campaigns", headers=token(["editor"])).status_code == 200
    assert client.post("/api/campaigns", headers=token(["unknown"])).status_code == 403
    with TestClient(app) as real_client:
        # Rejected before database access, even when a user calls APIs directly.
        assert (
            real_client.delete(
                "/api/campaigns/1", headers=token(["editor"])
            ).status_code
            == 403
        )
        result = real_client.get("/api/auth/permissions", headers=token(["editor"]))
        assert result.status_code == 200
        assert result.json() == {"permissions": ["campaigns.write", "workspace.read"]}


def test_unmapped_endpoint_is_denied(secured):
    _, token = secured
    probe = FastAPI(dependencies=[Depends(auth.authorize)])

    @probe.post("/api/new-action")
    def action():
        return {"ok": True}

    assert (
        TestClient(probe).post("/api/new-action", headers=token(["admin"])).status_code
        == 403
    )


def test_permission_policy_covers_all_api_endpoints():
    from app.core.permissions import load_policy

    policy = load_policy()
    endpoints = {
        f"{method.upper()} {path}"
        for path, definition in app.openapi()["paths"].items()
        if path.startswith("/api/")
        for method in definition
    }
    assert set(policy.api) == endpoints


def test_policy_rejects_unknown_permission():
    from app.core.permissions import PermissionPolicy, load_policy
    from pydantic import ValidationError

    data = load_policy().model_dump()
    data["roles"]["editor"] = ["typo.permission"]
    with pytest.raises(ValidationError):
        PermissionPolicy.model_validate(data)


def test_multiple_roles_combine_grants(secured, monkeypatch):
    client, token = secured
    from app.core.permissions import load_policy

    policy = load_policy().model_copy(deep=True)
    policy.roles["writer"] = ["campaigns.write"]
    monkeypatch.setattr(auth, "load_policy", lambda: policy)
    headers = token(["viewer", "writer", "unknown"])
    assert client.get("/api/campaigns", headers=headers).status_code == 200
    assert client.post("/api/campaigns", headers=headers).status_code == 200


def test_admin_has_no_implicit_bypass(secured, monkeypatch):
    client, token = secured
    from app.core.permissions import load_policy

    policy = load_policy().model_copy(deep=True)
    policy.roles["admin"] = ["workspace.read"]
    monkeypatch.setattr(auth, "load_policy", lambda: policy)
    assert client.post("/api/campaigns", headers=token(["admin"])).status_code == 403
