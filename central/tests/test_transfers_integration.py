"""Integration tests for E4-S2 against the deployed HiveMind stack.

Run: pytest -m integration tests/test_transfers_integration.py   (needs `aws login`; the stack must
include the Transfer API and relay WebSocket). The owner holds a real WebSocket open, uploads
through the presigned PUT URL and the requester downloads through the presigned GET URL, so this
is the end-to-end relay path. The slow test waits out the 60 s ack timeout; skip it with
`-m "integration and not slow"`. Tokens and URLs are never printed.
"""
import asyncio
import json
import time
import urllib.error
import urllib.request
import uuid

import pytest
from websockets.asyncio.client import connect

from test_auth_integration import cfg, cognito  # noqa: F401
from test_relay_integration import _headers, ws_url  # noqa: F401
from test_search_integration import _publish  # noqa: F401
from test_teams_integration import _call, make_user  # noqa: F401

pytestmark = pytest.mark.integration

FILE = {"filename": "transfer-probe.docx", "tags": ["probe"]}
PAYLOAD = b"HiveMind transfer probe \x00\x01\x02 " * 1000


@pytest.fixture
def team_of_two(cfg, make_user):  # noqa: F811
    requester, owner = make_user(), make_user()
    _call(cfg, "POST", "/teams", requester, {"name": "Transfer test"})
    code = _call(cfg, "POST", "/teams/me/invites", requester)[1]["code"]
    assert _call(cfg, "POST", "/teams/join", owner, {"code": code})[0] == 200
    yield requester, owner
    for token in (owner, requester):
        _call(cfg, "POST", "/teams/me/leave", token)


def _http(method, url, data=None, content_type=None):
    req = urllib.request.Request(url, method=method, data=data)
    if content_type:
        req.add_header("Content-Type", content_type)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read()


async def _owner_online(ws_url, owner):  # noqa: F811
    ws = await connect(ws_url, additional_headers=_headers(owner))
    await ws.send(json.dumps({"action": "ping"}))
    await asyncio.wait_for(ws.recv(), timeout=10)  # $connect has run
    return ws


async def _request(cfg, requester, file_id):  # noqa: F811
    return await asyncio.to_thread(_call, cfg, "POST", "/transfers", requester, {"file_id": file_id})


async def _next_upload_request(ws):
    return json.loads(await asyncio.wait_for(ws.recv(), timeout=15))


def _post(cfg, token, path, body=None):  # noqa: F811
    return _call(cfg, "POST", path, token, body)


def test_full_relay_path_owner_uploads_and_requester_downloads(ws_url, cfg, team_of_two):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws = await _owner_online(ws_url, owner)
        try:
            status, body = await _request(cfg, requester, file_id)
            assert status == 202 and body["status"] == "requested"
            transfer_id = body["transfer_id"]

            msg = await _next_upload_request(ws)
            assert msg["action"] == "upload_request" and msg["transfer_id"] == transfer_id
            assert msg["file_id"] == file_id and msg["ack_deadline_seconds"] == 60
            assert msg["upload_url"].startswith("https://") and msg["upload_url_expires_at"]

            assert _post(cfg, owner, f"/transfers/{transfer_id}/ack")[0] == 204
            assert _call(cfg, "GET", f"/transfers/{transfer_id}", requester)[1]["status"] == "uploading"

            # Any Content-Type must work: only bucket and key are signed.
            assert _http("PUT", msg["upload_url"], PAYLOAD, "application/x-hivemind-odd")[0] == 200
            assert _post(cfg, owner, f"/transfers/{transfer_id}/complete", {"size_bytes": len(PAYLOAD)})[0] == 204

            status, done = _call(cfg, "GET", f"/transfers/{transfer_id}", requester)
            assert status == 200 and done["status"] == "ready" and done["error_code"] is None
            assert done["file_id"] == file_id and done["download_url_expires_at"]
            assert _http("GET", done["download_url"])[1] == PAYLOAD

            # Only the requester sees the transfer; only the owner may drive it.
            assert _call(cfg, "GET", f"/transfers/{transfer_id}", owner)[0] == 404
            assert _post(cfg, requester, f"/transfers/{transfer_id}/ack")[0] == 404
            # Repeating a transition is safe.
            assert _post(cfg, owner, f"/transfers/{transfer_id}/complete")[0] == 204
        finally:
            await ws.close()

    asyncio.run(run())


def test_owner_offline_is_409_every_time(cfg, team_of_two):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)
    for _ in range(2):  # no ghost transfer is left behind by the first attempt
        status, body = _call(cfg, "POST", "/transfers", requester, {"file_id": file_id})
        assert status == 409 and body["error"]["code"] == "owner_offline"


def test_validation_errors(cfg, team_of_two):  # noqa: F811
    requester, owner = team_of_two
    own = _publish(cfg, owner, FILE)
    assert _call(cfg, "POST", "/transfers", owner, {"file_id": own})[1]["error"]["code"] == "own_file"
    assert _call(cfg, "POST", "/transfers", requester, {"file_id": str(uuid.uuid4())})[0] == 404
    assert _call(cfg, "POST", "/transfers", requester, {"file_id": "nope"})[0] == 400
    assert _call(cfg, "POST", "/transfers", requester, {})[0] == 400
    random_id = str(uuid.uuid4())
    assert _call(cfg, "GET", f"/transfers/{random_id}", requester)[0] == 404
    for action in ("ack", "complete"):
        assert _post(cfg, owner, f"/transfers/{random_id}/{action}")[0] == 404
    assert _post(cfg, owner, f"/transfers/{random_id}/fail", {"reason": "upload_error"})[0] == 404
    assert _post(cfg, owner, f"/transfers/{random_id}/fail", {"reason": "bogus"})[0] == 400


def test_no_team_cannot_request(cfg, make_user):  # noqa: F811
    status, body = _call(cfg, "POST", "/transfers", make_user(), {"file_id": str(uuid.uuid4())})
    assert status == 403 and body["error"]["code"] == "no_team"


def test_duplicate_request_reuses_the_in_flight_transfer(ws_url, cfg, team_of_two):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws = await _owner_online(ws_url, owner)
        try:
            first = (await _request(cfg, requester, file_id))[1]["transfer_id"]
            again = (await _request(cfg, requester, file_id))[1]["transfer_id"]
            assert first == again
            assert (await _next_upload_request(ws))["transfer_id"] == first
            with pytest.raises(asyncio.TimeoutError):  # the owner was notified once, not twice
                await asyncio.wait_for(ws.recv(), timeout=3)
        finally:
            await ws.close()

    asyncio.run(run())


def test_owner_failure_reports_the_error_code_and_allows_a_new_request(ws_url, cfg, team_of_two):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws = await _owner_online(ws_url, owner)
        try:
            first = (await _request(cfg, requester, file_id))[1]["transfer_id"]
            await _next_upload_request(ws)
            assert _post(cfg, owner, f"/transfers/{first}/fail", {"reason": "file_not_found"})[0] == 204
            _, failed = _call(cfg, "GET", f"/transfers/{first}", requester)
            assert failed["status"] == "failed" and failed["error_code"] == "file_unavailable"
            assert "download_url" not in failed
            # A failed transfer is not in flight: the same file can be requested again.
            second = (await _request(cfg, requester, file_id))[1]["transfer_id"]
            assert second != first
            await _next_upload_request(ws)
            # And the failed one cannot be revived.
            assert _post(cfg, owner, f"/transfers/{first}/ack")[1]["error"]["code"] == "conflict"
        finally:
            await ws.close()

    asyncio.run(run())


@pytest.mark.slow
def test_no_ack_within_the_timeout_fails_the_transfer(ws_url, cfg, team_of_two):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws = await _owner_online(ws_url, owner)
        try:
            transfer_id = (await _request(cfg, requester, file_id))[1]["transfer_id"]
            await _next_upload_request(ws)  # received, but never acknowledged
            assert _call(cfg, "GET", f"/transfers/{transfer_id}", requester)[1]["status"] == "requested"
            await asyncio.sleep(62)
            _, body = _call(cfg, "GET", f"/transfers/{transfer_id}", requester)
            assert body["status"] == "failed" and body["error_code"] == "owner_unresponsive"
            assert _post(cfg, owner, f"/transfers/{transfer_id}/ack")[1]["error"]["code"] == "conflict"
        finally:
            await ws.close()

    started = time.time()
    asyncio.run(run())
    assert time.time() - started >= 60
