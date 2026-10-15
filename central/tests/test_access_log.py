import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

from common.access_log import log_event  # noqa: E402


class FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))


def test_one_statement_serves_every_caller_with_nulls_for_what_is_absent():
    cur = FakeCursor()
    log_event(cur, "publish", "user-1", "team-1", "file-1")
    (sql, params), = cur.executed
    assert sql.startswith("INSERT INTO access_log") and "transfer_id, outcome" in sql
    assert params == ("publish", "user-1", "team-1", "file-1", None, None)


def test_transfer_and_outcome_are_recorded_when_given():
    cur = FakeCursor()
    log_event(cur, "transfer_request", "user-1", "team-1", "file-1", "transfer-1", "send_unconfirmed")
    assert cur.executed[0][1] == ("transfer_request", "user-1", "team-1", "file-1", "transfer-1", "send_unconfirmed")


def test_a_search_without_a_team_or_file_logs_nulls():
    cur = FakeCursor()
    log_event(cur, "search", "user-1")
    assert cur.executed[0][1] == ("search", "user-1", None, None, None, None)
