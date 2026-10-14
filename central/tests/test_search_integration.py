"""Integration tests for E3-S7 against the deployed HiveMind stack.

Run: pytest -m integration   (needs `aws login`; the stack must include the Search Lambda)
Creates throwaway Cognito users and teams. Leaving a team deletes the leaver's files, so
every fixture leaves its team at the end. This is the first real-Postgres use of the
public_files.search_vector column. Tokens are never printed.
"""
import uuid

import pytest

from test_auth_integration import cfg, cognito  # noqa: F401
from test_teams_integration import _call, _error_code, make_user  # noqa: F401

pytestmark = pytest.mark.integration

CONTRACTS = {"filename": "Q3_Client-Contracts.v2.docx", "tags": ["renewal", "legal"],
             "file_created_at": "2026-09-29T09:00:00Z", "file_modified_at": "2026-10-05T11:30:00Z"}
ROADMAP = {"filename": "roadmap.pptx", "tags": ["planning", "strategy"],
           "file_created_at": "2026-08-01T09:00:00Z", "file_modified_at": "2026-08-02T09:00:00Z"}


def _publish(cfg, token, body):  # noqa: F811
    file_id = str(uuid.uuid4())
    assert _call(cfg, "PUT", f"/files/{file_id}", token, body)[0] == 200
    return file_id


def _search(cfg, token, **body):  # noqa: F811
    body.setdefault("topic", None)
    return _call(cfg, "POST", "/search", token, body)


def _ids(resp):
    return [r["file_id"] for r in resp["results"]]


@pytest.fixture
def team_of_two(cfg, make_user):  # noqa: F811
    seeker, publisher = make_user(), make_user()
    _call(cfg, "POST", "/teams", seeker, {"name": "Search test"})
    code = _call(cfg, "POST", "/teams/me/invites", seeker)[1]["code"]
    assert _call(cfg, "POST", "/teams/join", publisher, {"code": code})[0] == 200
    yield seeker, publisher
    for token in (publisher, seeker):
        _call(cfg, "POST", "/teams/me/leave", token)


def test_topic_matches_filename_words_tags_and_stems(cfg, team_of_two):  # noqa: F811
    seeker, publisher = team_of_two
    contracts = _publish(cfg, publisher, CONTRACTS)
    roadmap = _publish(cfg, publisher, ROADMAP)
    for topic in ("client", "contract", "renewal", "Q3 contracts", "v2"):  # word, stem, tag, both
        status, resp = _search(cfg, seeker, topic=topic)
        assert status == 200 and _ids(resp) == [contracts], topic
    assert _ids(_search(cfg, seeker, topic="strategy")[1]) == [roadmap]
    assert _search(cfg, seeker, topic="nonexistentword")[1] == {"results": []}
    assert _search(cfg, seeker, topic="???")[1] == {"results": []}


def test_any_word_of_the_topic_is_enough(cfg, team_of_two):  # noqa: F811
    seeker, publisher = team_of_two
    contracts = _publish(cfg, publisher, CONTRACTS)
    assert _ids(_search(cfg, seeker, topic="client banana")[1]) == [contracts]


def test_result_shape_and_no_owner_identity(cfg, team_of_two):  # noqa: F811
    seeker, publisher = team_of_two
    file_id = _publish(cfg, publisher, CONTRACTS)
    _, resp = _search(cfg, seeker, topic="contracts")
    (result,) = resp["results"]
    assert set(result) == {"file_id", "filename", "tags", "file_created_at", "file_modified_at",
                           "expires_at", "owner_online"}
    assert result["file_id"] == file_id and result["filename"] == CONTRACTS["filename"]
    assert result["tags"] == CONTRACTS["tags"]
    assert result["file_created_at"].startswith("2026-09-29T09:00:00")
    assert result["owner_online"] is False  # no relay connections exist until E4


def test_own_files_are_excluded(cfg, team_of_two):  # noqa: F811
    seeker, publisher = team_of_two
    mine = _publish(cfg, seeker, ROADMAP)
    theirs = _publish(cfg, publisher, ROADMAP)
    assert _ids(_search(cfg, seeker, topic="roadmap")[1]) == [theirs]
    assert _ids(_search(cfg, publisher, topic="roadmap")[1]) == [mine]


def test_other_teams_never_see_the_files(cfg, team_of_two, make_user):  # noqa: F811
    _, publisher = team_of_two
    _publish(cfg, publisher, CONTRACTS)
    outsider = make_user()
    _call(cfg, "POST", "/teams", outsider, {"name": "Other team"})
    try:
        assert _search(cfg, outsider, topic="contracts")[1] == {"results": []}
        assert _search(cfg, outsider)[1] == {"results": []}
    finally:
        _call(cfg, "POST", "/teams/me/leave", outsider)


def test_date_range_matches_created_or_modified(cfg, team_of_two):  # noqa: F811
    seeker, publisher = team_of_two
    contracts = _publish(cfg, publisher, CONTRACTS)  # created 09-29, modified 10-05
    roadmap = _publish(cfg, publisher, ROADMAP)      # created 08-01, modified 08-02
    assert _ids(_search(cfg, seeker, date_from="2026-09-29T00:00:00Z",
                        date_to="2026-09-29T23:59:59Z")[1]) == [contracts]   # created in range
    assert _ids(_search(cfg, seeker, date_from="2026-10-05T00:00:00Z",
                        date_to="2026-10-05T23:59:59Z")[1]) == [contracts]   # modified in range
    assert _search(cfg, seeker, date_from="2026-12-01T00:00:00Z")[1] == {"results": []}
    # null topic, open range: everything, newest first
    assert _ids(_search(cfg, seeker, date_from="2026-07-01T00:00:00Z")[1]) == [contracts, roadmap]
    # topic and dates combine
    assert _search(cfg, seeker, topic="roadmap", date_from="2026-09-01T00:00:00Z")[1] == {"results": []}


def test_null_topic_and_dates_lists_the_team_newest_first(cfg, team_of_two):  # noqa: F811
    seeker, publisher = team_of_two
    contracts = _publish(cfg, publisher, CONTRACTS)
    roadmap = _publish(cfg, publisher, ROADMAP)
    assert _ids(_call(cfg, "POST", "/search", seeker, {})[1]) == [contracts, roadmap]


def test_no_team_is_403(cfg, make_user):  # noqa: F811
    status, resp = _search(cfg, make_user(), topic="x")
    assert status == 403 and _error_code(resp) == "no_team"


def test_bad_requests_are_400_naming_the_fields(cfg, team_of_two):  # noqa: F811
    seeker, _ = team_of_two
    for body, fields in [
        ({"topic": 5}, ["topic"]),
        ({"date_from": "2026-09-29T00:00:00"}, ["date_from"]),  # no timezone
        ({"date_from": "2026-10-02T00:00:00Z", "date_to": "2026-10-01T00:00:00Z"},
         ["date_from", "date_to"]),
    ]:
        status, resp = _call(cfg, "POST", "/search", seeker, body)
        assert status == 400 and _error_code(resp) == "invalid_request", body
        assert resp["error"]["details"]["fields"] == fields


def test_requests_without_a_token_are_rejected(cfg):  # noqa: F811
    assert _call(cfg, "POST", "/search", "not-a-token", {})[0] == 401
