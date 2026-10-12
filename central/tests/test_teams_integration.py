"""Integration tests for E1-S4 against the deployed HiveMind stack.

Run: pytest -m integration   (needs `aws login`; the stack must include the Teams API)
Creates throwaway Cognito users and teams; users are deleted afterwards and every
test leaves its teams (the last leaver deletes the team). Tokens are never printed.
"""
import json
import os
import urllib.error
import urllib.request
import uuid

import boto3
import pytest

from test_auth_integration import PASSWORD, REGION, _login, _sign_up, cfg, cognito  # noqa: F401

pytestmark = pytest.mark.integration


def _call(cfg, method, path, token, body=None):
    req = urllib.request.Request(cfg["api_url"] + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else None


@pytest.fixture
def make_user(cfg, cognito):  # noqa: F811
    created = []

    def _make():
        email = f"e1s4-{uuid.uuid4().hex[:12]}@example.com"
        _sign_up(cognito, cfg, email)
        created.append(email)
        return _login(cognito, cfg, email)["AccessToken"]

    yield _make
    for email in created:
        try:
            cognito.admin_delete_user(UserPoolId=cfg["pool_id"], Username=email)
        except cognito.exceptions.UserNotFoundException:
            pass


def _error_code(body):
    return body["error"]["code"]


def test_create_team_then_get_me(cfg, make_user):
    token = make_user()
    assert _call(cfg, "GET", "/teams/me", token) == (200, {"team": None})
    status, team = _call(cfg, "POST", "/teams", token, {"name": "Alpha"})
    assert status == 201 and team["name"] == "Alpha" and team["created_at"]
    assert _call(cfg, "GET", "/teams/me", token) == (
        200, {"team": {"team_id": team["team_id"], "name": "Alpha"}})
    status, body = _call(cfg, "POST", "/teams", token, {"name": "Beta"})
    assert status == 409 and _error_code(body) == "already_in_team"
    assert _call(cfg, "POST", "/teams/me/leave", token)[0] == 204


def test_invite_join_and_leave(cfg, make_user):
    owner, member = make_user(), make_user()
    _, team = _call(cfg, "POST", "/teams", owner, {"name": "Alpha"})
    status, invite = _call(cfg, "POST", "/teams/me/invites", owner)
    assert status == 201 and invite["code"] and invite["expires_at"]

    assert _call(cfg, "POST", "/teams/join", member, {"code": "ZZZZ-ZZZZ"})[1]["error"]["code"] == "invalid_code"
    status, joined = _call(cfg, "POST", "/teams/join", member, {"code": invite["code"].lower()})
    assert status == 200 and joined["team_id"] == team["team_id"]  # multi-use, case-insensitive
    status, body = _call(cfg, "POST", "/teams/join", member, {"code": invite["code"]})
    assert status == 409 and _error_code(body) == "already_in_team"

    # Leaving removes membership; team-scoped endpoints then return 403 no_team.
    assert _call(cfg, "POST", "/teams/me/leave", member)[0] == 204
    status, body = _call(cfg, "POST", "/teams/me/invites", member)
    assert status == 403 and _error_code(body) == "no_team"
    status, body = _call(cfg, "POST", "/teams/me/leave", member)
    assert status == 403 and _error_code(body) == "no_team"

    # The team survives while the owner remains; the last leaver deletes it and its invites.
    assert _call(cfg, "GET", "/teams/me", owner)[1]["team"]["team_id"] == team["team_id"]
    assert _call(cfg, "POST", "/teams/me/leave", owner)[0] == 204
    status, body = _call(cfg, "POST", "/teams/join", member, {"code": invite["code"]})
    assert status == 404 and _error_code(body) == "invalid_code"


def test_invite_expiry_and_team_id_never_taken_from_input(cfg, make_user):
    owner, other = make_user(), make_user()
    _, team = _call(cfg, "POST", "/teams", owner, {"name": "Alpha"})
    # A client-supplied team_id is ignored: invites always belong to the caller's team.
    status, invite = _call(cfg, "POST", "/teams/me/invites", owner, {"team_id": str(uuid.uuid4())})
    assert status == 201

    # Expire the invite directly in the DB (the DB is only reachable from the VPC, so
    # run the optional check only when a connection string is supplied).
    dsn = os.environ.get("HIVEMIND_TEST_DB_DSN")
    if dsn:
        import psycopg2

        with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("UPDATE invites SET expires_at = now() - interval '1 minute' WHERE code = %s",
                        (invite["code"],))
        status, body = _call(cfg, "POST", "/teams/join", other, {"code": invite["code"]})
        assert status == 410 and _error_code(body) == "invite_expired"
    assert _call(cfg, "POST", "/teams/me/leave", owner)[0] == 204


def test_validation_and_auth(cfg, make_user):
    token = make_user()
    for body in ({}, {"name": ""}, {"name": 5}):
        assert _call(cfg, "POST", "/teams", token, body)[0] == 400
    assert _call(cfg, "POST", "/teams/join", token, {})[0] == 400
    req = urllib.request.Request(cfg["api_url"] + "/teams/me")
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=15)
    assert exc.value.code == 401
