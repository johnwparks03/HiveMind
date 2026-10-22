"""E6-S6, publish side: chunk upload after publishing, retries and permanent failures,
re-sync when a published file changes, delete sync, backfill, and the SQLite migrations.
Central is faked at the HTTP layer; embeddings are the fake 32-dim ones."""
import asyncio
import sqlite3

import httpx
import pytest

from app import config, db
from app.auth import session
from app.central import publish, teams
from app.errors import ApiError
from app.folders import scanner
from app.indexing import vector_store
from app.indexing.embeddings import embed
from test_publish import FakeCentral, _file_row, _seed_file

PUT_OK = {"published_at": "p", "expires_at": "e", "last_confirmed": "c"}


class SeqCentral(FakeCentral):
    """FakeCentral that can answer one route with a sequence of replies (the last repeats),
    and records timeouts and query params."""

    def __init__(self):
        super().__init__()
        self.sequences = {}
        self.timeouts = []
        self.params = []

    def reply_seq(self, route, *replies):
        self.sequences[route] = list(replies)

    def __call__(self, method, url, headers=None, timeout=None, **kw):
        route = f"{method} {url.removeprefix(config.CENTRAL_API_URL)}"
        self.calls.append((route, kw.get("json")))
        self.timeouts.append((route, timeout))
        self.params.append((route, kw.get("params")))
        queue = self.sequences.get(route)
        if queue:
            status, body = queue.pop(0) if len(queue) > 1 else queue[0]
        else:
            status, body = self.replies.get(route, (200, {}))
        if status == 204:
            return httpx.Response(204)
        return httpx.Response(status, json=body)

    def chunk_calls(self, file_id="a"):
        return [body for route, body in self.calls if route == f"PUT /files/{file_id}/chunks"]


@pytest.fixture
def seq(cognito_fake, keyring_fake, monkeypatch):
    session.login("a@firm.com", "Passw0rd!x")
    fake = SeqCentral()
    fake.reply("PUT /files/a", 200, PUT_OK)
    monkeypatch.setattr("app.central.client.httpx.request", fake)
    monkeypatch.setattr(config, "TEAM_CACHE_SECONDS", 0)
    teams.invalidate_cache()
    return fake


def _seed_chunks(file_id="a", n=5):
    texts = [f"chunk {i} of {file_id}" for i in range(n)]
    vector_store.upsert_chunks(file_id, texts, embed(texts), {"file_id": file_id, "filename": f"{file_id}.txt"})
    return texts


def _queue_row(file_id="a"):
    with db.session() as conn:
        row = conn.execute("SELECT * FROM publish_queue WHERE file_id=?", (file_id,)).fetchone()
    return dict(row) if row else None


def _run(file_id="a", intent="publish"):
    publish.enqueue(file_id, intent)
    asyncio.run(publish._process_row(_queue_row(file_id)))


# --- reading chunks back from Chroma ------------------------------------------------------


def test_get_file_chunks_returns_chunk_order_text_and_list_embeddings(isolated_store):
    texts = _seed_chunks("a", 4)
    _seed_chunks("other", 2)
    chunks = vector_store.get_file_chunks("a")
    assert [c[0] for c in chunks] == [0, 1, 2, 3]
    assert [c[1] for c in chunks] == texts
    assert all(isinstance(c[2], list) and isinstance(c[2][0], float) for c in chunks)
    assert chunks[2][2] == pytest.approx(embed([texts[2]])[0])


def test_get_file_chunks_pages_through_more_than_one_page(isolated_store, monkeypatch):
    monkeypatch.setattr(vector_store, "CHROMA_PAGE_SIZE", 2)
    _seed_chunks("a", 5)
    assert [c[0] for c in vector_store.get_file_chunks("a")] == [0, 1, 2, 3, 4]


def test_has_chunks(isolated_store):
    _seed_chunks("a", 1)
    assert vector_store.has_chunks("a") and not vector_store.has_chunks("nope")


# --- uploading after publish --------------------------------------------------------------


def test_publish_uploads_chunks_in_batches_after_the_metadata(isolated_store, seq, monkeypatch):
    monkeypatch.setattr(config, "CHUNK_UPLOAD_BATCH_SIZE", 2)
    _seed_file()
    texts = _seed_chunks("a", 5)
    publish._publish("a")
    routes = [route for route, _ in seq.calls]
    assert routes == ["PUT /files/a", "PUT /files/a/chunks", "PUT /files/a/chunks", "PUT /files/a/chunks"]
    bodies = seq.chunk_calls()
    assert [(b["batch"], b["total_batches"]) for b in bodies] == [(1, 3), (2, 3), (3, 3)]
    assert [[c["chunk_index"] for c in b["chunks"]] for b in bodies] == [[0, 1], [2, 3], [4]]
    assert bodies[0]["chunks"][0]["text"] == texts[0]
    assert len(bodies[0]["chunks"][0]["embedding"]) == len(embed(["x"])[0])
    assert {t for route, t in seq.timeouts if route.endswith("/chunks")} == {config.CHUNK_UPLOAD_TIMEOUT_SECONDS}
    assert _file_row()["public_state"] == "public"


def test_a_file_with_no_chunks_uploads_an_empty_set_to_clear_old_ones(isolated_store, seq):
    _seed_file()
    publish._publish("a")
    assert seq.chunk_calls() == [{"chunks": [], "batch": 1, "total_batches": 1}]


def test_only_the_first_max_chunks_are_uploaded(isolated_store, seq, monkeypatch):
    monkeypatch.setattr(config, "MAX_CHUNKS_PER_FILE", 3)
    _seed_file()
    _seed_chunks("a", 5)
    publish._publish("a")
    bodies = seq.chunk_calls()
    assert [c["chunk_index"] for b in bodies for c in b["chunks"]] == [0, 1, 2]
    assert bodies[0]["total_batches"] == 1


def test_a_gap_in_the_chunks_means_a_reindex_is_in_progress_and_nothing_is_sent(isolated_store, seq):
    _seed_file()
    _seed_chunks("a", 3)
    vector_store.get_collection().delete(ids=["a::1"])
    with pytest.raises(ApiError) as exc_info:
        publish._publish("a")
    assert exc_info.value.status == 503 and seq.chunk_calls() == []


def test_a_retry_after_a_failed_batch_starts_again_from_batch_one(isolated_store, seq, monkeypatch):
    monkeypatch.setattr(config, "CHUNK_UPLOAD_BATCH_SIZE", 2)
    _seed_file()
    _seed_chunks("a", 4)
    seq.reply_seq("PUT /files/a/chunks", (200, {}), (503, {"error": {"code": "service_unavailable", "message": "x"}}),
                  (200, {}))
    _run()
    assert _queue_row()["attempts"] == 1  # the second batch failed: retry later
    first_pass = [(b["batch"]) for b in seq.chunk_calls()]
    assert first_pass == [1, 2]
    seq.sequences["PUT /files/a/chunks"] = [(200, {})]
    asyncio.run(publish._process_row(_queue_row()))
    assert [(b["batch"]) for b in seq.chunk_calls()][2:] == [1, 2]
    assert _queue_row() is None


@pytest.mark.parametrize("status,code", [(400, "invalid_request"), (404, "not_found"), (403, "forbidden")])
def test_a_permanent_chunk_rejection_fails_the_file_at_once(isolated_store, seq, status, code):
    _seed_file()
    _seed_chunks("a", 2)
    seq.reply("PUT /files/a/chunks", status, {"error": {"code": code, "message": "no"}})
    _run()
    row = _file_row()
    assert row["publish_state"] == "failed" and row["publish_failed_intent"] == "publish"
    assert _queue_row() is None
    assert len(seq.chunk_calls()) == 1  # not retried


def test_a_transient_chunk_failure_is_retried_with_backoff(isolated_store, seq):
    _seed_file()
    _seed_chunks("a", 2)
    seq.reply("PUT /files/a/chunks", 503, {"error": {"code": "service_unavailable", "message": "x"}})
    _run()
    queued = _queue_row()
    assert queued["attempts"] == 1 and queued["last_error"]
    assert _file_row()["publish_state"] != "failed"


def test_a_success_clears_the_failed_intent(isolated_store, seq):
    _seed_file(publish_state="failed")
    with db.session() as conn:
        conn.execute("UPDATE files SET publish_failed_intent='publish' WHERE file_id='a'")
    _run()
    assert _file_row()["publish_failed_intent"] is None and _file_row()["publish_state"] == "published"


# --- retry() picks the direction that failed ----------------------------------------------


@pytest.mark.parametrize("public_state,failed_intent,expected", [
    ("public", "publish", "publish"),      # chunk upload failed: re-upload, never unpublish
    ("public", "unpublish", "unpublish"),
    ("private", "publish", "publish"),
    ("public", None, "unpublish"),         # rows from before the column existed
    ("private", None, "publish"),
])
def test_retry_redoes_the_direction_that_failed(isolated_store, public_state, failed_intent, expected):
    _seed_file(public_state=public_state, publish_state="failed")
    with db.session() as conn:
        conn.execute("UPDATE files SET publish_failed_intent=? WHERE file_id='a'", (failed_intent,))
    assert publish.retry("a") is True
    assert _queue_row()["intent"] == expected


def test_an_unpublish_that_fails_for_good_remembers_its_direction(isolated_store, seq):
    _seed_file(public_state="public", publish_state="pending")
    seq.reply("DELETE /files/a", 400, {"error": {"code": "invalid_request", "message": "x"}})
    publish.enqueue("a", "unpublish")
    for _ in range(config.PUBLISH_MAX_ATTEMPTS):
        asyncio.run(publish._process_row(_queue_row()))  # each failure bumps attempts
        if _file_row()["publish_state"] == "failed":
            break
    assert _file_row()["publish_failed_intent"] == "unpublish"


# --- backfill and pagination in reconcile -------------------------------------------------


def _remote(file_id, chunk_count=0, **extra):
    return {"file_id": file_id, "filename": f"{file_id}.txt", "published_at": "p", "expires_at": "e",
            "last_confirmed": "c", "chunk_count": chunk_count, **extra}


def test_reconcile_queues_an_upload_for_published_files_central_has_no_chunks_for(isolated_store, seq):
    _seed_file("a", path="C:/x/a.txt", public_state="public", publish_state="published")
    _seed_chunks("a", 2)
    seq.reply("GET /files/mine", 200, {"files": [_remote("a", 0)], "next_cursor": None})
    publish._reconcile()
    assert _queue_row("a")["intent"] == "publish"


@pytest.mark.parametrize("remote_count,setup", [
    (3, {}),                                   # central already has chunks
    (None, {}),                                # an older central that does not report chunk_count
    (0, {"publish_state": "failed"}),          # gave up on it: the user retries explicitly
    (0, {"index_status": "failed"}),
    (0, {"no_chunks": True}),                  # nothing local to send (an empty file)
])
def test_reconcile_does_not_upload_when_there_is_nothing_to_backfill(isolated_store, seq, remote_count, setup):
    _seed_file("a", path="C:/x/a.txt", public_state="public",
               publish_state=setup.get("publish_state", "published"),
               index_status=setup.get("index_status", "indexed"))
    if not setup.get("no_chunks"):
        _seed_chunks("a", 2)
    remote = _remote("a", remote_count)
    if remote_count is None:
        del remote["chunk_count"]
    seq.reply("GET /files/mine", 200, {"files": [remote], "next_cursor": None})
    publish._reconcile()
    assert _queue_row("a") is None


def test_reconcile_never_resets_the_backoff_of_a_file_already_queued(isolated_store, seq):
    _seed_file("a", path="C:/x/a.txt", public_state="public", publish_state="published")
    _seed_chunks("a", 2)
    publish.enqueue("a", "publish")
    with db.session() as conn:
        conn.execute("UPDATE publish_queue SET attempts=3, last_error='boom' WHERE file_id='a'")
    seq.reply("GET /files/mine", 200, {"files": [_remote("a", 0)], "next_cursor": None})
    publish._reconcile()
    assert _queue_row("a")["attempts"] == 3


def test_reconcile_follows_every_page_of_files_mine(isolated_store, seq):
    _seed_file("a", path="C:/x/a.txt", public_state="public", publish_state="published")
    _seed_file("b", path="C:/x/b.txt", public_state="private")
    seq.reply_seq("GET /files/mine",
                  (200, {"files": [_remote("a", 1)], "next_cursor": "cur1"}),
                  (200, {"files": [_remote("b", 1)], "next_cursor": None}))
    publish._reconcile()
    assert [p for route, p in seq.params if route == "GET /files/mine"] == [None, {"cursor": "cur1"}]
    assert _file_row("b")["public_state"] == "public"  # adopted from the second page
    assert _file_row("a")["public_state"] == "public"  # and 'a' was not wrongly un-published


def test_reconcile_skips_the_round_when_central_is_unreachable(isolated_store, seq):
    _seed_file("a", path="C:/x/a.txt", public_state="public", publish_state="published")
    seq.reply("GET /files/mine", 503, {"error": {"code": "service_unavailable", "message": "x"}})
    publish._reconcile()
    assert _file_row("a")["public_state"] == "public"


# --- keeping central in step with local changes (scanner) ---------------------------------


@pytest.fixture
def library(isolated_store, tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("alpha budget notes for the quarter")
    folder_id = scanner.add_folder(str(folder))
    with db.session() as conn:
        file_id = conn.execute("SELECT file_id FROM files").fetchone()["file_id"]
    return {"folder": folder, "folder_id": folder_id, "file_id": file_id}


def _make_public(file_id, public_state="public", publish_state="published"):
    with db.session() as conn:
        conn.execute("UPDATE files SET public_state=?, publish_state=? WHERE file_id=?",
                     (public_state, publish_state, file_id))


def test_editing_a_published_file_requeues_its_metadata_and_chunks(library):
    _make_public(library["file_id"])
    (library["folder"] / "a.txt").write_text("alpha budget notes, revised after the review")
    scanner.scan_folder(library["folder_id"], str(library["folder"]))
    assert _queue_row(library["file_id"])["intent"] == "publish"
    assert _file_row(library["file_id"])["publish_state"] == "pending"


def test_editing_a_private_file_queues_nothing(library):
    (library["folder"] / "a.txt").write_text("a private edit")
    scanner.scan_folder(library["folder_id"], str(library["folder"]))
    assert _queue_row(library["file_id"]) is None


def test_an_unchanged_published_file_queues_nothing(library):
    _make_public(library["file_id"])
    scanner.scan_folder(library["folder_id"], str(library["folder"]))
    assert _queue_row(library["file_id"]) is None


def test_a_published_file_that_can_no_longer_be_indexed_is_pulled_back(library, monkeypatch):
    _make_public(library["file_id"])
    (library["folder"] / "a.txt").write_text("now unreadable")
    monkeypatch.setattr("app.folders.scanner.index_file", lambda **kw: {
        "index_status": "failed", "index_failure_reason": "boom", "in_document_date": None, "excerpt": None})
    scanner.scan_folder(library["folder_id"], str(library["folder"]))
    assert _queue_row(library["file_id"])["intent"] == "unpublish"


def test_a_published_file_deleted_from_disk_is_unpublished_after_its_row_is_gone(library):
    _make_public(library["file_id"])
    (library["folder"] / "a.txt").unlink()
    stats = scanner.scan_folder(library["folder_id"], str(library["folder"]))
    assert stats["removed"] == 1
    with db.session() as conn:
        assert conn.execute("SELECT COUNT(*) FROM files").fetchone()[0] == 0
    assert _queue_row(library["file_id"])["intent"] == "unpublish"


def test_removing_a_published_file_from_hivemind_unpublishes_it(library):
    _make_public(library["file_id"])
    assert scanner.exclude_files([library["file_id"]]) == 1
    assert _queue_row(library["file_id"])["intent"] == "unpublish"


def test_removing_a_folder_unpublishes_its_published_files(library):
    _make_public(library["file_id"])
    assert scanner.remove_folder(library["folder_id"]) is True
    assert _queue_row(library["file_id"])["intent"] == "unpublish"


def test_a_file_whose_publish_is_still_queued_is_also_cancelled_centrally(library):
    _make_public(library["file_id"], public_state="private", publish_state="pending")
    publish.enqueue(library["file_id"], "publish")
    scanner.exclude_files([library["file_id"]])
    assert _queue_row(library["file_id"])["intent"] == "unpublish"  # replaced the pending publish


def test_deleting_private_files_tells_central_nothing(library):
    scanner.exclude_files([library["file_id"]])
    scanner.remove_folder(library["folder_id"])
    assert _queue_row(library["file_id"]) is None


def test_a_queued_unpublish_for_a_deleted_file_still_reaches_central(library, seq):
    _make_public(library["file_id"])
    seq.reply(f"DELETE /files/{library['file_id']}", 204)
    scanner.exclude_files([library["file_id"]])
    asyncio.run(publish._process_row(_queue_row(library["file_id"])))
    assert (f"DELETE /files/{library['file_id']}", None) in seq.calls
    assert _queue_row(library["file_id"]) is None


# --- SQLite migrations ----------------------------------------------------------------------

OLD_SCHEMA = """
CREATE TABLE folders (folder_id TEXT PRIMARY KEY, path TEXT, added_at TEXT);
CREATE TABLE files (file_id TEXT PRIMARY KEY, folder_id TEXT, path TEXT UNIQUE, filename TEXT,
                    public_state TEXT NOT NULL DEFAULT 'private', publish_state TEXT);
CREATE TABLE publish_queue (
    file_id TEXT PRIMARY KEY REFERENCES files(file_id),
    intent TEXT NOT NULL CHECK (intent IN ('publish', 'unpublish')),
    attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at TEXT NOT NULL, last_error TEXT);
INSERT INTO folders (folder_id, path, added_at) VALUES ('f', 'C:/x', 't');
INSERT INTO files (file_id, folder_id, path, filename) VALUES ('a', 'f', 'C:/x/a.txt', 'a.txt');
INSERT INTO publish_queue VALUES ('a', 'publish', 2, '2026-01-01T00:00:00+00:00', 'boom');
"""


def test_init_db_upgrades_an_existing_database_without_losing_queued_work(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(OLD_SCHEMA)
    conn.commit()
    conn.close()
    monkeypatch.setattr(db, "SQLITE_PATH", path)
    db.init_db()
    db.init_db()  # idempotent
    with db.session() as c:
        assert c.execute("PRAGMA foreign_key_list(publish_queue)").fetchall() == []
        kept = dict(c.execute("SELECT * FROM publish_queue").fetchone())
        assert kept["attempts"] == 2 and kept["last_error"] == "boom" and kept["intent"] == "publish"
        assert "publish_failed_intent" in {r["name"] for r in c.execute("PRAGMA table_info(files)")}
        c.execute("DELETE FROM files WHERE file_id='a'")  # no foreign key: the queue row survives
        assert c.execute("SELECT COUNT(*) FROM publish_queue").fetchone()[0] == 1


def test_a_fresh_database_has_no_queue_foreign_key_and_the_new_column(isolated_store):
    with db.session() as c:
        assert c.execute("PRAGMA foreign_key_list(publish_queue)").fetchall() == []
        assert "publish_failed_intent" in {r["name"] for r in c.execute("PRAGMA table_info(files)")}
