"""Integration tests for E4-S5 against the deployed HiveMind stack.

Run: pytest -m integration tests/test_sweeper_integration.py   (needs `aws login`; the stack must
include the sweeper). Most tests invoke the deployed sweeper directly with `max_age_minutes: 0`
so they do not wait 15 minutes; that sweeps every transfer in the stack, so do not run them while
someone is mid-transfer on the shared demo. Two slow tests wait on the real schedule and config:
skip them with `-m "integration and not slow"`. Tokens and URLs are never printed.
"""
import asyncio
import json
import os
import time
import urllib.error

import boto3
import pytest

from test_auth_integration import REGION, STACK_NAME, cfg, cognito  # noqa: F401
from test_relay_integration import ws_url  # noqa: F401
from test_search_integration import _publish  # noqa: F401
from test_teams_integration import _call, make_user  # noqa: F401
from test_transfers_integration import (FILE, PAYLOAD, _http, _next_upload_request,  # noqa: F401
                                        _owner_online, _post, _request, team_of_two)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def sweeper_name():
    name = os.environ.get("HIVEMIND_SWEEPER_FUNCTION")
    if not name:
        stack = boto3.client("cloudformation", region_name=REGION).describe_stacks(
            StackName=STACK_NAME)["Stacks"][0]
        name = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}["SweeperFunctionName"]
    return name


def run_sweeper(name, **event):
    out = boto3.client("lambda", region_name=REGION).invoke(
        FunctionName=name, InvocationType="RequestResponse", Payload=json.dumps(event).encode())
    assert "FunctionError" not in out, "sweeper raised"
    return json.loads(out["Payload"].read())


async def _ready_transfer(ws_url, cfg, requester, owner, file_id):  # noqa: F811
    """Walk one transfer to `ready` with a real object in S3. Returns (ws, transfer_id, download_url)."""
    ws = await _owner_online(ws_url, owner)
    transfer_id = (await _request(cfg, requester, file_id))[1]["transfer_id"]
    msg = await _next_upload_request(ws)
    assert _post(cfg, owner, f"/transfers/{transfer_id}/ack")[0] == 204
    assert _http("PUT", msg["upload_url"], PAYLOAD)[0] == 200
    assert _post(cfg, owner, f"/transfers/{transfer_id}/complete")[0] == 204
    done = _call(cfg, "GET", f"/transfers/{transfer_id}", requester)[1]
    assert done["status"] == "ready" and _http("GET", done["download_url"])[1] == PAYLOAD
    return ws, transfer_id, done["download_url"]


def _gone(url):
    """True only for 404 (no such key). A 403 means the presigned URL expired, which proves nothing."""
    try:
        _http("GET", url)
    except urllib.error.HTTPError as err:
        return err.code == 404
    return False


def test_sweep_deletes_the_object_and_expires_the_transfer_idempotently(ws_url, cfg, team_of_two, sweeper_name):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws, transfer_id, url = await _ready_transfer(ws_url, cfg, requester, owner, file_id)
        try:
            first = await asyncio.to_thread(run_sweeper, sweeper_name, max_age_minutes=0)
            assert first["swept"] >= 1 and first["delete_errors"] == 0

            assert _gone(url)  # the bytes are no longer in S3
            status, body = _call(cfg, "GET", f"/transfers/{transfer_id}", requester)
            assert status == 200 and body["status"] == "expired" and "download_url" not in body

            again = await asyncio.to_thread(run_sweeper, sweeper_name, max_age_minutes=0)
            assert again["delete_errors"] == 0 and again["swept"] == 0  # nothing left to do
            assert _call(cfg, "GET", f"/transfers/{transfer_id}", requester)[1]["status"] == "expired"

            # An expired transfer is no longer in flight: the same file can be requested afresh.
            status, fresh = await _request(cfg, requester, file_id)
            assert status == 202 and fresh["transfer_id"] != transfer_id
            await _next_upload_request(ws)
        finally:
            await ws.close()

    asyncio.run(run())


def test_a_failed_transfer_keeps_its_status_but_is_still_swept(ws_url, cfg, team_of_two, sweeper_name):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws = await _owner_online(ws_url, owner)
        try:
            transfer_id = (await _request(cfg, requester, file_id))[1]["transfer_id"]
            await _next_upload_request(ws)
            assert _post(cfg, owner, f"/transfers/{transfer_id}/fail", {"reason": "upload_error"})[0] == 204
            result = await asyncio.to_thread(run_sweeper, sweeper_name, max_age_minutes=0)
            assert result["delete_errors"] == 0
            _, body = _call(cfg, "GET", f"/transfers/{transfer_id}", requester)
            assert body["status"] == "failed" and body["error_code"] == "upload_failed"
        finally:
            await ws.close()

    asyncio.run(run())


@pytest.mark.slow
def test_the_sweeper_fails_an_unacked_request_without_anyone_reading_it(ws_url, cfg, team_of_two, sweeper_name):  # noqa: F811
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws = await _owner_online(ws_url, owner)
        try:
            transfer_id = (await _request(cfg, requester, file_id))[1]["transfer_id"]
            await _next_upload_request(ws)  # received, never acknowledged
            await asyncio.sleep(62)
            # Run the sweeper before any GET, which would apply the timeout lazily itself.
            result = await asyncio.to_thread(run_sweeper, sweeper_name)
            assert result["failed_unacked"] >= 1
            _, body = _call(cfg, "GET", f"/transfers/{transfer_id}", requester)
            assert body["status"] == "failed" and body["error_code"] == "owner_unresponsive"
        finally:
            await ws.close()

    asyncio.run(run())


@pytest.mark.slow
def test_the_schedule_deletes_an_object_after_the_configured_age(ws_url, cfg, team_of_two):  # noqa: F811
    """No manual invocation: the real rule and the real 15-minute age. Takes about 16 minutes."""
    requester, owner = team_of_two
    file_id = _publish(cfg, owner, FILE)

    async def run():
        ws, transfer_id, url = await _ready_transfer(ws_url, cfg, requester, owner, file_id)
        try:
            started = time.time()
            while True:
                _, body = _call(cfg, "GET", f"/transfers/{transfer_id}", requester)
                if body["status"] != "ready":
                    break
                url = body["download_url"]  # re-signed each poll: the 5 minute URL must not lapse
                assert time.time() - started < 18 * 60, "transfer still ready after 18 minutes"
                await asyncio.sleep(20)
            print(f"transfer {body['status']} after {int(time.time() - started)} s")
            assert body["status"] == "expired" and "download_url" not in body
            assert _gone(url)  # the last URL was signed seconds ago, so a 404 means the object is deleted
        finally:
            await ws.close()

    asyncio.run(run())


@pytest.mark.slow
def test_the_rule_invokes_the_sweeper_about_once_a_minute(sweeper_name):
    logs = boto3.client("logs", region_name=REGION)
    group = f"/aws/lambda/{sweeper_name}"
    deadline = time.time() + 4 * 60
    while True:
        since = int((time.time() - 5 * 60) * 1000)
        events = logs.filter_log_events(logGroupName=group, startTime=since,
                                        filterPattern='"sweeper run"')["events"]
        if len(events) >= 3 or time.time() > deadline:
            break
        time.sleep(20)
    assert len(events) >= 3, f"only {len(events)} scheduled runs in the last 5 minutes"
