import os
import sys
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import sweeper  # noqa: E402
from common import transfer_state, transit  # noqa: E402


def tid(i):
    return f"00000000-0000-0000-0000-{i:012d}"


def due(*keys):
    """Due rows as (transfer_id, s3_key, created_at), oldest first; created_at is just the index."""
    return [(tid(i), key, i) for i, key in enumerate(keys)]


class FakeCursor:
    """Behaves like the sweeper's queries: SELECT returns unswept rows after the keyset cursor,
    oldest first, up to the limit; the marking UPDATE sweeps the ids it is given."""

    def __init__(self, rows, unacked=0, stalled=0):
        self.rows, self.unacked, self.stalled = list(rows), unacked, stalled
        self.swept, self.executed, self.rowcount, self._result = set(), [], 0, []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if sql.startswith("SELECT"):
            after = params[1:3] if "(created_at, transfer_id) >" in sql else None
            matching = [r for r in sorted(self.rows, key=lambda r: (r[2], r[0]))
                        if r[0] not in self.swept and (after is None or (r[2], r[0]) > tuple(after))]
            self._result = matching[:params[-1]]
        elif "swept_at" in sql:
            self.swept.update(params[0])
        elif "owner_unresponsive" in sql:
            self.rowcount = self.unacked
        elif "upload_failed" in sql:
            self.rowcount = self.stalled

    def fetchall(self):
        return self._result


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
    for name in ("SWEEPER_MAX_AGE_MINUTES", "TRANSFER_ACK_TIMEOUT_SECONDS", "TRANSFER_UPLOAD_TIMEOUT_SECONDS",
                 "CHUNK_STAGING_TTL_MINUTES"):
        monkeypatch.delenv(name, raising=False)

    def install(rows=(), unacked=0, stalled=0, fail=()):
        cur, s3 = FakeCursor(rows, unacked, stalled), FakeS3(fail)

        @contextmanager
        def transaction():
            yield cur

        monkeypatch.setattr(sweeper.db, "transaction", transaction)
        monkeypatch.setattr(transit, "_s3", lambda: s3)
        return cur, s3

    return install


def _updates(cur):
    return [(s, p) for s, p in cur.executed if s.startswith("UPDATE") and "swept_at" in s]


def _selects(cur):
    return [(s, p) for s, p in cur.executed if s.startswith("SELECT")]


def test_unacked_requests_fail_using_the_configured_ack_timeout(wired, monkeypatch):
    monkeypatch.setenv("TRANSFER_ACK_TIMEOUT_SECONDS", "75")
    cur, _ = wired(unacked=3)
    assert sweeper.handler({}, None)["failed_unacked"] == 3
    sql, params = cur.executed[0]
    assert "status = 'requested'" in sql and "owner_unresponsive" in sql and params == (75,)


def test_stalled_uploads_fail_using_the_configured_upload_timeout(wired, monkeypatch):
    monkeypatch.setenv("TRANSFER_UPLOAD_TIMEOUT_SECONDS", "480")
    cur, _ = wired(stalled=2)
    assert sweeper.handler({}, None)["failed_stalled"] == 2
    sql, params = cur.executed[1]  # after the unacked statement
    assert "status = 'uploading'" in sql and "error_code = 'upload_failed'" in sql
    assert "updated_at < now()" in sql and params == (480,)


def test_a_direct_invocation_may_override_the_upload_timeout(wired):
    cur, _ = wired()
    sweeper.handler({"upload_timeout_seconds": 0}, None)
    assert cur.executed[1][1] == (0,)


def test_stale_chunk_staging_is_cleared_using_the_configured_ttl(wired, monkeypatch):
    cur, _ = wired()
    sweeper.handler({}, None)
    sql, params = cur.executed[-1]
    assert sql.startswith("DELETE FROM public_chunks_staging WHERE staged_at < now()") and params == (60,)
    monkeypatch.setenv("CHUNK_STAGING_TTL_MINUTES", "5")
    cur, _ = wired()
    sweeper.handler({}, None)
    assert cur.executed[-1][1] == (5,)


def test_the_same_timeout_statements_serve_the_api_and_the_sweeper():
    cur = FakeCursor([])
    transfer_state.apply_timeouts(cur, "transfer_id = %s", ("t",))
    (unacked, p1), (stalled, p2) = cur.executed
    assert "owner_unresponsive" in unacked and "upload_failed" in stalled  # unacked first
    assert p1 == (60, "t") and p2 == (600, "t")
    assert unacked.endswith("AND transfer_id = %s") and stalled.endswith("AND transfer_id = %s")


def test_due_objects_are_deleted_then_their_transfers_marked(wired):
    cur, s3 = wired(due("k1", "k2"))
    result = sweeper.handler({}, None)
    assert result == {"failed_unacked": 0, "failed_stalled": 0, "swept": 2, "delete_errors": 0}
    assert s3.calls == [("bucket", ["k1", "k2"])]
    (sql, params), = _updates(cur)
    assert "THEN 'expired' ELSE status END" in sql and "swept_at IS NULL" in sql
    assert params == ([tid(0), tid(1)],)


def test_only_in_flight_statuses_become_expired(wired):
    cur, _ = wired(due("k"))
    sweeper.handler({}, None)
    sql, _ = _updates(cur)[0]
    assert f"status IN {transfer_state.IN_FLIGHT}" in sql  # failed/expired keep their status


def test_the_age_comes_from_config_and_only_unswept_rows_are_selected(wired, monkeypatch):
    monkeypatch.setenv("SWEEPER_MAX_AGE_MINUTES", "7")
    cur, _ = wired([])
    sweeper.handler({}, None)
    sql, params = _selects(cur)[0]
    assert "swept_at IS NULL" in sql and "make_interval(mins => %s)" in sql and params[0] == 7
    assert "ORDER BY created_at, transfer_id" in sql


def test_default_age_is_fifteen_minutes(wired):
    assert sweeper.max_age_minutes({}) == 15


def test_a_direct_invocation_may_override_the_age_but_not_with_junk(wired):
    assert sweeper.max_age_minutes({"max_age_minutes": 0}) == 0
    for junk in (-1, "5", True, None, 1.5):
        assert sweeper.max_age_minutes({"max_age_minutes": junk}) == 15


def test_objects_s3_failed_to_delete_are_not_marked_and_retry_next_run(wired):
    cur, _ = wired(due("ok", "bad"), fail={"bad"})
    result = sweeper.handler({}, None)
    assert result["swept"] == 1 and result["delete_errors"] == 1
    assert _updates(cur)[0][1] == ([tid(0)],)
    assert tid(1) not in cur.swept  # still due: the next scheduled run tries it again


def test_nothing_deletable_means_no_update(wired):
    cur, s3 = wired(due("bad"), fail={"bad"})
    sweeper.handler({}, None)
    assert _updates(cur) == [] and len(s3.calls) == 1


def test_an_idle_run_touches_neither_s3_nor_the_transfers(wired):
    cur, s3 = wired([])
    assert sweeper.handler({}, None) == {"failed_unacked": 0, "failed_stalled": 0, "swept": 0,
                                         "delete_errors": 0}
    assert s3.calls == [] and _updates(cur) == []


def test_a_second_run_after_everything_is_swept_does_nothing(wired):
    cur, s3 = wired(due("k"))
    assert sweeper.handler({}, None)["swept"] == 1
    assert sweeper.handler({}, None)["swept"] == 0 and len(s3.calls) == 1


def test_a_row_with_no_s3_key_is_still_marked_without_calling_s3(wired):
    cur, s3 = wired(due(None))
    assert sweeper.handler({}, None)["swept"] == 1 and s3.calls == []


def test_a_backlog_is_drained_in_pages_of_the_s3_limit(wired):
    cur, s3 = wired(due(*[f"k{i}" for i in range(2500)]))
    assert sweeper.handler({}, None)["swept"] == 2500
    assert [len(keys) for _, keys in s3.calls] == [1000, 1000, 500]
    first, second, third = [p for _, p in _selects(cur)]
    assert len(first) == 2 and second[1:3] == (999, tid(999)) and third[1:3] == (1999, tid(1999))


def test_rows_that_keep_failing_do_not_block_newer_ones(wired):
    """A whole page of failing rows used to be reselected forever, starving everything after it."""
    keys = [f"bad{i}" for i in range(1000)] + ["fresh1", "fresh2"]
    cur, s3 = wired(due(*keys), fail={f"bad{i}" for i in range(1000)})
    result = sweeper.handler({}, None)
    assert result["swept"] == 2 and result["delete_errors"] == 1000
    assert cur.swept == {tid(1000), tid(1001)}


def test_only_counts_are_printed(wired, capsys):
    wired(due("secret-key"))
    sweeper.handler({}, None)
    out = capsys.readouterr().out
    assert "secret-key" not in out and "00000000-0000" not in out and "swept" in out


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
