"""Google / Microsoft ID-token verification helpers (no heavy SDK required)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from urllib.parse import quote
from typing import Any

from django.conf import settings
from django.core.cache import cache


class SocialAuthError(Exception):
    pass


def _http_get_json(url: str, timeout: int = 12) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "WorkTaskMe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SocialAuthError(f"Token verification failed ({exc.code}).") from exc
    except Exception as exc:  # pragma: no cover
        raise SocialAuthError("Could not reach identity provider.") from exc


def verify_google_id_token(id_token: str) -> dict[str, Any]:
    client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "") or ""
    if not client_id:
        raise SocialAuthError("Google sign-in is not configured.")
    data = _http_get_json(
        f"https://oauth2.googleapis.com/tokeninfo?id_token={quote(id_token, safe='')}"
    )
    aud = data.get("aud") or data.get("azp")
    if aud != client_id:
        raise SocialAuthError("Google token audience mismatch.")
    if data.get("email_verified") not in (True, "true", "1"):
        raise SocialAuthError("Google email is not verified.")
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise SocialAuthError("Google account has no email.")
    return {
        "email": email,
        "first_name": data.get("given_name") or "",
        "last_name": data.get("family_name") or "",
        "provider": "google",
        "sub": data.get("sub") or "",
    }


def _microsoft_jwks() -> dict[str, Any]:  # kept for diagnostics / future use
    tenant = getattr(settings, "MICROSOFT_OAUTH_TENANT", "common") or "common"
    cache_key = f"ms_jwks_{tenant}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    jwks = _http_get_json(
        f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    )
    cache.set(cache_key, jwks, 3600)
    return jwks


def verify_microsoft_id_token(id_token: str) -> dict[str, Any]:
    """
    Verify Microsoft ID token using PyJWT + JWKS.
    Requires MICROSOFT_OAUTH_CLIENT_ID in settings.
    """
    client_id = getattr(settings, "MICROSOFT_OAUTH_CLIENT_ID", "") or ""
    if not client_id:
        raise SocialAuthError("Microsoft sign-in is not configured.")

    try:
        import jwt
        from jwt import PyJWKClient
    except ImportError as exc:  # pragma: no cover
        raise SocialAuthError("PyJWT is required for Microsoft sign-in.") from exc

    tenant = getattr(settings, "MICROSOFT_OAUTH_TENANT", "common") or "common"
    jwks_url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    jwks_client = PyJWKClient(jwks_url)
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            options={"verify_iss": False},  # multi-tenant issuers vary
        )
    except Exception as exc:
        raise SocialAuthError(f"Invalid Microsoft token: {exc}") from exc

    email = (
        (payload.get("email") or payload.get("preferred_username") or "")
        .strip()
        .lower()
    )
    if not email or "@" not in email:
        raise SocialAuthError("Microsoft account has no email.")
    name = (payload.get("name") or "").strip()
    parts = name.split(" ", 1) if name else ["", ""]
    return {
        "email": email,
        "first_name": payload.get("given_name") or (parts[0] if parts else ""),
        "last_name": payload.get("family_name")
        or (parts[1] if len(parts) > 1 else ""),
        "provider": "microsoft",
        "sub": payload.get("oid") or payload.get("sub") or "",
    }
