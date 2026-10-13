"""Teams API (Interface B /teams/*). One Lambda behind five routes; dispatches on
routeKey. team_id is always derived from the caller's membership, never from input."""
import os
import re
import secrets
import uuid

from common import db
from common.access_log import log_event
from common.auth import get_caller_sub
from common.errors import ApiError, Unauthorized, error_response, unauthorized_response
from common.http import get_membership, json_response, parse_body

# No 0/O/1/I/L so codes survive being read aloud or retyped.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_RE = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}$")
NAME_MAX_CHARS = 100


def invite_lifetime_days():
    return int(os.environ.get("INVITE_LIFETIME_DAYS", "7"))


def generate_code():
    half = lambda: "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))  # noqa: E731
    return f"{half()}-{half()}"


def normalize_code(raw):
    return raw.strip().upper() if isinstance(raw, str) else ""


def _is_unique_violation(exc):
    return getattr(exc, "pgcode", None) == "23505"


def create_team(cur, user_id, body):
    name = body.get("name")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > NAME_MAX_CHARS:
        raise ApiError(400, "invalid_request", "name is required (1-%d characters)" % NAME_MAX_CHARS)
    if get_membership(cur, user_id):
        raise ApiError(409, "already_in_team", "you are already in a team")
    team_id = str(uuid.uuid4())
    cur.execute("INSERT INTO teams (id, name, created_by) VALUES (%s, %s, %s) RETURNING created_at",
                (team_id, name.strip(), user_id))
    created_at = cur.fetchone()[0]
    cur.execute("INSERT INTO memberships (user_id, team_id) VALUES (%s, %s)", (user_id, team_id))
    log_event(cur, "team_create", user_id, team_id)
    return json_response(201, {"team_id": team_id, "name": name.strip(), "created_at": created_at.isoformat()})


def get_my_team(cur, user_id):
    row = get_membership(cur, user_id)
    return json_response(200, {"team": {"team_id": str(row[0]), "name": row[1]} if row else None})


def create_invite(cur, user_id):
    row = get_membership(cur, user_id)
    if not row:
        raise ApiError(403, "no_team", "you are not in a team")
    code = generate_code()
    cur.execute("INSERT INTO invites (code, team_id, created_by, expires_at) "
                "VALUES (%s, %s, %s, now() + make_interval(days => %s)) RETURNING expires_at",
                (code, row[0], user_id, invite_lifetime_days()))
    return json_response(201, {"code": code, "expires_at": cur.fetchone()[0].isoformat()})


def join_team(cur, user_id, body):
    code = normalize_code(body.get("code"))
    if not code:
        raise ApiError(400, "invalid_request", "code is required")
    if get_membership(cur, user_id):
        raise ApiError(409, "already_in_team", "you are already in a team")
    cur.execute("SELECT i.team_id, t.name, i.expires_at <= now(), "
                "i.max_uses IS NOT NULL AND i.use_count >= i.max_uses "
                "FROM invites i JOIN teams t ON t.id = i.team_id WHERE i.code = %s FOR UPDATE OF i",
                (code,))
    row = cur.fetchone() if CODE_RE.match(code) else None
    if not row:
        raise ApiError(404, "invalid_code", "invite code not found")
    team_id, name, expired, used_up = row
    if expired or used_up:
        raise ApiError(410, "invite_expired", "invite has expired or was already used")
    cur.execute("INSERT INTO memberships (user_id, team_id) VALUES (%s, %s)", (user_id, team_id))
    cur.execute("UPDATE invites SET use_count = use_count + 1 WHERE code = %s", (code,))
    log_event(cur, "team_join", user_id, team_id)
    return json_response(200, {"team_id": str(team_id), "name": name})


def leave_team(cur, user_id):
    row = get_membership(cur, user_id)
    if not row:
        raise ApiError(403, "no_team", "you are not in a team")
    team_id = row[0]
    # Lock the team so two last members leaving at once can't both skip the cleanup.
    cur.execute("SELECT id FROM teams WHERE id = %s FOR UPDATE", (team_id,))
    cur.execute("DELETE FROM public_files WHERE owner_id = %s", (user_id,))
    cur.execute("DELETE FROM connections WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM memberships WHERE user_id = %s", (user_id,))
    log_event(cur, "team_leave", user_id, team_id)
    cur.execute("SELECT count(*) FROM memberships WHERE team_id = %s", (team_id,))
    if cur.fetchone()[0] == 0:
        cur.execute("DELETE FROM invites WHERE team_id = %s", (team_id,))
        cur.execute("DELETE FROM teams WHERE id = %s", (team_id,))
    return {"statusCode": 204, "headers": {}, "body": ""}


ROUTES = {
    "POST /teams": lambda cur, user, body: create_team(cur, user, body),
    "GET /teams/me": lambda cur, user, body: get_my_team(cur, user),
    "POST /teams/me/invites": lambda cur, user, body: create_invite(cur, user),
    "POST /teams/join": lambda cur, user, body: join_team(cur, user, body),
    "POST /teams/me/leave": lambda cur, user, body: leave_team(cur, user),
}


def handler(event, context):
    try:
        user_id = get_caller_sub(event)
    except Unauthorized:
        return unauthorized_response()
    route = ROUTES.get(event.get("routeKey"))
    if route is None:
        return error_response(404, "not_found", "route not found")
    try:
        body = parse_body(event)
        with db.transaction() as cur:
            return route(cur, user_id, body)
    except ApiError as exc:
        return error_response(exc.status, exc.code, exc.message, exc.details)
    except Exception as exc:  # noqa: BLE001
        if _is_unique_violation(exc):  # concurrent join/create: UNIQUE(user_id) held
            return error_response(409, "already_in_team", "you are already in a team")
        print(f"teams handler error: {type(exc).__name__}")  # never log bodies or values
        return error_response(503, "service_unavailable", "service unavailable")
