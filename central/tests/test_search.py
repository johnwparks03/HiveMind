import datetime
import json
import os
import sys
import uuid
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import migrate  # noqa: E402
import search  # noqa: E402
from test_migrations import DSN, fresh_db  # noqa: E402,F401

TEAM = (str(uuid.uuid4()), "Alpha")
T0 = datetime.datetime(2026, 9, 29, 9, 0, tzinfo=datetime.timezone.utc)
T1 = datetime.datetime(2026, 11, 13, 9, 0, tzinfo=datetime.timezone.utc)
SECRET_TOPIC = "CONFIDENTIAL-TOPIC-MARKER"


def row(file_id="f1", filename="notes.docx", tags=("meeting",), online=False):
    return (file_id, filename, list(tags), T0, T0, T1, online)


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

    def search_call(self):
        return next((s, p) for s, p in self.executed if "FROM public_files" in s)

    def log_rows(self):
        return [p for s, p in self.executed if s.startswith("INSERT INTO access_log")]


@pytest.fixture(autouse=True)
def cap(monkeypatch):
    monkeypatch.setenv("SEARCH_RESULT_CAP", "7")


@pytest.fixture
def fake_db(monkeypatch):
    def install(results):
        cur = FakeCursor(results)

        @contextmanager
        def transaction():
            yield cur

        monkeypatch.setattr(search.db, "transaction", transaction)
        return cur

    return install


def _event(body=None, route="POST /search", sub="user-1", authed=True):
    event = {"routeKey": route, "body": json.dumps(body) if body is not None else None}
    if authed:
        event["requestContext"] = {"authorizer": {"jwt": {"claims": {"sub": sub}}}}
    return event


def _call(body=None, **kwargs):
    return search.handler(_event(body, **kwargs), None)


def _json(resp):
    return json.loads(resp["body"])


def test_topic_search_maps_rows_and_never_returns_owner_identity(fake_db):
    cur = fake_db([TEAM, [row("f1", "Q3_Contracts.docx", ["client", "legal"], online=True)]])
    resp = _call({"topic": "contracts"})
    assert resp["statusCode"] == 200
    assert _json(resp) == {"results": [{
        "file_id": "f1", "filename": "Q3_Contracts.docx", "tags": ["client", "legal"],
        "file_created_at": "2026-09-29T09:00:00.000000Z", "file_modified_at": "2026-09-29T09:00:00.000000Z",
        "expires_at": "2026-11-13T09:00:00.000000Z", "owner_online": True}]}
    assert "owner" not in resp["body"].replace("owner_online", "")
    sql, params = cur.search_call()
    assert "pf.owner_id) AS owner_online" in sql and "SELECT pf.file_id, pf.filename" in sql
    assert "pf.owner_id <>" in sql.replace("\n", " ") and "pf.expires_at > now()" in sql
    assert params["team_id"] == TEAM[0] and params["user_id"] == "user-1"


def test_topic_is_matched_as_any_word_and_ranked_before_recency(fake_db):
    cur = fake_db([TEAM, []])
    _call({"topic": "Q3 client-contracts!"})
    sql, params = cur.search_call()
    assert params["topic_query"] == "Q3 or client or contracts"
    assert "websearch_to_tsquery('english'" in sql and "pf.search_vector @@ q" in sql
    assert "ORDER BY ts_rank(pf.search_vector, q) DESC, coalesce(" in sql


@pytest.mark.parametrize("body", [{}, {"topic": None}, {"topic": "   "}, {"topic": ""}])
def test_no_topic_means_all_files_newest_first(fake_db, body):
    cur = fake_db([TEAM, []])
    assert _call(body)["statusCode"] == 200
    sql, params = cur.search_call()
    assert "search_vector" not in sql.replace("pf.search_vector", "") and "ts_rank" not in sql
    assert "topic_query" not in params
    assert "ORDER BY coalesce(pf.file_modified_at" in sql


def test_a_topic_with_no_words_is_an_empty_query_not_an_error(fake_db):
    cur = fake_db([TEAM, []])
    assert _json(_call({"topic": "???"})) == {"results": []}
    assert cur.search_call()[1]["topic_query"] == ""


def test_dates_are_passed_through_and_either_date_may_match(fake_db):
    cur = fake_db([TEAM, []])
    _call({"date_from": "2026-09-29T00:00:00-04:00", "date_to": "2026-09-29T23:59:59-04:00"})
    sql, params = cur.search_call()
    assert params["date_from"].utcoffset() == datetime.timedelta(hours=-4)
    assert params["date_to"].day == 29
    assert "pf.file_created_at BETWEEN" in sql and "pf.file_modified_at BETWEEN" in sql
    assert " OR " in sql


def test_one_open_ended_bound_is_allowed(fake_db):
    cur = fake_db([TEAM, []])
    assert _call({"date_from": "2026-09-29T00:00:00Z"})["statusCode"] == 200
    assert cur.search_call()[1]["date_to"] is None


def test_the_result_cap_comes_from_config(fake_db):
    cur = fake_db([TEAM, []])
    _call({})
    assert cur.search_call()[1]["cap"] == 7


def test_the_cap_defaults_to_twenty(fake_db, monkeypatch):
    monkeypatch.delenv("SEARCH_RESULT_CAP")
    cur = fake_db([TEAM, []])
    _call({})
    assert cur.search_call()[1]["cap"] == 20


def test_no_team_is_403(fake_db):
    cur = fake_db([None])
    resp = _call({"topic": "x"})
    assert resp["statusCode"] == 403 and _json(resp)["error"]["code"] == "no_team"
    assert not any("FROM public_files" in s for s, _ in cur.executed)


@pytest.mark.parametrize("body,fields", [
    ({"topic": 5}, ["topic"]),
    ({"topic": "x" * 501}, ["topic"]),
    ({"date_from": "2026-09-29T00:00:00"}, ["date_from"]),          # no timezone
    ({"date_to": "not-a-date"}, ["date_to"]),
    ({"date_from": 7}, ["date_from"]),
    ({"date_from": "2026-10-02T00:00:00Z", "date_to": "2026-10-01T00:00:00Z"}, ["date_from", "date_to"]),
    ({"topic": 5, "date_to": "nope"}, ["topic", "date_to"]),
])
def test_validation_names_fields_only(fake_db, body, fields):
    fake_db([TEAM, []])
    resp = _call(body)
    assert resp["statusCode"] == 400
    err = _json(resp)["error"]
    assert err["code"] == "invalid_request" and err["details"]["fields"] == fields


def test_malformed_json_is_400(fake_db):
    fake_db([TEAM, []])
    event = _event(None)
    event["body"] = "{nope"
    assert search.handler(event, None)["statusCode"] == 400


def test_one_log_row_per_matched_file_with_ids_only(fake_db):
    cur = fake_db([TEAM, [row("f1"), row("f2")]])
    _call({"topic": SECRET_TOPIC, "date_from": "2026-09-29T00:00:00Z"})
    assert cur.log_rows() == [("search", "user-1", TEAM[0], "f1"), ("search", "user-1", TEAM[0], "f2")]


def test_an_empty_search_is_still_logged_once_without_a_file(fake_db):
    cur = fake_db([TEAM, []])
    _call({"topic": "nothing"})
    assert cur.log_rows() == [("search", "user-1", TEAM[0], None)]


def test_the_topic_is_never_logged_or_stored(fake_db, capsys):
    cur = fake_db([TEAM, [row("f1")]])
    _call({"topic": SECRET_TOPIC})
    assert all(SECRET_TOPIC not in str(p) for p in cur.log_rows())
    out = capsys.readouterr()
    assert SECRET_TOPIC not in out.out + out.err


def test_unexpected_errors_are_503_and_log_only_the_class(fake_db, capsys):
    cur = fake_db([TEAM])
    cur.fetchall = lambda: (_ for _ in ()).throw(RuntimeError(f"boom {SECRET_TOPIC}"))
    resp = _call({"topic": SECRET_TOPIC})
    out = capsys.readouterr()
    assert resp["statusCode"] == 503 and _json(resp)["error"]["code"] == "service_unavailable"
    assert SECRET_TOPIC not in out.out + out.err + resp["body"] and "RuntimeError" in out.out


def test_unauthenticated_is_401(fake_db):
    fake_db([TEAM, []])
    assert _call({}, authed=False)["statusCode"] == 401


def test_unknown_route_is_404(fake_db):
    fake_db([TEAM, []])
    assert _call({}, route="POST /searches")["statusCode"] == 404


@pytest.mark.skipif(not DSN, reason="set HIVEMIND_TEST_DATABASE_URL to run against a real Postgres")
def test_search_sql_against_real_postgres(fresh_db):  # noqa: F811
    """Runs the real query: expiry, own-file exclusion, team scope, dates, ranking, cap, online."""
    team, other = str(uuid.uuid4()), str(uuid.uuid4())
    day = lambda n: f"2026-0{n}-01T00:00:00Z"  # noqa: E731
    with fresh_db, fresh_db.cursor() as cur:
        migrate.apply_migrations(cur)
        for tid in (team, other):
            cur.execute("INSERT INTO teams (id, name, created_by) VALUES (%s, 'T', 'seeker')", (tid,))
        for user, tid in (("seeker", team), ("pub", team), ("away", other)):
            cur.execute("INSERT INTO memberships (user_id, team_id) VALUES (%s, %s)", (user, tid))
        cur.execute("INSERT INTO connections (connection_id, user_id) VALUES ('c1', 'pub')")

        def add(file_id, owner, tid, filename, tags, created, modified, expires="now() + interval '10 days'"):
            cur.execute(
                "INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, file_created_at, "
                f"file_modified_at, expires_at) VALUES (%s, %s, %s, %s, %s, %s, %s, {expires})",
                (file_id, owner, tid, filename, tags, created, modified))

        add("hit", "pub", team, "Client_Contracts.docx", ["renewal"], day(7), day(8))
        add("weak", "pub", team, "notes.txt", ["contracts"], day(5), day(6))
        add("old", "pub", team, "Client_Contracts_old.docx", ["renewal"], day(1), day(2),
            expires="now() - interval '1 day'")           # expired: never returned
        add("mine", "seeker", team, "Client_Contracts_mine.docx", [], day(7), day(7))  # own file
        add("other", "away", other, "Client_Contracts_other.docx", [], day(7), day(7))  # other team
        add("undated", "pub", team, "Client_Undated.docx", [], None, None)

        def run(**body):
            out = _json(search.search(cur, "seeker", {"topic": None, **body}))
            return [r["file_id"] for r in out["results"]], out["results"]

        ids, results = run(topic="client contracts")
        assert ids[0] == "hit" and "weak" in ids and "old" not in ids        # ranked, expiry honoured
        assert not {"mine", "other"} & set(ids)
        assert next(r for r in results if r["file_id"] == "hit")["owner_online"] is True
        assert next(r for r in results if r["file_id"] == "weak")["owner_online"] is True
        assert run()[0] == ["undated", "hit", "weak"]  # newest first; undated falls back to published_at
        assert run(date_from=day(7), date_to=day(8))[0] == ["hit"]             # created or modified
        assert run(date_from="2026-08-01T00:00:00Z", date_to="2026-08-01T00:00:00Z")[0] == ["hit"]
        assert run(date_from="2027-01-01T00:00:00Z")[0] == []                  # undated never in a range
        assert len(run(topic="client")[0]) == 3
