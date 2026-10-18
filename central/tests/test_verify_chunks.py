import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import verify_chunks  # noqa: E402


class FakeCursor:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=()):
        self.statements.append(sql)
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("boom")

    def fetchone(self):
        return (0,)

    def fetchall(self):
        return []


class FakeConn:
    def __init__(self, cursor):
        self.cur = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cur

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_verify_never_commits_even_when_a_check_fails():
    conn = FakeConn(FakeCursor(fail_on="CREATE TEMP TABLE"))
    with pytest.raises(RuntimeError):
        verify_chunks.run(conn, rows=500)
    assert conn.commits == 0 and conn.rollbacks == 1


def test_row_count_is_clamped():
    conn = FakeConn(FakeCursor(fail_on="generate_series"))
    with pytest.raises(RuntimeError):
        verify_chunks.run(conn, rows=10_000_000)
    assert conn.rollbacks == 1


def test_handler_dispatches_verify_without_touching_the_migration_path(monkeypatch):
    import migrate
    from common import db

    conn = FakeConn(FakeCursor(fail_on="CREATE TEMP TABLE"))
    monkeypatch.setattr(db, "get_connection", lambda: conn)
    with pytest.raises(RuntimeError):
        migrate.handler({"action": "verify"}, None)
    assert conn.commits == 0 and conn.rollbacks == 1
    assert not any("schema_migrations" in s and "INSERT" in s for s in conn.cur.statements)
