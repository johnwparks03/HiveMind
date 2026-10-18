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

    def _fake_put(url, content=None, headers=None, timeout=None):
        uploaded["url"] = url
        uploaded["body"] = b"".join(content)
        uploaded["headers"] = headers
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
    assert uploaded["headers"] == {"Content-Length": "11"}  # S3 needs the size up front


def test_upload_error_reports_fail_not_complete(isolated_store, tmp_path, central, monkeypatch):
    path = tmp_path / "a.txt"
    path.write_text("hello world")
    _seed_file("a", str(path), public_state="public")

    def _broken_put(url, content=None, headers=None, timeout=None):
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


# --- the real upload request, against a local server standing in for S3 ---------------------------------


def _serve_puts():
    """A local HTTP server that records how each PUT arrives, as S3 would see it."""
    import http.server
    import threading

    seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_PUT(self):
            headers = {k.lower(): v for k, v in self.headers.items()}
            if headers.get("transfer-encoding", "").lower() == "chunked":
                # What S3 rejects with 501 NotImplemented.
                seen.append({"chunked": True, "body": b""})
                self.send_response(501)
                self.send_header("Content-Type", "application/xml")
                body = b"<Error><Code>NotImplemented</Code><Message>chunked</Message></Error>"
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            body = self.rfile.read(int(headers["content-length"]))
            seen.append({"chunked": False, "content_length": int(headers["content-length"]), "body": body})
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, seen


def test_the_upload_goes_out_with_a_content_length_not_chunked(isolated_store, tmp_path, central, monkeypatch):
    # A bare generator makes httpx send Transfer-Encoding: chunked, which S3 refuses for a presigned PUT.
    monkeypatch.setattr(config, "TRANSFER_UPLOAD_CHUNK_BYTES", 4)  # several pieces, still one declared length
    path = tmp_path / "a.txt"
    path.write_bytes(b"hello world, streamed in small pieces")
    _seed_file("a", str(path), public_state="public")
    server, seen = _serve_puts()
    try:
        relay._handle_upload_request({**PAYLOAD, "upload_url": f"http://127.0.0.1:{server.server_port}/key"})
    finally:
        server.shutdown()

    assert seen == [{"chunked": False, "content_length": 37, "body": b"hello world, streamed in small pieces"}]
    routes = [route for route, _ in central.calls]
    assert "POST /transfers/t1/complete" in routes and "POST /transfers/t1/fail" not in routes


def test_a_refused_upload_is_logged_with_its_status_but_never_the_url(isolated_store, tmp_path, central, monkeypatch, caplog):
    path = tmp_path / "a.txt"
    path.write_text("hello world")
    _seed_file("a", str(path), public_state="public")

    def _refused(url, content=None, headers=None, timeout=None):
        request = httpx.Request("PUT", url)
        return httpx.Response(501, request=request, text="<Error><Code>NotImplemented</Code></Error>")

    monkeypatch.setattr(relay.httpx, "put", _refused)
    with caplog.at_level("WARNING", logger="app.central.relay"):
        relay._handle_upload_request({**PAYLOAD, "upload_url": "https://bucket.example/key?X-Amz-Signature=SECRET"})

    assert "HTTP 501 NotImplemented" in caplog.text
    assert "SECRET" not in caplog.text and "X-Amz-Signature" not in caplog.text
    assert any(route == "POST /transfers/t1/fail" for route, _ in central.calls)


def test_describe_upload_error_names_the_kind_of_failure():
    assert relay._describe_upload_error(httpx.ConnectError("x")) == "ConnectError"
    refused = httpx.HTTPStatusError(
        "x", request=httpx.Request("PUT", "https://b/k"), response=httpx.Response(403, text="<Code>AccessDenied</Code>"))
    assert relay._describe_upload_error(refused) == "HTTP 403 AccessDenied"
    plain = httpx.HTTPStatusError("x", request=httpx.Request("PUT", "https://b/k"), response=httpx.Response(500, text="oops"))
    assert relay._describe_upload_error(plain) == "HTTP 500"
