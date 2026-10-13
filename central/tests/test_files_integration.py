"""Integration tests for E3-S2 against the deployed HiveMind stack.

Run: pytest -m integration   (needs `aws login`; the stack must include the Files Lambda)
Creates throwaway Cognito users and teams. Leaving a team deletes the leaver's files, so
every test leaves its team(s) at the end. Tokens are never printed.
"""
import time
import uuid

import pytest

from test_auth_integration import cfg, cognito  # noqa: F401
from test_teams_integration import _call, _error_code, make_user  # noqa: F401

pytestmark = pytest.mark.integration

BODY = {"filename": "Q3_Client-Contracts.v2.docx", "tags": ["contracts", "renewal"],
        "file_created_at": "2026-09-29T09:00:00Z", "file_modified_at": "2026-09-29T11:30:00Z"}


def _path(file_id):
    return f"/files/{file_id}"


@pytest.fixture
def team_of_two(cfg, make_user):  # noqa: F811
    owner, member = make_user(), make_user()
    _call(cfg, "POST", "/teams", owner, {"name": "Files test"})
    code = _call(cfg, "POST", "/teams/me/invites", owner)[1]["code"]
    assert _call(cfg, "POST", "/teams/join", member, {"code": code})[0] == 200
    yield owner, member
    for token in (member, owner):
        _call(cfg, "POST", "/teams/me/leave", token)


def test_publish_is_idempotent_and_preserves_expiry(cfg, team_of_two):
    owner, _ = team_of_two
    file_id = str(uuid.uuid4())
    status, first = _call(cfg, "PUT", _path(file_id), owner, BODY)
    assert status == 200 and first["file_id"] == file_id
    assert first["last_confirmed"] == first["published_at"]
    time.sleep(1.1)
    status, second = _call(cfg, "PUT", _path(file_id), owner, {**BODY, "tags": ["changed"]})
    assert status == 200
    assert (second["published_at"], second["expires_at"], second["last_confirmed"]) == (
        first["published_at"], first["expires_at"], first["last_confirmed"])
    files = _call(cfg, "GET", "/files/mine", owner)[1]["files"]
    assert [f["file_id"] for f in files] == [file_id]


def test_other_team_member_cannot_modify(cfg, team_of_two):
    owner, member = team_of_two
    file_id = str(uuid.uuid4())
    assert _call(cfg, "PUT", _path(file_id), owner, BODY)[0] == 200
    for method, path, body in [("PUT", _path(file_id), BODY), ("DELETE", _path(file_id), None),
                               ("POST", _path(file_id) + "/confirm", None)]:
        status, resp = _call(cfg, method, path, member, body)
        assert status == 403 and _error_code(resp) == "forbidden", method
    assert _call(cfg, "GET", "/files/mine", member)[1]["files"] == []


def test_no_team_cannot_publish(cfg, make_user):  # noqa: F811
    token = make_user()
    status, resp = _call(cfg, "PUT", _path(str(uuid.uuid4())), token, BODY)
    assert status == 403 and _error_code(resp) == "no_team"
    assert _call(cfg, "GET", "/files/mine", token) == (200, {"files": [], "next_cursor": None})


def test_delete_is_idempotent_and_confirm_404_after(cfg, team_of_two):
    owner, _ = team_of_two
    file_id = str(uuid.uuid4())
    _call(cfg, "PUT", _path(file_id), owner, BODY)
    assert _call(cfg, "DELETE", _path(file_id), owner)[0] == 204
    assert _call(cfg, "DELETE", _path(file_id), owner)[0] == 204
    status, resp = _call(cfg, "POST", _path(file_id) + "/confirm", owner)
    assert status == 404 and _error_code(resp) == "not_found"
    assert _call(cfg, "GET", "/files/mine", owner)[1]["files"] == []


def test_confirm_moves_expiry_forward(cfg, team_of_two):
    owner, _ = team_of_two
    file_id = str(uuid.uuid4())
    _, published = _call(cfg, "PUT", _path(file_id), owner, BODY)
    time.sleep(1.1)
    status, confirmed = _call(cfg, "POST", _path(file_id) + "/confirm", owner)
    assert status == 200
    assert confirmed["expires_at"] > published["expires_at"]
    assert confirmed["last_confirmed"] > published["last_confirmed"]


def test_mine_pages_through_all_files(cfg, team_of_two):
    owner, _ = team_of_two
    ids = sorted(str(uuid.uuid4()) for _ in range(3))
    for file_id in ids:
        assert _call(cfg, "PUT", _path(file_id), owner, BODY)[0] == 200
    seen, cursor = [], None
    for _ in range(5):
        query = "/files/mine?limit=2" + (f"&cursor={cursor}" if cursor else "")
        status, page = _call(cfg, "GET", query, owner)
        assert status == 200 and len(page["files"]) <= 2
        seen += [f["file_id"] for f in page["files"]]
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert seen == ids


def test_validation_errors_name_fields_only(cfg, team_of_two):
    owner, _ = team_of_two
    status, resp = _call(cfg, "PUT", _path(str(uuid.uuid4())), owner, {**BODY, "filename": ""})
    assert status == 400 and _error_code(resp) == "invalid_request"
    assert resp["error"]["details"]["fields"] == ["filename"]
    status, resp = _call(cfg, "PUT", _path("not-a-uuid"), owner, BODY)
    assert status == 400 and resp["error"]["details"]["fields"] == ["file_id"]
    assert _call(cfg, "GET", "/files/mine?limit=0", owner)[0] == 400


def test_requests_without_a_token_are_rejected(cfg):
    assert _call(cfg, "GET", "/files/mine", "not-a-token")[0] == 401
