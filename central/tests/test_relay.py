import json
import os
import sys
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import relay  # noqa: E402


class FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))


@pytest.fixture
def cur(monkeypatch):
    fake = FakeCursor()

    @contextmanager
    def transaction():
        yield fake

    monkeypatch.setattr(relay.db, "transaction", transaction)
    return fake


def _event(route, connection_id="conn-1", user_id="user-1"):
    context = {"routeKey": route, "connectionId": connection_id}
    if user_id:
        context["authorizer"] = {"user_id": user_id}
    return {"requestContext": context}


def test_connect_stores_connection_for_the_authorized_user(cur):
    assert relay.handler(_event("$connect"), None) == {"statusCode": 200}
    (sql, params), = cur.executed
    assert sql.startswith("INSERT INTO connections")
    assert params == ("conn-1", "user-1")


def test_connect_is_an_upsert_so_a_duplicate_delivery_is_safe(cur):
    relay.handler(_event("$connect"), None)
    assert "ON CONFLICT (connection_id) DO UPDATE" in cur.executed[0][0]


def test_connect_does_not_check_team_membership(cur):
    relay.handler(_event("$connect"), None)
    assert "memberships" not in cur.executed[0][0]


def test_disconnect_deletes_by_connection_id_without_needing_authorizer_context(cur):
    assert relay.handler(_event("$disconnect", user_id=None), None) == {"statusCode": 200}
    assert cur.executed == [("DELETE FROM connections WHERE connection_id = %s", ("conn-1",))]


def test_ping_returns_pong_without_touching_the_database(monkeypatch):
    def no_db():
        raise AssertionError("ping must not use the database")

    monkeypatch.setattr(relay.db, "transaction", no_db)
    result = relay.handler(_event("ping"), None)
    assert result["statusCode"] == 200 and json.loads(result["body"]) == {"action": "pong"}


def test_unknown_route_is_404(cur):
    assert relay.handler(_event("nope"), None) == {"statusCode": 404}
    assert cur.executed == []


def test_database_failure_returns_500_and_logs_no_values(monkeypatch, capsys):
    @contextmanager
    def broken():
        raise RuntimeError("secret-user-1")
        yield

    monkeypatch.setattr(relay.db, "transaction", broken)
    assert relay.handler(_event("$connect"), None) == {"statusCode": 500}
    assert "user-1" not in capsys.readouterr().out
