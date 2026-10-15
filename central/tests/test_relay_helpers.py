import io
import json
import os
import sys
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import notify  # noqa: E402
from common import relay, transit  # noqa: E402


class FakeCursor:
    def __init__(self, ids):
        self.ids = ids
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return [(i,) for i in self.ids]


class FakeLambda:
    """Stands in for boto3's lambda client; `result` is what the notify Lambda returns."""

    def __init__(self, result=None, function_error=None):
        self.result, self.function_error, self.invocations = result, function_error, []

    def invoke(self, FunctionName, InvocationType, Payload):  # noqa: N803
        self.invocations.append((FunctionName, InvocationType, json.loads(Payload)))
        body = json.dumps(self.result).encode()
        out = {"Payload": io.BytesIO(body)}
        if self.function_error:
            out["FunctionError"] = self.function_error
        return out


@pytest.fixture
def wired(monkeypatch):
    monkeypatch.setenv("NOTIFY_FUNCTION_NAME", "notify-fn")

    def install(ids, result=None, function_error=None):
        cur, client = FakeCursor(ids), FakeLambda(result, function_error)

        @contextmanager
        def transaction():
            yield cur

        monkeypatch.setattr(relay.db, "transaction", transaction)
        monkeypatch.setattr(relay, "_lambda", lambda: client)
        return cur, client

    return install


def test_connections_are_read_most_recent_first():
    cur = FakeCursor(["new", "old"])
    assert relay.connections_for(cur, "u") == ["new", "old"]
    sql, params = cur.executed[0]
    assert "ORDER BY connected_at DESC" in sql and params == ("u",)


def test_message_and_connection_ids_go_to_the_notify_lambda(wired):
    cur, client = wired(["new", "old"], {"delivered": "new", "gone": []})
    assert relay.send_to_user("u", {"action": "x"}) is True
    (name, kind, payload), = client.invocations
    assert name == "notify-fn" and kind == "RequestResponse"
    assert payload == {"connection_ids": ["new", "old"], "message": {"action": "x"}}
    assert not [s for s, _ in cur.executed if s.startswith("DELETE")]


def test_gone_connections_reported_by_notify_are_deleted(wired):
    cur, client = wired(["new", "old"], {"delivered": "old", "gone": ["new"]})
    assert relay.send_to_user("u", {"action": "x"}) is True
    assert ("DELETE FROM connections WHERE connection_id = ANY(%s)", (["new"],)) in cur.executed


def test_nothing_delivered_returns_false_and_clears_the_dead_ones(wired):
    cur, client = wired(["a", "b"], {"delivered": None, "gone": ["a", "b"]})
    assert relay.send_to_user("u", {"action": "x"}) is False
    assert ("DELETE FROM connections WHERE connection_id = ANY(%s)", (["a", "b"],)) in cur.executed


def test_no_connections_never_invokes_the_notify_lambda(wired):
    cur, client = wired([], {"delivered": None, "gone": []})
    assert relay.send_to_user("u", {"action": "x"}) is False and client.invocations == []


def test_a_notify_function_error_raises_without_echoing_its_payload(wired):
    cur, client = wired(["a"], {"errorMessage": "secret-upload-url"}, function_error="Unhandled")
    with pytest.raises(RuntimeError) as info:
        relay.send_to_user("u", {"action": "x"})
    assert "secret" not in str(info.value)


# ── notify Lambda ────────────────────────────────────────────────────────────

class FakeManagementApi:
    class exceptions:  # noqa: N801
        class GoneException(Exception):
            pass

    def __init__(self, gone=()):
        self.gone, self.posted = set(gone), []

    def post_to_connection(self, ConnectionId, Data):  # noqa: N803
        if ConnectionId in self.gone:
            raise self.exceptions.GoneException()
        self.posted.append((ConnectionId, json.loads(Data)))


@pytest.fixture
def management(monkeypatch):
    def install(gone=()):
        api = FakeManagementApi(gone)
        monkeypatch.setattr(notify, "_management_api", lambda: api)
        return api

    return install


def test_notify_delivers_to_the_first_live_connection_only(management):
    api = management()
    result = notify.handler({"connection_ids": ["new", "old"], "message": {"a": 1}}, None)
    assert result == {"delivered": "new", "gone": []} and api.posted == [("new", {"a": 1})]


def test_notify_skips_gone_connections_and_reports_them(management):
    api = management(gone={"new"})
    result = notify.handler({"connection_ids": ["new", "old"], "message": {"a": 1}}, None)
    assert result == {"delivered": "old", "gone": ["new"]} and api.posted == [("old", {"a": 1})]


def test_notify_with_every_connection_gone_delivers_nothing(management):
    management(gone={"a", "b"})
    assert notify.handler({"connection_ids": ["a", "b"], "message": {}}, None) == {
        "delivered": None, "gone": ["a", "b"]}


# ── transit presigning ───────────────────────────────────────────────────────

class FakeS3:
    def __init__(self):
        self.calls = []

    def generate_presigned_url(self, method, Params, ExpiresIn):  # noqa: N803
        self.calls.append((method, Params, ExpiresIn))
        return "https://signed"


@pytest.fixture
def s3(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(transit, "_s3", lambda: fake)
    monkeypatch.setenv("TRANSIT_BUCKET", "bucket")
    return fake


def test_put_signs_only_bucket_and_key_so_any_content_type_works(s3, monkeypatch):
    monkeypatch.setenv("UPLOAD_URL_EXPIRY_SECONDS", "123")
    url, expires_at = transit.presign_put("transfer-id")
    assert url == "https://signed"
    assert s3.calls == [("put_object", {"Bucket": "bucket", "Key": "transfer-id"}, 123)]
    assert expires_at.tzinfo is not None


def test_get_uses_the_download_expiry_from_config(s3, monkeypatch):
    monkeypatch.setenv("DOWNLOAD_URL_EXPIRY_SECONDS", "45")
    transit.presign_get("transfer-id")
    assert s3.calls == [("get_object", {"Bucket": "bucket", "Key": "transfer-id"}, 45)]


def test_expiry_defaults_are_configuration_driven(monkeypatch):
    monkeypatch.delenv("UPLOAD_URL_EXPIRY_SECONDS", raising=False)
    monkeypatch.delenv("DOWNLOAD_URL_EXPIRY_SECONDS", raising=False)
    assert (transit.upload_url_expiry_seconds(), transit.download_url_expiry_seconds()) == (600, 300)
