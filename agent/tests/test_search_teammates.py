"""search_service.py's central-search merge (docs/stories/BACKLOG.md E3-S8): the
"local comes up short, or the user asked for it" trigger, and the skipped_reason
mapping (local_sufficient | no_team | central_unavailable).
"""
from datetime import datetime

import httpx
import pytest

from app import config
from app.auth import session
from app.central import teams
from app.folders.scanner import add_folder
from app.search.search_service import search_local


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


@pytest.fixture
def searchable(isolated_store, corpus):
    root, written = corpus
    add_folder(str(root))
    return root, written


SOME_TEAM = {"team": {"team_id": "t1", "name": "Alpha"}}
NO_TEAM = {"team": None}
SOME_RESULTS = {"results": [
    {"file_id": "x1", "filename": "roadmap.docx", "tags": ["roadmap"],
     "file_created_at": "2026-09-01T00:00:00+00:00", "file_modified_at": "2026-09-01T00:00:00+00:00",
     "expires_at": "2026-11-01T00:00:00+00:00", "owner_online": True}
]}


def test_local_results_found_skips_central_by_default(searchable, central):
    central.reply("GET /teams/me", 200, SOME_TEAM)
    result = search_local("budget plan")
    assert result["local_results"], "expected this query to find something locally"
    assert result["teammate"] == {"searched": False, "skipped_reason": "local_sufficient", "results": []}
    assert not any(route.startswith("POST /search") for route, _ in central.calls)


def test_empty_local_results_triggers_central(searchable, central):
    central.reply("GET /teams/me", 200, SOME_TEAM)
    central.reply("POST /search", 200, SOME_RESULTS)
    # A date nothing in the corpus falls in guarantees zero local results regardless
    # of embedding behavior (fake embeddings in tests aren't reliably "low score for
    # nonsense text" the way the real model is).
    result = search_local("project status from 1999")
    assert result["local_results"] == []
    assert result["teammate"]["searched"] is True
    assert result["teammate"]["skipped_reason"] is None
    assert result["teammate"]["results"] == SOME_RESULTS["results"]


def test_include_teammates_calls_central_even_with_local_results(searchable, central):
    central.reply("GET /teams/me", 200, SOME_TEAM)
    central.reply("POST /search", 200, SOME_RESULTS)
    result = search_local("budget plan", include_teammates=True)
    assert result["local_results"], "this query should still find something locally"
    assert result["teammate"]["searched"] is True
    assert result["teammate"]["results"] == SOME_RESULTS["results"]


def test_no_team_gives_no_team_skipped_reason(searchable, central):
    central.reply("GET /teams/me", 200, NO_TEAM)
    result = search_local("budget plan", include_teammates=True)
    assert result["teammate"] == {"searched": False, "skipped_reason": "no_team", "results": []}
    assert not any(route.startswith("POST /search") for route, _ in central.calls)


def test_central_unavailable_does_not_fail_the_whole_request(searchable, central):
    central.reply("GET /teams/me", 200, SOME_TEAM)
    central.reply("POST /search", 503, {"error": {"code": "service_unavailable", "message": "down"}})
    result = search_local("budget plan", include_teammates=True)
    assert result["local_results"], "local results must still come back"
    assert result["teammate"] == {"searched": False, "skipped_reason": "central_unavailable", "results": []}


def test_sends_timezone_aware_dates_to_central(searchable, central):
    # Same class of bug as the publish fix: a naive timestamp is silently rejected
    # by central's validator. The query parser's dates are already timezone-aware,
    # but this pins it so a future refactor can't quietly drop that.
    central.reply("GET /teams/me", 200, SOME_TEAM)
    central.reply("POST /search", 200, {"results": []})
    search_local("budget plan from last week", include_teammates=True)
    sent = next(body for route, body in central.calls if route == "POST /search")
    assert datetime.fromisoformat(sent["date_from"]).tzinfo is not None
    assert datetime.fromisoformat(sent["date_to"]).tzinfo is not None
