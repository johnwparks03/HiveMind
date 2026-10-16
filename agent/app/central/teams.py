"""Team calls to central (Interface B /teams/*) and the local state that follows them."""
import time

import httpx

from app import config
from app.auth import session
from app.central import client as central_client
from app.central import publish
from app.db import session as db_session
from app.errors import ApiError

_call = central_client.request_json  # kept as a short local alias; call sites unchanged

_cache: tuple[float, dict | None] | None = None


def invalidate_cache() -> None:
    global _cache
    _cache = None


def get_team() -> dict | None:
    team = _call("GET", "/teams/me")["team"]
    if team:
        _report_own_email(team)
    return team


def _report_own_email(team: dict) -> None:
    """Central can't look emails up (no route out of its VPC), so each agent tells it
    its own. Runs when the caller's membership has no email yet; best effort, because
    a failure just means the list shows no address for this person until the next call."""
    mine = next((m for m in team.get("members", []) if m.get("is_you")), None)
    own = session.email()
    if not mine or mine.get("email") or not own:
        return
    try:
        _call("PUT", "/teams/me/email", json={"email": own})
    except (ApiError, httpx.HTTPError):
        return
    mine["email"] = own


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
    file. Tags are kept so a later re-publish doesn't regenerate them. Also cancels
    anything still queued — without this, a pending publish would just keep
    retrying into 403 no_team forever."""
    publish.cancel_all()
    with db_session() as conn:
        conn.execute(
            "UPDATE files SET public_state = 'private', publish_state = NULL, "
            "published_at = NULL, expires_at = NULL, last_confirmed = NULL"
        )
