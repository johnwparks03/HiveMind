"""Shared client for the central API (Interface B). Adds the Bearer token and
refreshes on expiry; all stories that call central go through `request`.
"""
import time

import httpx

from app import config
from app.auth import session
from app.errors import ApiError


def _send(method: str, path: str, **kwargs) -> httpx.Response:
    if not config.CENTRAL_API_URL:
        raise ApiError(503, "service_unavailable",
                       "central service is not configured: set HIVEMIND_CENTRAL_API_URL in agent/.env",
                       {"missing": "HIVEMIND_CENTRAL_API_URL"})
    headers = {"Authorization": f"Bearer {session.access_token()}"}
    kwargs.setdefault("timeout", config.CENTRAL_TIMEOUT_SECONDS)  # callers may pass a longer one
    try:
        return httpx.request(method, config.CENTRAL_API_URL + path, headers=headers, **kwargs)
    except httpx.HTTPError:
        raise ApiError(503, "service_unavailable", "could not reach the central service") from None


def request(method: str, path: str, **kwargs) -> httpx.Response:
    """Calls central with the user's access token. On a 401 (token revoked or
    clock skew) refreshes once and retries."""
    resp = _send(method, path, **kwargs)
    if resp.status_code == 401:
        session.refresh_now()
        resp = _send(method, path, **kwargs)
        if resp.status_code == 401:
            raise ApiError(401, "unauthorized", "central rejected the session")
    return resp


def request_json(method: str, path: str, **kwargs) -> dict | None:
    """Calls central and returns the parsed JSON body (None for 204). A non-2xx
    central error envelope is re-raised one to one; anything unparseable is a 503.
    Promoted from teams.py's original private `_call` so every central-calling
    module (teams, publish, search merge, relay/download) shares one implementation
    instead of each re-parsing the error envelope itself."""
    resp = request(method, path, **kwargs)
    if resp.status_code == 204:
        return None
    try:
        body = resp.json()
    except ValueError:
        raise ApiError(503, "service_unavailable", "central returned an invalid response") from None
    if resp.status_code >= 400:
        err = body.get("error") if isinstance(body, dict) else None
        if not isinstance(err, dict) or "code" not in err:
            raise ApiError(503, "service_unavailable", "central returned an invalid response")
        raise ApiError(resp.status_code, err["code"], err.get("message", ""), err.get("details") or {})
    return body


_health: tuple[float, bool] = (0.0, False)  # (checked_at, reachable)


def is_reachable() -> bool:
    """Open GET /health; no token needed. Cached briefly because the frontend polls
    /session and each uncached check can block a worker for the full timeout."""
    global _health
    if not config.CENTRAL_API_URL:
        return False
    checked_at, reachable = _health
    if time.monotonic() - checked_at < config.CENTRAL_HEALTH_CACHE_SECONDS:
        return reachable
    try:
        reachable = httpx.get(config.CENTRAL_API_URL + "/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        reachable = False
    _health = (time.monotonic(), reachable)
    return reachable
