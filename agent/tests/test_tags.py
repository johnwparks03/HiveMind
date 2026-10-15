"""On-demand local tag generation. Validation logic (clean_tags) mirrors
central/lambdas/llm.py's proven version; this pins the agent's copy stays correct,
and that POST /files/{id}/tags/generate wires it up with the right error codes.
"""
import json

import pytest

from app.folders.scanner import add_folder
from app.llm import bedrock
from app.llm.tags import clean_tags

GOOD = ["contracts", "renewal", "pricing", "client", "legal", "q3"]


def test_clean_tags_accepts_a_good_reply():
    assert clean_tags(GOOD) == GOOD


def test_clean_tags_rejects_too_few():
    assert clean_tags(["one", "two"]) is None


def test_clean_tags_dedupes_and_lowercases():
    assert clean_tags(["Budget", "budget", "Plan", "Q4", "Q4", "Notes", "Team"]) == [
        "budget", "plan", "q4", "notes", "team",
    ]


def test_clean_tags_trims_to_the_max():
    nine = [f"tag{i}" for i in range(9)]
    assert len(clean_tags(nine)) == 8


def test_clean_tags_rejects_non_string_or_non_list():
    assert clean_tags("not a list") is None
    assert clean_tags(["ok", 123, "fine", "more", "tags"]) is None


@pytest.fixture
def client(isolated_store, corpus):
    from fastapi.testclient import TestClient

    from app.auth.security import STARTUP_TOKEN
    from app.main import app

    root, _ = corpus
    add_folder(str(root))
    test_client = TestClient(app)
    test_client.headers.update({"X-HiveMind-Token": STARTUP_TOKEN})
    return test_client


def _first_file_id(client):
    files = client.get("/files").json()["files"]
    return next(f["file_id"] for f in files if f["index_status"] == "indexed")


def test_generate_tags_happy_path(client, monkeypatch):
    monkeypatch.setattr(bedrock, "invoke_json", lambda *a, **k: {"tags": GOOD})
    file_id = _first_file_id(client)

    resp = client.post(f"/files/{file_id}/tags/generate")
    assert resp.status_code == 200
    assert resp.json() == {"file_id": file_id, "tags": GOOD}

    stored = client.get("/files").json()["files"]
    row = next(f for f in stored if f["file_id"] == file_id)
    assert json.loads(row["tags"]) == GOOD


def test_generate_tags_rejects_bad_model_output(client, monkeypatch):
    monkeypatch.setattr(bedrock, "invoke_json", lambda *a, **k: {"tags": ["x"]})
    file_id = _first_file_id(client)

    resp = client.post(f"/files/{file_id}/tags/generate")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "service_unavailable"


def test_generate_tags_unknown_file_is_404(client):
    resp = client.post("/files/not-a-real-id/tags/generate")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_generate_tags_without_aws_credentials_is_503(client, monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    file_id = _first_file_id(client)

    resp = client.post(f"/files/{file_id}/tags/generate")
    assert resp.status_code == 503
    assert resp.json()["error"]["details"]["missing"] == "AWS_ACCESS_KEY_ID"


# --- Automatic tagging on add/rescan (scanner.py, 2026-10-15) ---------------------------


def test_add_folder_tags_files_automatically(isolated_store, corpus, monkeypatch):
    monkeypatch.setattr(bedrock, "invoke_json", lambda *a, **k: {"tags": GOOD})
    root, _ = corpus
    add_folder(str(root))

    from app.db import session as db_session

    with db_session() as conn:
        rows = conn.execute(
            "SELECT tags FROM files WHERE index_status = 'indexed'"
        ).fetchall()
    assert rows, "expected at least one indexed file"
    assert all(json.loads(r["tags"]) == GOOD for r in rows)


def test_tag_generation_failure_does_not_fail_the_scan(isolated_store, corpus):
    # No mock installed: the autouse no_real_bedrock_calls fixture makes every
    # Bedrock call fail, same as a real outage or missing credentials would.
    root, _ = corpus
    from app.db import session as db_session

    add_folder(str(root))
    with db_session() as conn:
        rows = conn.execute("SELECT index_status, tags FROM files").fetchall()
    assert any(r["index_status"] == "indexed" for r in rows)
    assert all(r["tags"] is None for r in rows)


def test_rescan_tags_an_already_indexed_but_untagged_file(isolated_store, corpus, monkeypatch):
    from app.db import session as db_session
    from app.folders.scanner import scan_folder

    root, _ = corpus
    # First pass: Bedrock unavailable (autouse default) -> indexed but untagged.
    folder_id = add_folder(str(root))
    with db_session() as conn:
        before = conn.execute("SELECT file_id, content_hash, tags, index_status FROM files").fetchall()
    indexed_before = [r for r in before if r["index_status"] == "indexed"]
    assert indexed_before, "expected at least one indexed file"
    assert all(r["tags"] is None for r in before)

    # Rescan with Bedrock now working: files are unchanged (same content hash), so
    # this must retag them without a full re-index.
    monkeypatch.setattr(bedrock, "invoke_json", lambda *a, **k: {"tags": GOOD})
    stats = scan_folder(folder_id, str(root))
    assert stats["unchanged"] == len(before)
    assert stats["reindexed"] == 0 and stats["added"] == 0

    with db_session() as conn:
        after = conn.execute("SELECT file_id, content_hash, tags FROM files").fetchall()
    after_by_id = {r["file_id"]: r for r in after}
    # Files that extracted fine the first time get tagged on rescan, without a
    # full re-index (content hash is unchanged).
    for row in indexed_before:
        assert after_by_id[row["file_id"]]["content_hash"] == row["content_hash"]
        assert json.loads(after_by_id[row["file_id"]]["tags"]) == GOOD
    # Files that never had extractable content (e.g. a corrupt/blank doc) have
    # nothing to tag and correctly stay untagged.
    for row in before:
        if row["index_status"] != "indexed":
            assert after_by_id[row["file_id"]]["tags"] is None
