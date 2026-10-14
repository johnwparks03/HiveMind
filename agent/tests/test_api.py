"""The HTTP surface the frontend uses (API_Contract.md section 2.1), checked against a corpus.

These pin the response shapes in frontend/src/api/client.js and lib/files.js, so a change
on either side shows up here first.
"""
from pathlib import Path

import pytest

from corpus_generator import TOTAL_DOCX, TOTAL_PPTX


@pytest.fixture
def client(isolated_store):
    from fastapi.testclient import TestClient

    from app.auth.security import STARTUP_TOKEN
    from app.main import app

    test_client = TestClient(app)
    test_client.headers.update({"X-HiveMind-Token": STARTUP_TOKEN})
    return test_client


FRONTEND_ORIGIN = "http://localhost:5173"


def test_token_endpoint_only_answers_the_frontend_origin(client):
    assert client.get("/auth/token", headers={"Origin": FRONTEND_ORIGIN}).status_code == 200

    other = client.get("/auth/token", headers={"Origin": "http://evil.example"})
    assert other.status_code == 403
    assert other.json()["error"]["code"] == "forbidden"


def test_other_endpoints_need_the_token(client):
    anonymous = client.get("/folders", headers={"X-HiveMind-Token": ""})
    assert anonymous.status_code == 401
    assert anonymous.json()["error"]["code"] == "unauthorized"
    assert client.get("/folders").status_code == 200


def test_adding_a_folder_indexes_the_whole_corpus(client, corpus):
    root, _ = corpus
    created = client.post("/folders", json={"path": str(root)})
    assert created.status_code == 200
    folder_id = created.json()["folder_id"]

    folders = client.get("/folders").json()["folders"]
    assert [f["folder_id"] for f in folders] == [folder_id]

    files = client.get("/files").json()["files"]
    assert len(files) == TOTAL_DOCX + TOTAL_PPTX + 3
    for f in files:
        assert f["index_status"] in {"pending", "indexed", "failed"}
        assert f["folder_id"] == folder_id
        assert f["filename"] == Path(f["path"]).name


def test_failed_files_carry_a_reason(client, corpus):
    root, _ = corpus
    client.post("/folders", json={"path": str(root)})
    failed = [f for f in client.get("/files").json()["files"] if f["index_status"] == "failed"]

    assert {f["filename"] for f in failed} == {"Blank document.docx", "Corrupt export.docx"}
    assert all(f["index_failure_reason"] for f in failed)


def test_search_response_has_the_fields_the_ui_renders(client, corpus):
    root, _ = corpus
    client.post("/folders", json={"path": str(root)})

    body = client.post("/search", json={"query": "budget plan from last week"}).json()
    assert {"interpreted", "local_results", "teammate"} <= body.keys()
    assert {"topic", "date_from", "date_to", "source"} <= body["interpreted"].keys()
    for r in body["local_results"]:
        assert {"file_id", "filename", "path", "snippet", "score"} <= r.keys()


def test_bad_folder_path_is_rejected_with_an_error_code(client):
    response = client.post("/folders", json={"path": "C:\\definitely\\not\\a\\folder"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_request"


def test_removing_an_unknown_folder_is_a_404(client):
    response = client.delete("/folders/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_rescan_reports_stats(client, corpus):
    root, _ = corpus
    folder_id = client.post("/folders", json={"path": str(root)}).json()["folder_id"]

    response = client.post(f"/folders/{folder_id}/rescan")
    assert response.status_code == 200
    assert response.json()["stats"]["unchanged"] == TOTAL_DOCX + TOTAL_PPTX + 3

def test_pick_folder_returns_the_chosen_path_and_null_on_cancel(client, monkeypatch):
    from app.folders import picker

    monkeypatch.setattr(picker, "pick_folder", lambda: "C:\\Notes")
    chosen = client.post("/folders/pick")
    assert chosen.status_code == 200
    assert chosen.json() == {"path": "C:\\Notes"}

    monkeypatch.setattr(picker, "pick_folder", lambda: None)
    cancelled = client.post("/folders/pick")
    assert cancelled.status_code == 200
    assert cancelled.json() == {"path": None}

def test_remove_files_endpoint_reports_how_many_were_removed(client, corpus):
    root, _ = corpus
    folder_id = client.post("/folders", json={"path": str(root)}).json()["folder_id"]
    files = client.get("/files").json()["files"]
    readable = next(f for f in files if f["index_status"] == "indexed")

    response = client.post("/files/remove", json={"file_ids": [readable["file_id"]]})
    assert response.status_code == 200
    assert response.json() == {"removed": 1}
    assert all(f["file_id"] != readable["file_id"] for f in client.get("/files").json()["files"])
