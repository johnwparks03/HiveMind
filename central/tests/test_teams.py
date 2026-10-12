import datetime
import json
import os
import sys
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import teams  # noqa: E402
import migrate  # noqa: E402


class FakeCursor:
    """Scripted cursor: each fetchone()/fetchall() pops the next canned result."""

    def __init__(self, results=()):
        self.results = list(results)
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.results.pop(0)

    def fetchall(self):
        return self.results.pop(0)

    def sqls(self):
        return " | ".join(s for s, _ in self.executed)


@pytest.fixture
def fake_db(monkeypatch):
    holder = {}

    def install(results):
        cur = FakeCursor(results)
        holder["cur"] = cur

        @contextmanager
        def transaction():
            yield cur

        monkeypatch.setattr(teams.db, "transaction", transaction)
        return cur

    return install


def _event(route, body=None, sub="user-1"):
    return {
        "routeKey": route,
        "body": json.dumps(body) if body is not None else None,
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": sub}}}},
    }


def _body(resp):
    return json.loads(resp["body"])


NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def test_generate_code_format_and_alphabet():
    for _ in range(200):
        code = teams.generate_code()
        assert teams.CODE_RE.match(code)
        assert not set(code.replace("-", "")) & set("01OIL")


def test_normalize_code():
    assert teams.normalize_code("  k7q2-9xpd ") == "K7Q2-9XPD"
    assert teams.normalize_code(None) == ""
    assert teams.normalize_code(5) == ""


def test_unauthenticated_is_401():
    resp = teams.handler({"routeKey": "GET /teams/me"}, None)
    assert resp["statusCode"] == 401


def test_unknown_route_is_404(fake_db):
    fake_db([])
    assert teams.handler(_event("GET /nope"), None)["statusCode"] == 404


def test_invalid_json_body_is_400(fake_db):
    fake_db([])
    event = _event("POST /teams")
    event["body"] = "{not json"
    resp = teams.handler(event, None)
    assert resp["statusCode"] == 400 and _body(resp)["error"]["code"] == "invalid_request"


@pytest.mark.parametrize("body", [{}, {"name": ""}, {"name": "   "}, {"name": 5}, {"name": "x" * 101}])
def test_create_team_validates_name(fake_db, body):
    fake_db([])
    resp = teams.handler(_event("POST /teams", body), None)
    assert resp["statusCode"] == 400


def test_create_team_when_already_member_is_409(fake_db):
    fake_db([("team-id", "Alpha")])
    resp = teams.handler(_event("POST /teams", {"name": "Beta"}), None)
    assert resp["statusCode"] == 409 and _body(resp)["error"]["code"] == "already_in_team"


def test_create_team_success_logs_event(fake_db):
    cur = fake_db([None, (NOW,)])
    resp = teams.handler(_event("POST /teams", {"name": " Alpha "}), None)
    body = _body(resp)
    assert resp["statusCode"] == 201
    assert body["name"] == "Alpha" and body["team_id"] and body["created_at"] == NOW.isoformat()
    assert "INSERT INTO memberships" in cur.sqls() and "access_log" in cur.sqls()


def test_get_my_team(fake_db):
    fake_db([("tid", "Alpha")])
    assert _body(teams.handler(_event("GET /teams/me"), None)) == {"team": {"team_id": "tid", "name": "Alpha"}}
    fake_db([None])
    assert _body(teams.handler(_event("GET /teams/me"), None)) == {"team": None}


def test_invite_without_team_is_403(fake_db):
    fake_db([None])
    resp = teams.handler(_event("POST /teams/me/invites"), None)
    assert resp["statusCode"] == 403 and _body(resp)["error"]["code"] == "no_team"


def test_invite_uses_configured_lifetime(fake_db, monkeypatch):
    monkeypatch.setenv("INVITE_LIFETIME_DAYS", "3")
    cur = fake_db([("tid", "Alpha"), (NOW,)])
    resp = teams.handler(_event("POST /teams/me/invites"), None)
    assert resp["statusCode"] == 201 and teams.CODE_RE.match(_body(resp)["code"])
    assert cur.executed[-1][1][-1] == 3


def test_join_requires_code(fake_db):
    fake_db([])
    assert teams.handler(_event("POST /teams/join", {}), None)["statusCode"] == 400


def test_join_already_in_team_is_409(fake_db):
    fake_db([("tid", "Alpha")])
    resp = teams.handler(_event("POST /teams/join", {"code": "K7Q2-9XPD"}), None)
    assert resp["statusCode"] == 409


def test_join_unknown_or_malformed_code_is_404(fake_db):
    fake_db([None, None])
    resp = teams.handler(_event("POST /teams/join", {"code": "K7Q2-9XPD"}), None)
    assert resp["statusCode"] == 404 and _body(resp)["error"]["code"] == "invalid_code"
    fake_db([None])
    assert teams.handler(_event("POST /teams/join", {"code": "bad"}), None)["statusCode"] == 404


@pytest.mark.parametrize("expired,used_up", [(True, False), (False, True)])
def test_join_expired_or_used_is_410(fake_db, expired, used_up):
    fake_db([None, ("tid", "Alpha", expired, used_up)])
    resp = teams.handler(_event("POST /teams/join", {"code": "K7Q2-9XPD"}), None)
    assert resp["statusCode"] == 410 and _body(resp)["error"]["code"] == "invite_expired"


def test_join_success_normalizes_code_and_counts_use(fake_db):
    cur = fake_db([None, ("tid", "Alpha", False, False)])
    resp = teams.handler(_event("POST /teams/join", {"code": " k7q2-9xpd"}), None)
    assert resp["statusCode"] == 200 and _body(resp) == {"team_id": "tid", "name": "Alpha"}
    assert "use_count = use_count + 1" in cur.sqls()


def test_leave_without_team_is_403(fake_db):
    fake_db([None])
    assert teams.handler(_event("POST /teams/me/leave"), None)["statusCode"] == 403


def test_leave_last_member_deletes_team_and_invites(fake_db):
    cur = fake_db([("tid", "Alpha"), (0,)])
    resp = teams.handler(_event("POST /teams/me/leave"), None)
    assert resp["statusCode"] == 204
    assert "DELETE FROM invites" in cur.sqls() and "DELETE FROM teams" in cur.sqls()


def test_leave_keeps_team_when_others_remain(fake_db):
    cur = fake_db([("tid", "Alpha"), (2,)])
    assert teams.handler(_event("POST /teams/me/leave"), None)["statusCode"] == 204
    assert "DELETE FROM teams" not in cur.sqls()
    assert "DELETE FROM memberships" in cur.sqls()


def test_unique_violation_maps_to_already_in_team(monkeypatch):
    class Dup(Exception):
        pgcode = "23505"

    @contextmanager
    def boom():
        raise Dup()
        yield

    monkeypatch.setattr(teams.db, "transaction", boom)
    resp = teams.handler(_event("GET /teams/me"), None)
    assert resp["statusCode"] == 409 and _body(resp)["error"]["code"] == "already_in_team"


def test_unexpected_error_is_503_without_leaking(monkeypatch):
    @contextmanager
    def boom():
        raise RuntimeError("password=hunter2")
        yield

    monkeypatch.setattr(teams.db, "transaction", boom)
    resp = teams.handler(_event("GET /teams/me"), None)
    assert resp["statusCode"] == 503 and "hunter2" not in resp["body"]


def test_migrate_pending_is_ordered_and_skips_applied():
    assert migrate.pending(["0001_a.sql"], ["0002_b.sql", "0001_a.sql", "0003_c.sql"]) == [
        "0002_b.sql", "0003_c.sql"]
