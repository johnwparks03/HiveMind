import httpx
import pytest

from app import config, db
from app.auth import session
from app.central import teams


class FakeCentral:
    """Stands in for httpx.request in app.central.client. Replies per 'METHOD path'."""

    def __init__(self):
        self.replies = {}
        self.calls = []

    def reply(self, route, status, body=None):
        self.replies[route] = (status, body)

    def __call__(self, method, url, headers=None, timeout=None, **kw):
        route = f"{method} {url.removeprefix(config.CENTRAL_API_URL)}"
        self.calls.append((route, kw.get("json")))
        status, body = self.replies[route]
        if status == 204:
            return httpx.Response(204)
        return httpx.Response(status, json=body)


def _err(code, message="msg"):
    return {"error": {"code": code, "message": message, "details": {}}}


@pytest.fixture
def central(cognito_fake, keyring_fake, monkeypatch):
    session.login("a@firm.com", "Passw0rd!x")
    fake = FakeCentral()
    monkeypatch.setattr("app.central.client.httpx.request", fake)
    monkeypatch.setattr(config, "TEAM_CACHE_SECONDS", 0)
    teams.invalidate_cache()
    return fake


@pytest.fixture
def local_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "SQLITE_PATH", tmp_path / "registry.db")
    db.init_db()
    with db.session() as conn:
        conn.execute("INSERT INTO folders (folder_id, path, added_at) VALUES ('f1', 'C:/x', '2026-01-01T00:00:00+00:00')")
        conn.execute(
            "INSERT INTO files (file_id, folder_id, path, filename, tags, public_state, publish_state, "
            "published_at, expires_at, last_confirmed) VALUES "
            "('a', 'f1', 'C:/x/a.txt', 'a.txt', '[\"t\"]', 'public', 'published', 'p', 'e', 'c')")
    return db


def test_get_team(client, auth, central):
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "Alpha"}})
    assert client.get("/team", headers=auth).json() == {"team": {"team_id": "t1", "name": "Alpha"}}
    central.reply("GET /teams/me", 200, {"team": None})
    assert client.get("/team", headers=auth).json() == {"team": None}


def test_create_team_strips_created_at(client, auth, central):
    central.reply("POST /teams", 201, {"team_id": "t1", "name": "Alpha", "created_at": "x"})
    resp = client.post("/team", headers=auth, json={"name": "Alpha"})
    assert resp.status_code == 201 and resp.json() == {"team_id": "t1", "name": "Alpha"}
    assert central.calls[-1] == ("POST /teams", {"name": "Alpha"})


def test_invite_and_join(client, auth, central):
    central.reply("POST /teams/me/invites", 201, {"code": "K7Q2-9XPD", "expires_at": "e"})
    resp = client.post("/team/invites", headers=auth)
    assert resp.status_code == 201 and resp.json() == {"code": "K7Q2-9XPD", "expires_at": "e"}
    central.reply("POST /teams/join", 200, {"team_id": "t1", "name": "Alpha"})
    resp = client.post("/team/join", headers=auth, json={"code": "K7Q2-9XPD"})
    assert resp.status_code == 200 and resp.json() == {"team_id": "t1", "name": "Alpha"}


@pytest.mark.parametrize("route,path,body,status,code", [
    ("POST /teams", "/team", {"name": "A"}, 409, "already_in_team"),
    ("POST /teams/me/invites", "/team/invites", None, 403, "no_team"),
    ("POST /teams/join", "/team/join", {"code": "X"}, 404, "invalid_code"),
    ("POST /teams/join", "/team/join", {"code": "X"}, 410, "invite_expired"),
    ("POST /teams/join", "/team/join", {"code": "X"}, 409, "already_in_team"),
    ("POST /teams/me/leave", "/team/leave", None, 403, "no_team"),
])
def test_central_errors_map_one_to_one(client, auth, central, route, path, body, status, code):
    central.reply(route, status, _err(code, "from central"))
    resp = client.post(path, headers=auth, json=body)
    assert resp.status_code == status
    assert resp.json() == {"error": {"code": code, "message": "from central", "details": {}}}


def test_garbage_central_response_is_503(client, auth, central):
    central.reply("GET /teams/me", 502, {"unexpected": True})
    resp = client.get("/team", headers=auth)
    assert resp.status_code == 503 and resp.json()["error"]["code"] == "service_unavailable"


def test_requires_sign_in(client, auth):
    resp = client.get("/team", headers=auth)
    assert resp.status_code == 401 and resp.json()["error"]["code"] == "unauthorized"


def test_body_validation(client, auth, central):
    assert client.post("/team", headers=auth, json={}).status_code == 400
    assert client.post("/team/join", headers=auth, json={}).status_code == 400


def test_leave_clears_local_publish_state(client, auth, central, local_db):
    central.reply("POST /teams/me/leave", 204)
    assert client.post("/team/leave", headers=auth).status_code == 204
    with local_db.session() as conn:
        row = dict(conn.execute("SELECT * FROM files").fetchone())
    assert row["public_state"] == "private"
    assert row["publish_state"] is row["published_at"] is row["expires_at"] is row["last_confirmed"] is None
    assert row["tags"] == '["t"]'


def test_failed_leave_leaves_local_state_alone(client, auth, central, local_db):
    central.reply("POST /teams/me/leave", 503, _err("service_unavailable"))
    assert client.post("/team/leave", headers=auth).status_code == 503
    with local_db.session() as conn:
        assert conn.execute("SELECT public_state FROM files").fetchone()[0] == "public"


def test_session_reports_team(client, auth, central, monkeypatch):
    monkeypatch.setattr("app.central.client.httpx.get", lambda *a, **k: httpx.Response(200, json={}))
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "Alpha"}})
    assert client.get("/session", headers=auth).json()["team"] == {"team_id": "t1", "name": "Alpha"}


def test_session_survives_team_lookup_failure(client, auth, central, monkeypatch):
    monkeypatch.setattr("app.central.client.httpx.get", lambda *a, **k: httpx.Response(200, json={}))
    central.reply("GET /teams/me", 503, _err("service_unavailable"))
    body = client.get("/session", headers=auth).json()
    assert body["signed_in"] is True and body["team"] is None


def test_session_team_is_cached(client, auth, central, monkeypatch):
    monkeypatch.setattr("app.central.client.httpx.get", lambda *a, **k: httpx.Response(200, json={}))
    monkeypatch.setattr(config, "TEAM_CACHE_SECONDS", 60)
    central.reply("GET /teams/me", 200, {"team": None})
    client.get("/session", headers=auth)
    client.get("/session", headers=auth)
    assert [c for c, _ in central.calls].count("GET /teams/me") == 1


def test_local_search_works_without_team(client, auth, central, local_db):
    # A user with no team still searches locally; search never calls central.
    central.reply("GET /teams/me", 200, {"team": None})
    resp = client.post("/search", headers=auth, json={"query": "anything"})
    assert resp.status_code != 403
    assert not any(route.startswith("POST /teams") for route, _ in central.calls)


def test_get_team_reports_own_email_when_central_has_none(client, auth, central):
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "Alpha", "members": [
        {"email": None, "is_you": True}, {"email": "b@firm.com", "is_you": False}]}})
    central.reply("PUT /teams/me/email", 204)
    members = client.get("/team", headers=auth).json()["team"]["members"]
    assert members[0] == {"email": "a@firm.com", "is_you": True}
    assert ("PUT /teams/me/email", {"email": "a@firm.com"}) in central.calls


def test_get_team_does_not_resend_an_email_central_already_has(client, auth, central):
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "Alpha", "members": [
        {"email": "a@firm.com", "is_you": True}]}})
    client.get("/team", headers=auth)
    assert [route for route, _ in central.calls] == ["GET /teams/me"]


def test_get_team_survives_a_failed_email_report(client, auth, central):
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "Alpha", "members": [
        {"email": None, "is_you": True}]}})
    central.reply("PUT /teams/me/email", 503, _err("service_unavailable"))
    resp = client.get("/team", headers=auth)
    assert resp.status_code == 200 and resp.json()["team"]["members"][0]["email"] is None
