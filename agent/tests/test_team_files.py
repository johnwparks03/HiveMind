"""list_team_files() (search_service.py), backing the Groups page's browse view:
central's no-topic search mode, reused as-is - same FakeCentral pattern as
test_search_teammates.py.
"""
import httpx
import pytest

from app import config
from app.auth import session
from app.central import teams
from app.errors import ApiError
from app.search.search_service import list_team_files


class FakeCentral:
    def __init__(self):
        self.replies = {}
        self.calls = []

    def reply(self, route, status, body=None):
        self.replies[route] = (status, body)

    def __call__(self, method, url, headers=None, timeout=None, **kw):
        route = f"{method} {url.removeprefix(config.CENTRAL_API_URL)}"
        self.calls.append((route, kw.get("json")))
        status, body = self.replies.get(route, (200, {"results": []}))
        if status == 204:
            return httpx.Response(204)
        return httpx.Response(status, json=body)


@pytest.fixture
def central(cognito_fake, keyring_fake, monkeypatch):
    session.login("a@firm.com", "Passw0rd!x")
    fake = FakeCentral()
    monkeypatch.setattr("app.central.client.httpx.request", fake)
    monkeypatch.setattr(config, "TEAM_CACHE_SECONDS", 0)
    teams.invalidate_cache()
    return fake


SOME_TEAM = {"team": {"team_id": "t1", "name": "Alpha"}}
NO_TEAM = {"team": None}
SOME_RESULTS = {"results": [
    {"file_id": "x1", "filename": "roadmap.docx", "tags": ["roadmap"],
     "file_created_at": "2026-09-01T00:00:00+00:00", "file_modified_at": "2026-09-01T00:00:00+00:00",
     "expires_at": "2026-11-01T00:00:00+00:00", "owner_online": True}
]}


def test_lists_everything_the_team_shared(isolated_store, central):
    central.reply("GET /teams/me", 200, SOME_TEAM)
    central.reply("POST /search", 200, SOME_RESULTS)
    assert list_team_files() == SOME_RESULTS["results"]
    sent = next(body for route, body in central.calls if route == "POST /search")
    assert sent == {"topic": None, "date_from": None, "date_to": None}


def test_no_team_raises_no_team(isolated_store, central):
    central.reply("GET /teams/me", 200, NO_TEAM)
    with pytest.raises(ApiError) as exc:
        list_team_files()
    assert exc.value.code == "no_team"
    assert exc.value.status == 403


def test_central_unavailable_raises_service_unavailable(isolated_store, central):
    central.reply("GET /teams/me", 200, SOME_TEAM)
    central.reply("POST /search", 503, {"error": {"code": "service_unavailable", "message": "down"}})
    with pytest.raises(ApiError) as exc:
        list_team_files()
    assert exc.value.code == "service_unavailable"
    assert exc.value.status == 503
