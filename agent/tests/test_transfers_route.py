"""agent/app/api/routes_transfers.py (API_Contract.md section 2.6): the thin HTTP
layer over download.py. Same FakeCentral/local_db pattern as test_team.py.
"""
import httpx
import pytest

from app import config, db
from app.auth import session
from app.central import teams


class FakeCentral:
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
    return db


def test_post_transfers_returns_202_and_the_row(client, auth, central, local_db):
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    resp = client.post("/transfers", headers=auth, json={"file_id": "f1", "filename": "notes.docx"})
    assert resp.status_code == 202
    body = resp.json()
    assert body["transfer_id"] == "t1"
    assert body["filename"] == "notes.docx"
    assert body["status"] == "requested"


def test_post_transfers_maps_central_errors(client, auth, central, local_db):
    central.reply("POST /transfers", 409, {"error": {"code": "owner_offline", "message": "offline"}})
    resp = client.post("/transfers", headers=auth, json={"file_id": "f1"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "owner_offline"


def test_get_transfers_lists_local_rows(client, auth, central, local_db):
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    client.post("/transfers", headers=auth, json={"file_id": "f1", "filename": "notes.docx"})
    resp = client.get("/transfers", headers=auth)
    assert resp.status_code == 200
    assert len(resp.json()["transfers"]) == 1


def test_get_one_transfer_404_when_unknown(client, auth, local_db):
    resp = client.get("/transfers/does-not-exist", headers=auth)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
