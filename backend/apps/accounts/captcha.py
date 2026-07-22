"""Bot protection: Google reCAPTCHA v2 or Cloudflare Turnstile."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from django.conf import settings


class CaptchaError(Exception):
    pass


def captcha_config() -> dict[str, Any]:
    provider = (getattr(settings, "CAPTCHA_PROVIDER", "") or "none").strip().lower()
    if provider == "recaptcha":
        site = getattr(settings, "RECAPTCHA_SITE_KEY", "") or ""
        secret = getattr(settings, "RECAPTCHA_SECRET_KEY", "") or ""
        return {
            "provider": "recaptcha" if site and secret else "none",
            "site_key": site if site and secret else "",
            "required": bool(site and secret),
        }
    if provider == "turnstile":
        site = getattr(settings, "TURNSTILE_SITE_KEY", "") or ""
        secret = getattr(settings, "TURNSTILE_SECRET_KEY", "") or ""
        return {
            "provider": "turnstile" if site and secret else "none",
            "site_key": site if site and secret else "",
            "required": bool(site and secret),
        }
    # Auto-detect from keys if provider not set
    if getattr(settings, "RECAPTCHA_SITE_KEY", "") and getattr(
        settings, "RECAPTCHA_SECRET_KEY", ""
    ):
        return {
            "provider": "recaptcha",
            "site_key": settings.RECAPTCHA_SITE_KEY,
            "required": True,
        }
    if getattr(settings, "TURNSTILE_SITE_KEY", "") and getattr(
        settings, "TURNSTILE_SECRET_KEY", ""
    ):
        return {
            "provider": "turnstile",
            "site_key": settings.TURNSTILE_SITE_KEY,
            "required": True,
        }
    return {"provider": "none", "site_key": "", "required": False}


def _post_form(url: str, data: dict[str, str], timeout: int = 12) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "WorkTaskMe/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise CaptchaError(f"Captcha provider error ({exc.code}).") from exc
    except Exception as exc:  # pragma: no cover
        raise CaptchaError("Could not reach captcha provider.") from exc


def verify_captcha_token(token: str | None, remote_ip: str | None = None) -> None:
    """
    Validate captcha token from the browser.
    - If captcha is not configured: require nothing (checkbox/honeypot still apply).
    - In DEBUG, token 'dev-bypass' is accepted when captcha is not configured.
    """
    cfg = captcha_config()
    token = (token or "").strip()

    if not cfg["required"]:
        if settings.DEBUG and token in ("", "dev-bypass"):
            return
        return

    if not token:
        raise CaptchaError("Please complete the captcha challenge.")

    if cfg["provider"] == "recaptcha":
        payload = {
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": token,
        }
        if remote_ip:
            payload["remoteip"] = remote_ip
        result = _post_form(
            "https://www.google.com/recaptcha/api/siteverify", payload
        )
        if not result.get("success"):
            raise CaptchaError("reCAPTCHA verification failed. Try again.")
        return

    if cfg["provider"] == "turnstile":
        payload = {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": token,
        }
        if remote_ip:
            payload["remoteip"] = remote_ip
        result = _post_form(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify", payload
        )
        if not result.get("success"):
            raise CaptchaError("Turnstile verification failed. Try again.")
        return

    raise CaptchaError("Captcha is misconfigured.")
