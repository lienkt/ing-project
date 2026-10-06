"""Keycloak access-token validation and API role enforcement."""

from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.permissions import load_policy

bearer = HTTPBearer(auto_error=False)


@lru_cache
def jwks_client(issuer: str):
    return jwt.PyJWKClient(f"{issuer}/protocol/openid-connect/certs", timeout=5)


def authorize(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    policy = load_policy()
    if not settings.auth_enabled:
        request.state.permissions = set(policy.permissions)
        return
    if not settings.oidc_issuer or not settings.oidc_audience:
        raise HTTPException(503, "Authentication is not configured")
    if credentials is None:
        raise HTTPException(
            401, "Login required", headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        key = jwks_client(settings.oidc_issuer).get_signing_key_from_jwt(
            credentials.credentials
        )
        claims = jwt.decode(
            credentials.credentials,
            key.key,
            algorithms=["RS256"],
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(503, "Identity provider unavailable") from None
    except jwt.PyJWTError:
        raise HTTPException(
            401,
            "Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    # Keycloak access tokens have typ=Bearer; ID tokens must not authorize APIs.
    if claims.get("typ") != "Bearer":
        raise HTTPException(
            401, "Access token required", headers={"WWW-Authenticate": "Bearer"}
        )
    access = claims.get("realm_access", {})
    roles = access.get("roles", []) if isinstance(access, dict) else []
    grants = (
        policy.grants([role for role in roles if isinstance(role, str)])
        if isinstance(roles, list)
        else set()
    )
    route = request.scope.get("route")
    endpoint = f"{request.method} {getattr(route, 'path', '')}"
    required = policy.api.get(endpoint)
    if required is None or required not in grants:
        raise HTTPException(403, "Permission denied")
    request.state.permissions = grants
