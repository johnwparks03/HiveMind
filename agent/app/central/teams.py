"""Team calls to central (Interface B /teams/*) and the local state that follows them."""
import time

import httpx

from app import config
from app.central import client as central_client
from app.db import session as db_session
from app.errors import ApiError


def _call(method: str, path: str, **kwargs):
    """Calls central and returns the parsed JSON body (None for 204). A non-2xx
    central error envelope is re-raised one to one; anything unparseable is a 503."""
    resp = central_client.request(method, path, **kwargs)
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


_cache: tuple[float, dict | None] | None = None


def invalidate_cache() -> None:
    global _cache
    _cache = None


def get_team() -> dict | None:
    body = _call("GET", "/teams/me")
    return body["team"]


def current_team_or_none() -> dict | None:
    """For GET /session: the cached team, or None when it can't be fetched. Never raises,
    because /session must keep working with central down or the user signed out."""
    global _cache
    if _cache and time.monotonic() - _cache[0] < config.TEAM_CACHE_SECONDS:
        return _cache[1]
    try:
        team = get_team()
    except (ApiError, httpx.HTTPError):
        return None
    _cache = (time.monotonic(), team)
    return team


def create_team(name: str) -> dict:
    body = _call("POST", "/teams", json={"name": name})
    invalidate_cache()
    return {"team_id": body["team_id"], "name": body["name"]}


def create_invite() -> dict:
    body = _call("POST", "/teams/me/invites")
    return {"code": body["code"], "expires_at": body["expires_at"]}


def join_team(code: str) -> dict:
    body = _call("POST", "/teams/join", json={"code": code})
    invalidate_cache()
    return {"team_id": body["team_id"], "name": body["name"]}


def leave_team() -> None:
    _call("POST", "/teams/me/leave")  # raises before any local change if central fails
    invalidate_cache()
    clear_local_publish_state()


def clear_local_publish_state() -> None:
    """After leaving, nothing is public any more: reset publish state on every local
    file. Tags are kept so a later re-publish doesn't regenerate them.
    E3 extends this to cancel queued publishes once the publish queue exists."""
    with db_session() as conn:
        conn.execute(
            "UPDATE files SET public_state = 'private', publish_state = NULL, "
            "published_at = NULL, expires_at = NULL, last_confirmed = NULL"
        )
