import datetime
import json
import os
import sys
import uuid
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import transfers  # noqa: E402

TEAM = "11111111-1111-1111-1111-111111111111"
FILE_ID = str(uuid.uuid4())
TRANSFER_ID = str(uuid.uuid4())
NOW = datetime.datetime(2026, 10, 14, 12, 0, tzinfo=datetime.timezone.utc)


class FakeCursor:
    """Answers fetches by the last SQL run: `answers` maps a substring of the SQL to a queue of
    results (the last one repeats). Unlisted queries return None / []."""

    def __init__(self, answers):
        self.answers = {k: list(v) for k, v in answers.items()}
        self.executed = []
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def _next(self, default):
        sql = self.executed[-1][0]
        for key, queue in self.answers.items():
            if key in sql:
                return queue.pop(0) if len(queue) > 1 else queue[0]
        return default

    def fetchone(self):
        return self._next(None)

    def fetchall(self):
        return self._next([])

    def ran(self, fragment):
        return [(s, p) for s, p in self.executed if fragment in s]


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("TRANSFER_ACK_TIMEOUT_SECONDS", "60")
    sent = []
    monkeypatch.setattr(transfers.transit, "presign_put", lambda key: (f"https://s3/put/{key}", NOW))
    monkeypatch.setattr(transfers.transit, "presign_get", lambda key: (f"https://s3/get/{key}", NOW))

    def send(user_id, message):
        sent.append((user_id, message))
        return send.result

    send.result = True
    monkeypatch.setattr(transfers.relay, "send_to_user", send)
    return sent, send


@pytest.fixture
def db(monkeypatch):
    holder = {}

    def install(answers):
        cur = FakeCursor(answers)
        holder["cur"] = cur

        @contextmanager
        def transaction():
            yield cur

        monkeypatch.setattr(transfers.db, "transaction", transaction)
        return cur

    return install


def call(route, body=None, path=None, sub="user-1"):
    event = {
        "routeKey": route,
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": path,
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": sub}}}},
    }
    return transfers.handler(event, None)


def code(resp):
    return json.loads(resp["body"])["error"]["code"]


def _request_answers(**overrides):
    answers = {"memberships": [(TEAM, "T")], "FROM public_files": [("owner-1",)],
               "SELECT transfer_id, status FROM transfers": [None],
               "FROM connections": [(1,)], "INSERT INTO transfers": [(TRANSFER_ID,)]}
    answers.update(overrides)
    return answers


def _log_rows(cur):
    return [p for _, p in cur.ran("INSERT INTO access_log")]


# ── POST /transfers ──────────────────────────────────────────────────────────

def test_request_creates_transfer_and_sends_upload_request_to_the_owner(db, env):
    sent, _ = env
    cur = db(_request_answers())
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 202
    body = json.loads(resp["body"])
    assert body["status"] == "requested" and uuid.UUID(body["transfer_id"])
    (owner, message), = sent
    assert owner == "owner-1"
    assert message["action"] == "upload_request" and message["transfer_id"] == body["transfer_id"]
    assert message["file_id"] == FILE_ID and message["ack_deadline_seconds"] == 60
    assert message["upload_url"] == f"https://s3/put/{body['transfer_id']}"
    assert message["upload_url_expires_at"] == "2026-10-14T12:00:00.000000Z"
    (_, params), = cur.ran("INSERT INTO transfers")
    assert params[0] == params[4] == body["transfer_id"]  # S3 key is the transfer id
    assert params[2:4] == ("user-1", "owner-1")
    assert _log_rows(cur) == [("transfer_request", "user-1", TEAM, FILE_ID, body["transfer_id"], "requested")]


@pytest.mark.parametrize("body", [{}, {"file_id": None}, {"file_id": "nope"}, {"file_id": 5}])
def test_invalid_file_id_is_400(db, env, body):
    db(_request_answers())
    resp = call("POST /transfers", body)
    assert resp["statusCode"] == 400 and code(resp) == "invalid_request"


def test_no_team_is_403(db, env):
    db(_request_answers(memberships=[None]))
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 403 and code(resp) == "no_team"


def test_unknown_expired_or_other_team_file_is_404(db, env):
    cur = db(_request_answers(**{"FROM public_files": [None]}))
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 404 and code(resp) == "not_found"
    sql, params = cur.ran("FROM public_files")[0]
    assert "team_id = %s" in sql and "expires_at > now()" in sql and params == (FILE_ID, TEAM)


def test_own_file_is_400_and_creates_nothing(db, env):
    sent, _ = env
    cur = db(_request_answers(**{"FROM public_files": [("user-1",)]}))
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 400 and code(resp) == "own_file"
    assert not cur.ran("INSERT INTO transfers") and not sent


def test_in_flight_transfer_is_reused_without_notifying_the_owner_again(db, env):
    sent, _ = env
    existing = str(uuid.uuid4())
    cur = db(_request_answers(**{"SELECT transfer_id, status FROM transfers": [(existing, "uploading")]}))
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 202
    assert json.loads(resp["body"]) == {"transfer_id": existing, "status": "uploading"}
    assert not sent and not cur.ran("INSERT INTO transfers")
    assert _log_rows(cur)[0][-1] == "reused"


def test_a_stale_unacked_transfer_is_failed_before_reuse_is_checked(db, env):
    cur = db(_request_answers())
    call("POST /transfers", {"file_id": FILE_ID})
    order = [s for s, _ in cur.executed]
    expire = next(i for i, s in enumerate(order) if "owner_unresponsive" in s)
    reuse = next(i for i, s in enumerate(order) if s.startswith("SELECT transfer_id, status"))
    assert expire < reuse
    assert cur.ran("owner_unresponsive")[0][1][0] == 60  # TRANSFER_ACK_TIMEOUT_SECONDS


def test_owner_with_no_connection_is_409_and_still_logged(db, env):
    sent, _ = env
    cur = db(_request_answers(**{"FROM connections": [None]}))
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 409 and code(resp) == "owner_offline"
    assert not cur.ran("INSERT INTO transfers") and not sent
    assert _log_rows(cur) == [("transfer_request", "user-1", TEAM, FILE_ID, None, "owner_offline")]


def test_concurrent_identical_request_reuses_the_winner(db, env):
    sent, _ = env
    winner = str(uuid.uuid4())
    cur = db(_request_answers(**{"INSERT INTO transfers": [None],
                                 "SELECT transfer_id, status FROM transfers": [None, (winner, "requested")]}))
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert json.loads(resp["body"])["transfer_id"] == winner and not sent
    assert _log_rows(cur)[-1][-1] == "reused"


def test_all_connections_gone_fails_the_transfer_and_returns_owner_offline(db, env):
    sent, send = env
    send.result = False
    cur = db(_request_answers())
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 409 and code(resp) == "owner_offline"
    (sql, params), = [(s, p) for s, p in cur.ran("UPDATE transfers") if "owner_unresponsive" in s
                      and "WHERE transfer_id" in s and "requester_id" not in s]
    assert "status = 'requested'" in sql
    assert [p[-1] for p in _log_rows(cur)] == ["requested", "owner_offline"]


def test_send_error_is_503_logs_no_urls_and_fails_the_transfer(db, env, monkeypatch, capsys):
    cur = db(_request_answers())

    def boom(user_id, message):
        raise RuntimeError(message["upload_url"])

    monkeypatch.setattr(transfers.relay, "send_to_user", boom)
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 503 and code(resp) == "service_unavailable"
    assert [p[-1] for p in _log_rows(cur)] == ["requested", "send_failed"]
    assert "https://" not in capsys.readouterr().out


# ── GET /transfers/{id} ──────────────────────────────────────────────────────

def _get(db_answers, transfer_id=TRANSFER_ID):
    return call("GET /transfers/{transfer_id}", path={"transfer_id": transfer_id}), db_answers


def test_get_ready_returns_a_presigned_download_url(db, env):
    db({"SELECT file_id, status": [(FILE_ID, "ready", TRANSFER_ID, None)]})
    resp, _ = _get(None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"]) == {
        "transfer_id": TRANSFER_ID, "file_id": FILE_ID, "status": "ready", "error_code": None,
        "download_url": f"https://s3/get/{TRANSFER_ID}", "download_url_expires_at": "2026-10-14T12:00:00.000000Z"}


@pytest.mark.parametrize("status,error", [("requested", None), ("uploading", None),
                                          ("failed", "owner_unresponsive"), ("expired", None)])
def test_get_not_ready_has_no_download_url(db, env, status, error):
    db({"SELECT file_id, status": [(FILE_ID, status, TRANSFER_ID, error)]})
    body = json.loads(_get(None)[0]["body"])
    assert body["status"] == status and body["error_code"] == error and "download_url" not in body


def test_get_scopes_to_the_requester_and_lazily_applies_the_ack_timeout(db, env):
    cur = db({"SELECT file_id, status": [(FILE_ID, "failed", TRANSFER_ID, "owner_unresponsive")]})
    _get(None)
    expire_sql, expire_params = cur.ran("owner_unresponsive")[0]
    assert "status = 'requested'" in expire_sql and expire_params == (60, TRANSFER_ID, "user-1")
    assert cur.ran("FROM transfers")[0][1] == (TRANSFER_ID, "user-1")


def test_get_someone_elses_or_unknown_transfer_is_404(db, env):
    db({"SELECT file_id, status": [None]})
    resp = _get(None)[0]
    assert resp["statusCode"] == 404 and code(resp) == "not_found"


def test_get_malformed_id_is_400(db, env):
    db({})
    resp = _get(None, "not-a-uuid")[0]
    assert resp["statusCode"] == 400 and code(resp) == "invalid_request"


# ── owner endpoints ──────────────────────────────────────────────────────────

def _owner(route, db_, body=None, transfer_id=TRANSFER_ID):
    return call(f"POST /transfers/{{transfer_id}}/{route}", body, {"transfer_id": transfer_id})


def test_ack_moves_requested_to_uploading(db, env):
    cur = db({"RETURNING 1": [(1,)]})
    resp = _owner("ack", db)
    assert resp["statusCode"] == 204
    sql, params = cur.ran("RETURNING 1")[0]
    assert params == ("uploading", TRANSFER_ID, "user-1", "requested")
    assert "owner_id = %s" in sql


def test_complete_records_size_and_moves_to_ready(db, env):
    cur = db({"RETURNING 1": [(1,)]})
    assert _owner("complete", db, {"size_bytes": 482113})["statusCode"] == 204
    sql, params = cur.ran("RETURNING 1")[0]
    assert params == ("ready", 482113, TRANSFER_ID, "user-1", "requested", "uploading")
    assert "size_bytes = %s" in sql


def test_complete_without_size_is_fine(db, env):
    db({"RETURNING 1": [(1,)]})
    assert _owner("complete", db)["statusCode"] == 204


@pytest.mark.parametrize("size", [-1, "12", 1.5, True])
def test_complete_rejects_a_bad_size(db, env, size):
    db({"RETURNING 1": [(1,)]})
    resp = _owner("complete", db, {"size_bytes": size})
    assert resp["statusCode"] == 400 and code(resp) == "invalid_request"


@pytest.mark.parametrize("reason,error", [("file_not_found", "file_unavailable"),
                                          ("not_public", "file_unavailable"),
                                          ("upload_error", "upload_failed")])
def test_fail_maps_the_reason_to_the_contract_error_code(db, env, reason, error):
    cur = db({"RETURNING 1": [(1,)]})
    assert _owner("fail", db, {"reason": reason})["statusCode"] == 204
    assert cur.ran("RETURNING 1")[0][1] == ("failed", error, TRANSFER_ID, "user-1", "requested", "uploading")


@pytest.mark.parametrize("body", [{}, {"reason": "because"}, {"reason": None}])
def test_fail_requires_a_known_reason(db, env, body):
    db({"RETURNING 1": [(1,)]})
    resp = _owner("fail", db, body)
    assert resp["statusCode"] == 400 and code(resp) == "invalid_request"


def test_not_the_owner_or_unknown_transfer_is_404(db, env):
    db({"RETURNING 1": [None], "SELECT status FROM transfers": [None]})
    resp = _owner("ack", db)
    assert resp["statusCode"] == 404 and code(resp) == "not_found"


def test_repeating_the_transition_already_made_is_204(db, env):
    db({"RETURNING 1": [None], "SELECT status FROM transfers": [("uploading",)]})
    assert _owner("ack", db)["statusCode"] == 204


def test_a_conflicting_state_is_409_with_the_current_status(db, env):
    db({"RETURNING 1": [None], "SELECT status FROM transfers": [("failed",)]})
    resp = _owner("ack", db)
    assert resp["statusCode"] == 409 and code(resp) == "conflict"
    assert json.loads(resp["body"])["error"]["details"] == {"status": "failed"}


def test_owner_endpoint_lazily_applies_the_ack_timeout_first(db, env):
    cur = db({"RETURNING 1": [None], "SELECT status FROM transfers": [("failed",)]})
    _owner("ack", db)
    assert "owner_unresponsive" in cur.executed[0][0] and cur.executed[0][1] == (60, TRANSFER_ID, "user-1")


# ── routing and auth ─────────────────────────────────────────────────────────

def test_missing_authorizer_claims_is_401(db, env):
    resp = transfers.handler({"routeKey": "POST /transfers", "body": "{}"}, None)
    assert resp["statusCode"] == 401


def test_unknown_route_is_404(db, env):
    assert call("DELETE /transfers")["statusCode"] == 404


def test_unexpected_error_is_503_and_logs_only_the_type(db, env, monkeypatch, capsys):
    @contextmanager
    def broken():
        raise RuntimeError(FILE_ID)
        yield

    monkeypatch.setattr(transfers.db, "transaction", broken)
    resp = call("POST /transfers", {"file_id": FILE_ID})
    assert resp["statusCode"] == 503
    out = capsys.readouterr().out
    assert FILE_ID not in out and "RuntimeError" in out


def test_malformed_json_body_is_400(db, env):
    db({})
    event = {"routeKey": "POST /transfers", "body": "{nope",
             "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "u"}}}}}
    assert transfers.handler(event, None)["statusCode"] == 400
