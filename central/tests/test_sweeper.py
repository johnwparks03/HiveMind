import os
import sys
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import sweeper  # noqa: E402
from common import transfer_state, transit  # noqa: E402


class FakeCursor:
    """`due` is what the sweeper's SELECT returns, as (transfer_id, s3_key) pairs; each SELECT
    consumes up to `limit` of them, like the real query once rows are marked swept."""

    def __init__(self, due, unacked=0):
        self.due, self.unacked, self.executed, self.rowcount = list(due), unacked, [], 0
        self._rows = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if sql.startswith("SELECT"):
            self._rows, self.due = self.due[:params[1]], self.due[params[1]:]
        elif "owner_unresponsive" in sql:
            self.rowcount = self.unacked

    def fetchall(self):
        return self._rows


class FakeS3:
    def __init__(self, fail=()):
        self.fail, self.calls = set(fail), []

    def delete_objects(self, Bucket, Delete):  # noqa: N803
        keys = [o["Key"] for o in Delete["Objects"]]
        self.calls.append((Bucket, keys))
        return {"Deleted": [{"Key": k} for k in keys if k not in self.fail],
                "Errors": [{"Key": k, "Code": "AccessDenied"} for k in keys if k in self.fail]}


@pytest.fixture
def wired(monkeypatch):
    monkeypatch.setenv("TRANSIT_BUCKET", "bucket")
    monkeypatch.delenv("SWEEPER_MAX_AGE_MINUTES", raising=False)
    monkeypatch.delenv("TRANSFER_ACK_TIMEOUT_SECONDS", raising=False)

    def install(due=(), unacked=0, fail=()):
        cur, s3 = FakeCursor(due, unacked), FakeS3(fail)

        @contextmanager
        def transaction():
            yield cur

        monkeypatch.setattr(sweeper.db, "transaction", transaction)
        monkeypatch.setattr(transit, "_s3", lambda: s3)
        return cur, s3

    return install


def _updates(cur):
    return [(s, p) for s, p in cur.executed if s.startswith("UPDATE") and "swept_at" in s]


def test_unacked_requests_fail_using_the_configured_ack_timeout(wired, monkeypatch):
    monkeypatch.setenv("TRANSFER_ACK_TIMEOUT_SECONDS", "75")
    cur, _ = wired(unacked=3)
    assert sweeper.handler({}, None)["failed_unacked"] == 3
    sql, params = cur.executed[0]
    assert "status = 'requested'" in sql and "owner_unresponsive" in sql and params == (75,)


def test_the_same_timeout_statement_serves_the_api_and_the_sweeper():
    cur = FakeCursor([])
    transfer_state.expire_unacked(cur, "transfer_id = %s", ("t",))
    assert cur.executed[0][1] == (60, "t") and "AND transfer_id = %s" in cur.executed[0][0]


def test_due_objects_are_deleted_then_their_transfers_marked(wired):
    cur, s3 = wired([("11111111-1111-1111-1111-111111111111", "k1"),
                     ("22222222-2222-2222-2222-222222222222", "k2")])
    result = sweeper.handler({}, None)
    assert result == {"failed_unacked": 0, "swept": 2, "delete_errors": 0}
    assert s3.calls == [("bucket", ["k1", "k2"])]
    (sql, params), = _updates(cur)
    assert "THEN 'expired' ELSE status END" in sql and "swept_at IS NULL" in sql
    assert params == (["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"],)


def test_only_in_flight_statuses_become_expired(wired):
    cur, _ = wired([("11111111-1111-1111-1111-111111111111", "k")])
    sweeper.handler({}, None)
    sql, _ = _updates(cur)[0]
    assert "status IN ('requested', 'uploading', 'ready')" in sql  # failed/expired keep their status


def test_the_age_comes_from_config_and_only_unswept_rows_are_selected(wired, monkeypatch):
    monkeypatch.setenv("SWEEPER_MAX_AGE_MINUTES", "7")
    cur, _ = wired([])
    sweeper.handler({}, None)
    sql, params = [(s, p) for s, p in cur.executed if s.startswith("SELECT")][0]
    assert "swept_at IS NULL" in sql and "make_interval(mins => %s)" in sql and params[0] == 7


def test_default_age_is_fifteen_minutes(wired):
    assert sweeper.max_age_minutes({}) == 15


def test_a_direct_invocation_may_override_the_age_but_not_with_junk(wired):
    assert sweeper.max_age_minutes({"max_age_minutes": 0}) == 0
    for junk in (-1, "5", True, None, 1.5):
        assert sweeper.max_age_minutes({"max_age_minutes": junk}) == 15


def test_objects_s3_failed_to_delete_are_not_marked_and_retry_next_run(wired):
    cur, _ = wired([("11111111-1111-1111-1111-111111111111", "ok"),
                    ("22222222-2222-2222-2222-222222222222", "bad")], fail={"bad"})
    result = sweeper.handler({}, None)
    assert result["swept"] == 1 and result["delete_errors"] == 1
    assert _updates(cur)[0][1] == (["11111111-1111-1111-1111-111111111111"],)


def test_nothing_deletable_means_no_update_and_no_looping(wired):
    cur, s3 = wired([("11111111-1111-1111-1111-111111111111", "bad")], fail={"bad"})
    sweeper.handler({}, None)
    assert _updates(cur) == [] and len(s3.calls) == 1


def test_an_idle_run_touches_neither_s3_nor_the_transfers(wired):
    cur, s3 = wired([])
    assert sweeper.handler({}, None) == {"failed_unacked": 0, "swept": 0, "delete_errors": 0}
    assert s3.calls == [] and _updates(cur) == []


def test_a_second_run_after_everything_is_swept_does_nothing(wired):
    cur, s3 = wired([("11111111-1111-1111-1111-111111111111", "k")])
    assert sweeper.handler({}, None)["swept"] == 1
    assert sweeper.handler({}, None)["swept"] == 0 and len(s3.calls) == 1


def test_a_row_with_no_s3_key_is_still_marked_without_calling_s3(wired):
    cur, s3 = wired([("11111111-1111-1111-1111-111111111111", None)])
    assert sweeper.handler({}, None)["swept"] == 1 and s3.calls == []


def test_a_backlog_is_drained_in_batches_of_the_s3_limit(wired):
    due = [(f"00000000-0000-0000-0000-{i:012d}", f"k{i}") for i in range(2500)]
    cur, s3 = wired(due)
    assert sweeper.handler({}, None)["swept"] == 2500
    assert [len(keys) for _, keys in s3.calls] == [1000, 1000, 500]


def test_only_counts_are_printed(wired, capsys):
    wired([("11111111-1111-1111-1111-111111111111", "secret-key")])
    sweeper.handler({}, None)
    out = capsys.readouterr().out
    assert "secret-key" not in out and "11111111" not in out and "swept" in out


# ── transit.delete_objects ───────────────────────────────────────────────────

def test_delete_objects_batches_and_reports_failures(monkeypatch):
    s3 = FakeS3(fail={"k5"})
    monkeypatch.setattr(transit, "_s3", lambda: s3)
    monkeypatch.setenv("TRANSIT_BUCKET", "bucket")
    keys = [f"k{i}" for i in range(1500)]
    deleted, errors = transit.delete_objects(keys)
    assert errors == 1 and len(deleted) == 1499 and "k5" not in deleted
    assert [len(k) for _, k in s3.calls] == [1000, 500]


def test_delete_objects_with_no_keys_makes_no_call(monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(transit, "_s3", lambda: s3)
    assert transit.delete_objects([]) == (set(), 0) and s3.calls == []
