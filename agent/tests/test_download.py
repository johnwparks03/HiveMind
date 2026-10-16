"""agent/app/central/download.py: requester-side download (docs/stories/BACKLOG.md
E4-S4/S5). FakeCentral pattern matches test_publish.py / test_search_teammates.py.
"""
import httpx
import pytest

from app import config, db
from app.auth import session
from app.central import download, teams
from app.errors import ApiError


class FakeCentral:
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


@pytest.fixture
def downloads_dir(tmp_path, monkeypatch):
    folder = tmp_path / "Downloads"
    monkeypatch.setattr(download, "downloads_folder", lambda: folder)
    return folder


def _row(transfer_id):
    with db.session() as conn:
        row = conn.execute("SELECT * FROM downloads WHERE transfer_id = ?", (transfer_id,)).fetchone()
    return dict(row) if row else None


def test_request_download_creates_a_local_row(isolated_store, central):
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    row = download.request_download("f1", "notes.docx")
    assert row["transfer_id"] == "t1"
    assert row["file_id"] == "f1"
    assert row["filename"] == "notes.docx"
    assert row["status"] == "requested"
    assert row["saved_path"] is None


def test_request_download_twice_updates_not_duplicates(isolated_store, central):
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    download.request_download("f1", "notes.docx")
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})  # central reused it
    download.request_download("f1", "notes.docx")
    assert len(download.list_downloads()) == 1


def test_request_download_propagates_owner_offline(isolated_store, central):
    central.reply("POST /transfers", 409, {"error": {"code": "owner_offline", "message": "offline"}})
    with pytest.raises(ApiError) as exc:
        download.request_download("f1", "notes.docx")
    assert exc.value.code == "owner_offline"


def test_poll_updates_status_while_in_flight(isolated_store, central):
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    download.request_download("f1", "notes.docx")
    central.reply("GET /transfers/t1", 200, {"transfer_id": "t1", "status": "uploading", "error_code": None})
    download._poll_one(_row("t1"))
    assert _row("t1")["status"] == "uploading"


class _FakeStreamResponse:
    def __init__(self, data: bytes):
        self._data = data

    def raise_for_status(self):
        pass

    def iter_bytes(self, chunk_size):
        yield self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_poll_downloads_the_file_once_ready(isolated_store, central, downloads_dir, monkeypatch):
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    download.request_download("f1", "notes.docx")
    central.reply("GET /transfers/t1", 200, {
        "transfer_id": "t1", "status": "ready",
        "download_url": "https://transit.test/t1", "error_code": None,
    })
    monkeypatch.setattr(
        download.httpx, "stream",
        lambda method, url, timeout=None: _FakeStreamResponse(b"hello world"),
    )
    download._poll_one(_row("t1"))

    row = _row("t1")
    assert row["status"] == "downloaded"
    saved = downloads_dir / "notes.docx"
    assert row["saved_path"] == str(saved)
    assert saved.read_bytes() == b"hello world"


def test_poll_suffixes_filename_on_collision(isolated_store, central, downloads_dir, monkeypatch):
    downloads_dir.mkdir(parents=True)
    (downloads_dir / "notes.docx").write_bytes(b"existing")
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    download.request_download("f1", "notes.docx")
    central.reply("GET /transfers/t1", 200, {
        "transfer_id": "t1", "status": "ready",
        "download_url": "https://transit.test/t1", "error_code": None,
    })
    monkeypatch.setattr(
        download.httpx, "stream",
        lambda method, url, timeout=None: _FakeStreamResponse(b"new content"),
    )
    download._poll_one(_row("t1"))

    row = _row("t1")
    assert row["saved_path"] == str(downloads_dir / "notes (1).docx")
    assert (downloads_dir / "notes.docx").read_bytes() == b"existing"


def test_unique_path_suffixes_on_collision(tmp_path):
    folder = tmp_path
    (folder / "notes.docx").write_text("x")
    assert download._unique_path(folder, "notes.docx").name == "notes (1).docx"
    (folder / "notes (1).docx").write_text("x")
    assert download._unique_path(folder, "notes.docx").name == "notes (2).docx"


def test_poll_marks_failed_on_404(isolated_store, central):
    central.reply("POST /transfers", 202, {"transfer_id": "t1", "status": "requested"})
    download.request_download("f1", "notes.docx")
    central.reply("GET /transfers/t1", 404, {"error": {"code": "not_found", "message": "gone"}})
    download._poll_one(_row("t1"))
    row = _row("t1")
    assert row["status"] == "failed"
    assert row["error_code"] == "download_failed"
