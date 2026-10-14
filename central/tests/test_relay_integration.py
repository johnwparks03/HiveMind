"""Integration tests for E4-S1 against the deployed HiveMind stack.

Run: pytest -m integration   (needs `aws login`; the stack must include the relay WebSocket API)
The WebSocket URL comes from HIVEMIND_WS_URL or the `WebSocketUrl` stack output. Throwaway
Cognito users and teams are cleaned up by the shared fixtures. Tokens are never printed.
"""
import asyncio
import json
import os
import time
import uuid

import boto3
import pytest
from websockets.asyncio.client import connect
from websockets.exceptions import InvalidHandshake

from test_auth_integration import REGION, STACK_NAME, cfg, cognito  # noqa: F401
from test_search_integration import _publish, _search  # noqa: F401
from test_teams_integration import _call, make_user  # noqa: F401

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def ws_url():
    url = os.environ.get("HIVEMIND_WS_URL")
    if not url:
        stack = boto3.client("cloudformation", region_name=REGION).describe_stacks(
            StackName=STACK_NAME)["Stacks"][0]
        url = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}["WebSocketUrl"]
    return url


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_connect_ping_pong(ws_url, make_user):  # noqa: F811
    token = make_user()  # a user with no team may connect

    async def run():
        async with connect(ws_url, additional_headers=_headers(token)) as ws:
            await ws.send(json.dumps({"action": "ping"}))
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=10))

    assert asyncio.run(run()) == {"action": "pong"}


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not.a.jwt"}],
                         ids=["no-token", "garbage-token"])
def test_connect_without_a_valid_token_is_rejected(ws_url, headers):
    async def run():
        async with connect(ws_url, additional_headers=headers):
            pass

    with pytest.raises(InvalidHandshake) as info:
        asyncio.run(run())
    assert info.value.response.status_code in (401, 403)


def test_id_token_is_rejected(ws_url, cfg, cognito, make_user):  # noqa: F811
    """The authorizer accepts access tokens only (E0-S3 decision)."""
    from test_auth_integration import _login, _sign_up

    email = f"e4s1-{uuid.uuid4().hex[:12]}@example.com"
    _sign_up(cognito, cfg, email)
    try:
        id_token = _login(cognito, cfg, email)["IdToken"]

        async def run():
            async with connect(ws_url, additional_headers=_headers(id_token)):
                pass

        with pytest.raises(InvalidHandshake):
            asyncio.run(run())
    finally:
        cognito.admin_delete_user(UserPoolId=cfg["pool_id"], Username=email)


@pytest.fixture
def team_of_two(cfg, make_user):  # noqa: F811
    seeker, owner = make_user(), make_user()
    _call(cfg, "POST", "/teams", seeker, {"name": "Relay test"})
    code = _call(cfg, "POST", "/teams/me/invites", seeker)[1]["code"]
    assert _call(cfg, "POST", "/teams/join", owner, {"code": code})[0] == 200
    yield seeker, owner
    for token in (owner, seeker):
        _call(cfg, "POST", "/teams/me/leave", token)


def _owner_online(cfg, seeker, file_id):  # noqa: F811
    (result,) = [r for r in _search(cfg, seeker, topic="relayprobe")[1]["results"]
                 if r["file_id"] == file_id]
    return result["owner_online"]


def test_owner_online_follows_the_connection(ws_url, cfg, team_of_two):  # noqa: F811
    seeker, owner = team_of_two
    file_id = _publish(cfg, owner, {"filename": "relayprobe.docx", "tags": []})
    assert _owner_online(cfg, seeker, file_id) is False

    async def run():
        async with connect(ws_url, additional_headers=_headers(owner)) as ws:
            await ws.send(json.dumps({"action": "ping"}))
            await asyncio.wait_for(ws.recv(), timeout=10)  # connected and $connect has run
            return _owner_online(cfg, seeker, file_id)

    assert asyncio.run(run()) is True
    deadline = time.time() + 15  # $disconnect is delivered asynchronously
    while _owner_online(cfg, seeker, file_id) and time.time() < deadline:
        time.sleep(1)
    assert _owner_online(cfg, seeker, file_id) is False
