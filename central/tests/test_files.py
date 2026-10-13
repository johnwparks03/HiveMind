import base64
import datetime
import json
import os
import sys
import uuid
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import files  # noqa: E402

FILE_ID = str(uuid.uuid4())
TEAM = (str(uuid.uuid4()), "Alpha")
T0 = datetime.datetime(2026, 10, 1, 12, 0, tzinfo=datetime.timezone.utc)
T1 = T0 + datetime.timedelta(days=45)
BODY = {"filename": "notes.docx", "tags": ["meeting", "roadmap"],
        "file_created_at": "2026-09-29T09:00:00Z", "file_modified_at": "2026-09-29T11:30:00Z"}


class FakeCursor:
    def __init__(self, results=()):
        self.results = list(results)
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.results.pop(0)

    def fetchall(self):
        return self.results.pop(0)

    def sqls(self):
        return " | ".join(s for s, _ in self.executed)

    def log_events(self):
        return [p[0] for s, p in self.executed if s.startswith("INSERT INTO access_log")]


@pytest.fixture
def fake_db(monkeypatch):
    def install(results):
        cur = FakeCursor(results)

        @contextmanager
        def transaction():
            yield cur

        monkeypatch.setattr(files.db, "transaction", transaction)
        return cur

    return install


def _event(route, file_id=FILE_ID, body=None, query=None, sub="user-1"):
    return {
        "routeKey": route,
        "pathParameters": {"file_id": file_id} if file_id else None,
        "queryStringParameters": query,
        "body": json.dumps(body) if body is not None else None,
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": sub}}}},
    }


def _put(body=BODY, file_id=FILE_ID):
    return files.handler(_event("PUT /files/{file_id}", file_id, body), None)


def _body(resp):
    return json.loads(resp["body"])


def test_unauthenticated_is_401():
    event = _event("PUT /files/{file_id}", body=BODY)
    del event["requestContext"]
    assert files.handler(event, None)["statusCode"] == 401


def test_unknown_route_is_404(fake_db):
    fake_db([])
    assert files.handler(_event("GET /files/other"), None)["statusCode"] == 404


@pytest.mark.parametrize("override,field", [
    ({"filename": ""}, "filename"),
    ({"filename": 5}, "filename"),
    ({"filename": "x" * 300}, "filename"),
    ({"tags": "meeting"}, "tags"),
    ({"tags": ["ok", ""]}, "tags"),
    ({"tags": [1]}, "tags"),
    ({"file_created_at": "yesterday"}, "file_created_at"),
    ({"file_modified_at": "2026-09-29T09:00:00"}, "file_modified_at"),
])
def test_put_validation_names_the_field_not_the_value(fake_db, override, field):
    fake_db([])
    resp = _put({**BODY, "filename": "ok.docx", **override})
    assert resp["statusCode"] == 400
    err = _body(resp)["error"]
    assert err["code"] == "invalid_request" and field in err["details"]["fields"]
    assert "yesterday" not in resp["body"]


def test_put_bad_file_id_is_400(fake_db):
    fake_db([])
    resp = _put(file_id="not-a-uuid")
    assert resp["statusCode"] == 400 and _body(resp)["error"]["details"]["fields"] == ["file_id"]


def test_put_invalid_json_is_400(fake_db):
    fake_db([])
    event = _event("PUT /files/{file_id}")
    event["body"] = "{nope"
    assert files.handler(event, None)["statusCode"] == 400


def test_put_without_team_is_403_no_team(fake_db):
    cur = fake_db([None])
    resp = _put()
    assert resp["statusCode"] == 403 and _body(resp)["error"]["code"] == "no_team"
    assert "INSERT INTO public_files" not in cur.sqls()


def test_first_publish_returns_timestamps_and_logs_publish(fake_db):
    cur = fake_db([TEAM, (T0, T1, T0, True)])
    resp = _put()
    assert resp["statusCode"] == 200
    assert _body(resp) == {"file_id": FILE_ID, "published_at": "2026-10-01T12:00:00.000000Z",
                           "expires_at": "2026-11-15T12:00:00.000000Z",
                           "last_confirmed": "2026-10-01T12:00:00.000000Z"}
    assert cur.log_events() == ["publish"]
    insert_params = next(p for s, p in cur.executed if s.startswith("INSERT INTO public_files"))
    assert insert_params[:5] == (FILE_ID, "user-1", TEAM[0], "notes.docx", ["meeting", "roadmap"])
    assert insert_params[-1] == 45


def test_republish_is_idempotent_and_does_not_log(fake_db):
    cur = fake_db([TEAM, (T0, T1, T0, False)])
    assert _put()["statusCode"] == 200
    assert cur.log_events() == []
    assert "ON CONFLICT (file_id) DO UPDATE" in cur.sqls()
    # published_at/expires_at/last_confirmed are never in the update list
    update = cur.executed[-1][0].split("DO UPDATE SET")[1].split("WHERE")[0]
    assert "published_at" not in update and "expires_at" not in update and "last_confirmed" not in update


def test_put_on_another_users_row_is_403_forbidden(fake_db):
    cur = fake_db([TEAM, None])
    resp = _put()
    assert resp["statusCode"] == 403 and _body(resp)["error"]["code"] == "forbidden"
    assert cur.log_events() == []


def test_retention_days_is_configurable(fake_db, monkeypatch):
    monkeypatch.setenv("RETENTION_DAYS", "10")
    cur = fake_db([TEAM, (T0, T1, T0, True)])
    _put()
    assert cur.executed[-2][1][-1] == 10


def test_delete_removes_and_logs_unpublish(fake_db):
    cur = fake_db([(TEAM[0],)])
    resp = files.handler(_event("DELETE /files/{file_id}"), None)
    assert resp["statusCode"] == 204 and cur.log_events() == ["unpublish"]


def test_delete_missing_is_204_and_not_logged(fake_db):
    cur = fake_db([None, None])
    assert files.handler(_event("DELETE /files/{file_id}"), None)["statusCode"] == 204
    assert cur.log_events() == []


def test_delete_other_users_file_is_403(fake_db):
    fake_db([None, ("someone-else",)])
    resp = files.handler(_event("DELETE /files/{file_id}"), None)
    assert resp["statusCode"] == 403 and _body(resp)["error"]["code"] == "forbidden"


def test_confirm_extends_and_logs(fake_db):
    cur = fake_db([(TEAM[0], T1, T0)])
    resp = files.handler(_event("POST /files/{file_id}/confirm"), None)
    assert resp["statusCode"] == 200
    assert _body(resp) == {"expires_at": "2026-11-15T12:00:00.000000Z",
                           "last_confirmed": "2026-10-01T12:00:00.000000Z"}
    assert cur.log_events() == ["confirm"]
    assert "expires_at > now()" in cur.sqls()


def test_confirm_missing_or_expired_is_404(fake_db):
    fake_db([None, None])
    resp = files.handler(_event("POST /files/{file_id}/confirm"), None)
    assert resp["statusCode"] == 404 and _body(resp)["error"]["code"] == "not_found"


def test_confirm_other_users_file_is_403(fake_db):
    fake_db([None, ("someone-else",)])
    assert files.handler(_event("POST /files/{file_id}/confirm"), None)["statusCode"] == 403


def _row(n):
    return (str(uuid.UUID(int=n)), f"f{n}.docx", T0, T1, T0)


def test_mine_returns_rows_and_no_cursor_on_last_page(fake_db):
    fake_db([[_row(1), _row(2)]])
    resp = files.handler(_event("GET /files/mine", None), None)
    body = _body(resp)
    assert resp["statusCode"] == 200 and body["next_cursor"] is None
    assert [f["filename"] for f in body["files"]] == ["f1.docx", "f2.docx"]
    assert set(body["files"][0]) == {"file_id", "filename", "published_at", "expires_at", "last_confirmed"}


def test_mine_pages_with_a_cursor_that_round_trips(fake_db):
    cur = fake_db([[_row(1), _row(2), _row(3)]])
    body = _body(files.handler(_event("GET /files/mine", None, query={"limit": "2"}), None))
    assert len(body["files"]) == 2 and body["next_cursor"]
    assert cur.executed[0][1][-1] == 3  # fetched limit + 1
    cur2 = fake_db([[_row(3)]])
    files.handler(_event("GET /files/mine", None, query={"limit": "2", "cursor": body["next_cursor"]}), None)
    assert cur2.executed[0][1][1] == str(uuid.UUID(int=2))


@pytest.mark.parametrize("query", [{"limit": "0"}, {"limit": "501"}, {"limit": "abc"},
                                   {"cursor": "!!!"}, {"cursor": base64.urlsafe_b64encode(b"nope").decode()}])
def test_mine_bad_limit_or_cursor_is_400(fake_db, query):
    fake_db([])
    resp = files.handler(_event("GET /files/mine", None, query=query), None)
    assert resp["statusCode"] == 400


def test_unexpected_error_is_503_without_leaking(fake_db, monkeypatch):
    @contextmanager
    def boom():
        raise RuntimeError("secret detail")
        yield

    monkeypatch.setattr(files.db, "transaction", boom)
    resp = _put()
    assert resp["statusCode"] == 503 and "secret detail" not in resp["body"]
