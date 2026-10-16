"""agent/app/central/relay.py's owner-side upload handling (docs/stories/BACKLOG.md
E4-S3). The WebSocket connection lifecycle itself needs a live two-agent test
(see the team-sharing plan) - these tests cover _handle_upload_request, the piece
that's pure request/response logic and testable the same way as the rest of the
central-calling modules.
"""
import httpx
import pytest

from app import config, db
from app.auth import session
from app.central import relay, teams


class FakeCentral:
    def __init__(self):
        self.replies = {}
        self.calls = []

    def reply(self, route, status, body=None):
        self.replies[route] = (status, body)

    def __call__(self, method, url, headers=None, timeout=None, **kw):
        route = f"{method} {url.removeprefix(config.CENTRAL_API_URL)}"
        self.calls.append((route, kw.get("json")))
        status, body = self.replies.get(route, (204, None))
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


def _seed_file(file_id, path, public_state="public"):
    with db.session() as conn:
        conn.execute("INSERT OR IGNORE INTO folders VALUES ('f1', 'C:/x', '2026-01-01T00:00:00+00:00')")
        conn.execute(
            "INSERT INTO files (file_id, folder_id, path, filename, index_status, public_state) "
            "VALUES (?, 'f1', ?, ?, 'indexed', ?)",
            (file_id, path, path.rsplit("/", 1)[-1], public_state),
        )


PAYLOAD = {
    "action": "upload_request", "transfer_id": "t1", "file_id": "a",
    "upload_url": "https://transit.test/t1", "upload_url_expires_at": "2026-10-16T00:00:00+00:00",
    "ack_deadline_seconds": 60,
}


def test_fails_not_public_for_a_private_file(isolated_store, tmp_path, central):
    path = tmp_path / "a.txt"
    path.write_text("hello")
    _seed_file("a", str(path), public_state="private")
    relay._handle_upload_request(PAYLOAD)
    sent = next(body for route, body in central.calls if route == "POST /transfers/t1/fail")
    assert sent == {"reason": "not_public"}


def test_fails_file_not_found_when_missing_locally(isolated_store, central):
    relay._handle_upload_request({**PAYLOAD, "file_id": "missing"})
    sent = next(body for route, body in central.calls if route == "POST /transfers/t1/fail")
    assert sent == {"reason": "file_not_found"}


def test_fails_file_not_found_when_path_gone_from_disk(isolated_store, tmp_path, central):
    _seed_file("a", str(tmp_path / "gone.txt"), public_state="public")
    relay._handle_upload_request(PAYLOAD)
    sent = next(body for route, body in central.calls if route == "POST /transfers/t1/fail")
    assert sent == {"reason": "file_not_found"}


def test_acks_uploads_and_completes_for_a_valid_public_file(isolated_store, tmp_path, central, monkeypatch):
    path = tmp_path / "a.txt"
    path.write_text("hello world")
    _seed_file("a", str(path), public_state="public")

    uploaded = {}

    def _fake_put(url, content=None, timeout=None):
        uploaded["url"] = url
        uploaded["body"] = b"".join(content)
        return httpx.Response(200, request=httpx.Request("PUT", url))

    monkeypatch.setattr(relay.httpx, "put", _fake_put)
    relay._handle_upload_request(PAYLOAD)

    routes = [route for route, _ in central.calls]
    assert "POST /transfers/t1/ack" in routes
    assert "POST /transfers/t1/fail" not in routes
    complete_body = next(body for route, body in central.calls if route == "POST /transfers/t1/complete")
    assert complete_body == {"size_bytes": len(b"hello world")}
    assert uploaded["url"] == PAYLOAD["upload_url"]
    assert uploaded["body"] == b"hello world"


def test_upload_error_reports_fail_not_complete(isolated_store, tmp_path, central, monkeypatch):
    path = tmp_path / "a.txt"
    path.write_text("hello world")
    _seed_file("a", str(path), public_state="public")

    def _broken_put(url, content=None, timeout=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(relay.httpx, "put", _broken_put)
    relay._handle_upload_request(PAYLOAD)

    routes = [route for route, _ in central.calls]
    assert "POST /transfers/t1/complete" not in routes
    fail_body = next(body for route, body in central.calls if route == "POST /transfers/t1/fail")
    assert fail_body == {"reason": "upload_error"}


def test_ack_failure_stops_before_uploading(isolated_store, tmp_path, central, monkeypatch):
    path = tmp_path / "a.txt"
    path.write_text("hello world")
    _seed_file("a", str(path), public_state="public")
    central.reply("POST /transfers/t1/ack", 409, {"error": {"code": "conflict", "message": "x"}})

    called = {"put": False}
    monkeypatch.setattr(relay.httpx, "put", lambda *a, **kw: called.__setitem__("put", True))
    relay._handle_upload_request(PAYLOAD)
    assert called["put"] is False


def test_state_defaults_to_disconnected():
    assert relay.state() == "disconnected"


def test_close_is_a_no_op_with_no_live_connection():
    relay.close()  # must not raise even with nothing connected
