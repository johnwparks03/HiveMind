"""agent/app/central/publish.py + agent/app/folders/share.py: the durable
publish/unpublish queue and folder share/unshare (docs/stories/BACKLOG.md E3-S4/S5/S6).
"""
import asyncio
import json
from datetime import datetime

import httpx
import pytest

from app import config, db
from app.auth import session
from app.central import publish, teams
from app.folders import share


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
        status, body = self.replies.get(route, (200, {}))
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


def _seed_file(file_id="a", path="C:/x/a.txt", tags='["budget"]', index_status="indexed",
                public_state="private", publish_state=None, folder_id="f1"):
    with db.session() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO folders (folder_id, path, added_at) VALUES (?, 'C:/x', '2026-01-01T00:00:00+00:00')", (folder_id,)
        )
        conn.execute(
            "INSERT INTO files (file_id, folder_id, path, filename, index_status, tags, "
            "public_state, publish_state, file_created_at, file_modified_at) VALUES "
            # Naive (no tzinfo) local-time strings, same shape scanner.py actually stores -
            # this is exactly the shape that silently failed central's validator in real use.
            "(?, ?, ?, ?, ?, ?, ?, ?, '2026-10-01T09:00:00', '2026-10-10T14:30:00')",
            (file_id, folder_id, path, path.rsplit("/", 1)[-1], index_status, tags, public_state, publish_state),
        )


def _file_row(file_id="a"):
    with db.session() as conn:
        return conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)).fetchone()


# --- enqueue / retry / cancel (pure SQLite logic, no central call) ----------------------


def test_enqueue_latest_intent_wins(isolated_store):
    _seed_file()
    publish.enqueue("a", "publish")
    publish.enqueue("a", "unpublish")
    with db.session() as conn:
        rows = conn.execute("SELECT * FROM publish_queue").fetchall()
    assert len(rows) == 1
    assert rows[0]["intent"] == "unpublish"
    assert rows[0]["attempts"] == 0


def test_retry_infers_publish_when_still_private(isolated_store):
    _seed_file(public_state="private", publish_state="failed")
    assert publish.retry("a") is True
    with db.session() as conn:
        row = conn.execute("SELECT intent FROM publish_queue WHERE file_id='a'").fetchone()
    assert row["intent"] == "publish"


def test_retry_infers_unpublish_when_still_public(isolated_store):
    _seed_file(public_state="public", publish_state="failed")
    assert publish.retry("a") is True
    with db.session() as conn:
        row = conn.execute("SELECT intent FROM publish_queue WHERE file_id='a'").fetchone()
    assert row["intent"] == "unpublish"


def test_retry_refuses_when_nothing_failed(isolated_store):
    _seed_file(public_state="public", publish_state="published")
    assert publish.retry("a") is False
    with db.session() as conn:
        assert conn.execute("SELECT * FROM publish_queue").fetchall() == []


def test_cancel_all_clears_the_queue(isolated_store):
    _seed_file("a", "C:/x/a.txt")
    _seed_file("b", "C:/x/b.txt")
    publish.enqueue("a", "publish")
    publish.enqueue("b", "unpublish")
    publish.cancel_all()
    with db.session() as conn:
        assert conn.execute("SELECT * FROM publish_queue").fetchall() == []


# --- _publish / _unpublish (the real central call, mocked transport) --------------------


def _metadata_put(central, file_id="a"):
    """The body of the PUT /files/{id} call. Publishing also uploads chunks afterwards (E6-S6),
    so the metadata call is no longer the last one."""
    return next(body for route, body in central.calls if route == f"PUT /files/{file_id}")


def test_publish_sends_existing_tags_without_regenerating(isolated_store, central):
    _seed_file(tags='["budget", "q4"]')
    central.reply("PUT /files/a", 200, {"published_at": "p", "expires_at": "e", "last_confirmed": "c"})
    publish._publish("a")
    sent = _metadata_put(central)
    assert sent["filename"] == "a.txt"
    assert sent["tags"] == ["budget", "q4"]
    row = _file_row()
    assert row["public_state"] == "public"
    assert row["publish_state"] == "published"
    assert row["expires_at"] == "e"


def test_publish_sends_timezone_aware_timestamps(isolated_store, central):
    # Verified live 2026-10-15: file_created_at/file_modified_at are stored as naive
    # local-time strings (filesystem stat times), which central's validator rejects
    # outright (400 invalid_request) - every publish attempt was silently failing on
    # this before it was caught. The represented moment must stay correct, not just
    # gain a fake "Z" suffix.
    _seed_file()
    central.reply("PUT /files/a", 200, {"published_at": "p", "expires_at": "e", "last_confirmed": "c"})
    publish._publish("a")
    sent = _metadata_put(central)
    created = datetime.fromisoformat(sent["file_created_at"])
    modified = datetime.fromisoformat(sent["file_modified_at"])
    assert created.tzinfo is not None
    assert modified.tzinfo is not None
    # Same wall-clock moment as stored, just now explicit about which timezone.
    assert created.replace(tzinfo=None) == datetime(2026, 10, 1, 9, 0, 0)
    assert modified.replace(tzinfo=None) == datetime(2026, 10, 10, 14, 30, 0)


def test_publish_generates_tags_when_none_exist(isolated_store, central, tmp_path, monkeypatch):
    real_path = tmp_path / "a.txt"
    real_path.write_text("some budget planning content")
    _seed_file(path=str(real_path), tags=None)
    monkeypatch.setattr("app.llm.bedrock.invoke_json", lambda *a, **k: {
        "tags": ["budget", "plan", "q4", "finance", "forecast"]
    })
    central.reply(f"PUT /files/a", 200, {"published_at": "p", "expires_at": "e", "last_confirmed": "c"})
    publish._publish("a")
    assert _metadata_put(central)["tags"] == ["budget", "plan", "q4", "finance", "forecast"]


def test_publish_falls_back_to_no_tags_when_bedrock_unavailable(isolated_store, central, tmp_path):
    # No bedrock mock installed: the autouse no_real_bedrock_calls fixture makes it fail,
    # same as a real outage or missing credentials.
    real_path = tmp_path / "a.txt"
    real_path.write_text("some content")
    _seed_file(path=str(real_path), tags=None)
    central.reply("PUT /files/a", 200, {"published_at": "p", "expires_at": "e", "last_confirmed": "c"})
    publish._publish("a")  # must not raise
    assert _metadata_put(central)["tags"] == []


def test_publish_rejects_a_file_that_is_not_indexed(isolated_store, central):
    _seed_file(index_status="pending")
    with pytest.raises(Exception) as exc_info:
        publish._publish("a")
    assert exc_info.value.code == "file_unavailable"


def test_unpublish_resets_local_state(isolated_store, central):
    _seed_file(public_state="public", publish_state="published")
    central.reply("DELETE /files/a", 204)
    publish._unpublish("a")
    row = _file_row()
    assert row["public_state"] == "private"
    assert row["publish_state"] is None
    assert row["expires_at"] is None


# --- failure backoff / give-up -----------------------------------------------------------


def test_handle_failure_backs_off_before_giving_up(isolated_store):
    _seed_file(public_state="private", publish_state="pending")
    publish.enqueue("a", "publish")
    for attempt in range(config.PUBLISH_MAX_ATTEMPTS - 1):
        publish._handle_failure("a", attempt, "boom")
        with db.session() as conn:
            row = conn.execute("SELECT * FROM publish_queue WHERE file_id='a'").fetchone()
        assert row is not None, f"queue row should still exist after attempt {attempt + 1}"
        assert row["attempts"] == attempt + 1
    # One more failure reaches PUBLISH_MAX_ATTEMPTS: gives up for good.
    publish._handle_failure("a", config.PUBLISH_MAX_ATTEMPTS - 1, "boom")
    with db.session() as conn:
        assert conn.execute("SELECT * FROM publish_queue WHERE file_id='a'").fetchone() is None
    assert _file_row()["publish_state"] == "failed"


def test_process_row_end_to_end_success_removes_queue_row(isolated_store, central):
    _seed_file(tags='["a"]')
    publish.enqueue("a", "publish")
    central.reply("PUT /files/a", 200, {"published_at": "p", "expires_at": "e", "last_confirmed": "c"})
    with db.session() as conn:
        row = dict(conn.execute("SELECT * FROM publish_queue WHERE file_id='a'").fetchone())
    asyncio.run(publish._process_row(row))
    with db.session() as conn:
        assert conn.execute("SELECT * FROM publish_queue WHERE file_id='a'").fetchone() is None
    assert _file_row()["public_state"] == "public"


def test_process_row_failure_schedules_a_retry_not_a_crash(isolated_store, central):
    _seed_file(tags='["a"]')
    publish.enqueue("a", "publish")
    central.reply("PUT /files/a", 500, {"error": {"code": "internal_error", "message": "boom"}})
    with db.session() as conn:
        row = dict(conn.execute("SELECT * FROM publish_queue WHERE file_id='a'").fetchone())
    asyncio.run(publish._process_row(row))
    with db.session() as conn:
        after = conn.execute("SELECT * FROM publish_queue WHERE file_id='a'").fetchone()
    assert after is not None
    assert after["attempts"] == 1


# --- reconciliation -----------------------------------------------------------------------


def test_reconcile_adopts_centrally_public_files(isolated_store, central):
    _seed_file(public_state="private", publish_state=None)
    central.reply("GET /files/mine", 200, {"files": [
        {"file_id": "a", "tags": ["x"], "published_at": "p", "expires_at": "e", "last_confirmed": "c"}
    ]})
    publish._reconcile()
    row = _file_row()
    assert row["public_state"] == "public"
    assert json.loads(row["tags"]) == ["x"]


def test_reconcile_drops_files_no_longer_public_centrally(isolated_store, central):
    _seed_file(public_state="public", publish_state="published")
    central.reply("GET /files/mine", 200, {"files": []})
    publish._reconcile()
    row = _file_row()
    assert row["public_state"] == "private"
    assert row["publish_state"] is None


# --- folder share/unshare -----------------------------------------------------------------


def test_share_preview_counts_eligible_files_only(isolated_store):
    _seed_file("a", "C:/x/a.txt", index_status="indexed", public_state="private")
    _seed_file("b", "C:/x/b.txt", index_status="indexed", public_state="public")
    _seed_file("c", "C:/x/c.txt", index_status="pending", public_state="private")
    assert share.share_preview("f1") == 1  # only "a" is indexed and not yet public


def test_share_folder_enqueues_every_eligible_file(isolated_store):
    _seed_file("a", "C:/x/a.txt", index_status="indexed", public_state="private")
    _seed_file("b", "C:/x/b.txt", index_status="indexed", public_state="private")
    assert share.share_folder("f1") == 2
    with db.session() as conn:
        queued = {r["file_id"] for r in conn.execute("SELECT file_id FROM publish_queue").fetchall()}
    assert queued == {"a", "b"}
    assert _file_row("a")["publish_state"] == "pending"


def test_unshare_folder_only_targets_public_files(isolated_store):
    _seed_file("a", "C:/x/a.txt", public_state="public")
    _seed_file("b", "C:/x/b.txt", public_state="private")
    assert share.unshare_folder("f1") == 1
    with db.session() as conn:
        queued = {r["file_id"] for r in conn.execute("SELECT file_id FROM publish_queue").fetchall()}
    assert queued == {"a"}


# --- routes (agent-facing HTTP surface) ---------------------------------------------------


def test_publish_route_requires_team(isolated_store, client, auth, central):
    _seed_file()
    central.reply("GET /teams/me", 200, {"team": None})
    resp = client.post("/files/a/publish", headers=auth)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "no_team"


def test_publish_route_404_for_unknown_file(isolated_store, client, auth, central):
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "A"}})
    resp = client.post("/files/missing/publish", headers=auth)
    assert resp.status_code == 404


def test_publish_route_409_when_not_indexed(isolated_store, client, auth, central):
    _seed_file(index_status="pending")
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "A"}})
    resp = client.post("/files/a/publish", headers=auth)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "file_unavailable"


def test_publish_route_202_enqueues(isolated_store, client, auth, central):
    _seed_file()
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "A"}})
    resp = client.post("/files/a/publish", headers=auth)
    assert resp.status_code == 202
    assert resp.json()["publish_state"] == "pending"
    with db.session() as conn:
        row = conn.execute("SELECT intent FROM publish_queue WHERE file_id='a'").fetchone()
    assert row["intent"] == "publish"


def test_unpublish_route_202(isolated_store, client, auth):
    _seed_file(public_state="public", publish_state="published")
    resp = client.post("/files/a/unpublish", headers=auth)
    assert resp.status_code == 202
    assert resp.json()["publish_state"] == "pending"


def test_retry_route_409_when_nothing_to_retry(isolated_store, client, auth):
    _seed_file(publish_state="published")
    resp = client.post("/files/a/retry", headers=auth)
    assert resp.status_code == 409


def test_retry_route_202(isolated_store, client, auth):
    _seed_file(public_state="private", publish_state="failed")
    resp = client.post("/files/a/retry", headers=auth)
    assert resp.status_code == 202
    assert resp.json()["publish_state"] == "pending"


def test_put_tags_route_updates_and_republishes_if_public(isolated_store, client, auth):
    _seed_file(public_state="public", publish_state="published")
    resp = client.put("/files/a/tags", headers=auth, json={"tags": ["new", "tags"]})
    assert resp.status_code == 200
    assert json.loads(resp.json()["tags"]) == ["new", "tags"]
    with db.session() as conn:
        row = conn.execute("SELECT intent FROM publish_queue WHERE file_id='a'").fetchone()
    assert row["intent"] == "publish"


def test_put_tags_route_does_not_republish_private_files(isolated_store, client, auth):
    _seed_file(public_state="private")
    resp = client.put("/files/a/tags", headers=auth, json={"tags": ["new"]})
    assert resp.status_code == 200
    with db.session() as conn:
        assert conn.execute("SELECT * FROM publish_queue").fetchall() == []


def test_share_preview_route(isolated_store, client, auth):
    _seed_file("a", "C:/x/a.txt", index_status="indexed", public_state="private")
    resp = client.get("/folders/f1/share-preview", headers=auth)
    assert resp.status_code == 200
    assert resp.json() == {"file_count": 1}


def test_share_preview_route_404_for_unknown_folder(isolated_store, client, auth):
    resp = client.get("/folders/nope/share-preview", headers=auth)
    assert resp.status_code == 404


def test_share_route_requires_team(isolated_store, client, auth, central):
    _seed_file("a", "C:/x/a.txt", index_status="indexed", public_state="private")
    central.reply("GET /teams/me", 200, {"team": None})
    resp = client.post("/folders/f1/share", headers=auth)
    assert resp.status_code == 403


def test_share_route_202(isolated_store, client, auth, central):
    _seed_file("a", "C:/x/a.txt", index_status="indexed", public_state="private")
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "A"}})
    resp = client.post("/folders/f1/share", headers=auth)
    assert resp.status_code == 202
    assert resp.json() == {"queued": 1}


def test_unshare_route_202(isolated_store, client, auth):
    _seed_file("a", "C:/x/a.txt", public_state="public")
    resp = client.post("/folders/f1/unshare", headers=auth)
    assert resp.status_code == 202
    assert resp.json() == {"queued": 1}
