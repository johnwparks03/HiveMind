"""POST /retrieval/search (E6-S4). Scripted-cursor style like test_search.py: results come back in the
order retrieval_search fetches them (membership, then the chunk rows)."""
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import migrate  # noqa: E402
import search  # noqa: E402
from test_migrations import DSN, fresh_db  # noqa: E402,F401
from test_search import TEAM, _call, _json, fake_db  # noqa: E402,F401  (fake_db is a fixture)

VEC = [0.1] * 384
SECRET = "SECRET-CHUNK-TEXT"


def chunk_row(file_id="f1", filename="notes.docx", index=0, text=SECRET, distance=0.1234567):
    return (file_id, filename, index, text, distance)


def _retrieve(body=None, **kwargs):
    return _call({"query_embedding": VEC} if body is None else body, route="POST /retrieval/search", **kwargs)


def _query(cur):
    return next((s, p) for s, p in cur.executed if "FROM public_chunks" in s)


@pytest.fixture(autouse=True)
def limits(monkeypatch):
    for name in ("RETRIEVAL_LIMIT_DEFAULT", "RETRIEVAL_LIMIT_MAX", "EMBEDDING_DIMENSION"):
        monkeypatch.delenv(name, raising=False)


def test_results_are_mapped_in_order_and_never_include_owner_identity(fake_db):
    cur = fake_db([TEAM, [chunk_row("f1", "a.docx", 2, "alpha", 0.01), chunk_row("f2", "b.docx", 0, "beta", 0.5)]])
    resp = _retrieve()
    assert resp["statusCode"] == 200
    assert _json(resp) == {"results": [
        {"file_id": "f1", "filename": "a.docx", "chunk_index": 2, "text": "alpha", "distance": 0.01},
        {"file_id": "f2", "filename": "b.docx", "chunk_index": 0, "text": "beta", "distance": 0.5}]}
    assert "owner" not in resp["body"] and "owner_online" not in resp["body"]
    assert cur.executed[1][0].startswith("SET LOCAL hnsw.iterative_scan")  # before the query


def test_distance_is_rounded_to_six_places(fake_db):
    fake_db([TEAM, [chunk_row(distance=0.123456789)]])
    assert _json(_retrieve())["results"][0]["distance"] == 0.123457


def test_the_query_is_scoped_to_the_team_excludes_own_and_expired_files_and_orders_by_cosine(fake_db):
    cur = fake_db([TEAM, []])
    _retrieve()
    sql, params = _query(cur)
    assert "pf.team_id = %(team_id)s" in sql and "pf.owner_id <> %(user_id)s" in sql
    assert "pf.expires_at > now()" in sql and "JOIN public_files pf ON pf.file_id = pc.file_id" in sql
    assert "ORDER BY pc.embedding <=> %(q)s::vector, pc.file_id, pc.chunk_index" in sql
    assert params["team_id"] == TEAM[0] and params["user_id"] == "user-1"


def test_the_vector_is_sent_as_a_text_literal(fake_db):
    cur = fake_db([TEAM, []])
    _retrieve()
    literal = _query(cur)[1]["q"]
    assert literal.startswith("[0.1,") and literal.endswith("]") and literal.count(",") == 383


def test_file_ids_default_to_none_and_are_passed_through(fake_db):
    cur = fake_db([TEAM, []])
    _retrieve()
    assert _query(cur)[1]["file_ids"] is None
    cur = fake_db([TEAM, []])
    _retrieve({"query_embedding": VEC, "file_ids": ["a", "b"]})
    assert _query(cur)[1]["file_ids"] == ["a", "b"]
    cur = fake_db([TEAM, []])
    _retrieve({"query_embedding": VEC, "file_ids": []})  # an empty scope matches nothing
    assert _query(cur)[1]["file_ids"] == []


def test_limit_defaults_and_is_capped_by_config(fake_db, monkeypatch):
    cur = fake_db([TEAM, []])
    _retrieve()
    assert _query(cur)[1]["limit"] == 20
    cur = fake_db([TEAM, []])
    _retrieve({"query_embedding": VEC, "limit": 999})
    assert _query(cur)[1]["limit"] == 50
    cur = fake_db([TEAM, []])
    _retrieve({"query_embedding": VEC, "limit": 7})
    assert _query(cur)[1]["limit"] == 7
    monkeypatch.setenv("RETRIEVAL_LIMIT_DEFAULT", "3")
    monkeypatch.setenv("RETRIEVAL_LIMIT_MAX", "5")
    cur = fake_db([TEAM, []])
    _retrieve()
    assert _query(cur)[1]["limit"] == 3
    cur = fake_db([TEAM, []])
    _retrieve({"query_embedding": VEC, "limit": 10})
    assert _query(cur)[1]["limit"] == 5


@pytest.mark.parametrize("body,field", [
    ({}, "query_embedding"),
    ({"query_embedding": [0.1] * 383}, "query_embedding"),
    ({"query_embedding": [0.1] * 385}, "query_embedding"),
    ({"query_embedding": "nope"}, "query_embedding"),
    ({"query_embedding": None}, "query_embedding"),
    ({"query_embedding": [float("nan")] * 384}, "query_embedding"),
    ({"query_embedding": [float("inf")] * 384}, "query_embedding"),
    ({"query_embedding": [True] * 384}, "query_embedding"),
    ({"query_embedding": ["0.1"] * 384}, "query_embedding"),
    ({"query_embedding": VEC, "file_ids": "abc"}, "file_ids"),
    ({"query_embedding": VEC, "file_ids": [1]}, "file_ids"),
    ({"query_embedding": VEC, "file_ids": [""]}, "file_ids"),
    ({"query_embedding": VEC, "file_ids": ["x"] * 201}, "file_ids"),
    ({"query_embedding": VEC, "limit": 0}, "limit"),
    ({"query_embedding": VEC, "limit": -1}, "limit"),
    ({"query_embedding": VEC, "limit": "5"}, "limit"),
    ({"query_embedding": VEC, "limit": True}, "limit"),
    ({"query_embedding": VEC, "limit": 2.5}, "limit"),
])
def test_bad_bodies_are_400_naming_the_field_before_any_query(fake_db, body, field):
    cur = fake_db([])
    resp = _retrieve(body)
    err = _json(resp)["error"]
    assert resp["statusCode"] == 400 and err["code"] == "invalid_request"
    assert field in err["details"]["fields"]
    assert cur.executed == []


def test_the_dimension_comes_from_config(fake_db, monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIMENSION", "3")
    cur = fake_db([TEAM, []])
    assert _retrieve({"query_embedding": [0.1, 0.2, 0.3]})["statusCode"] == 200
    assert _query(cur)[1]["q"] == "[0.1,0.2,0.3]"
    assert _retrieve({"query_embedding": VEC})["statusCode"] == 400


def test_no_team_is_403_and_runs_no_query(fake_db):
    cur = fake_db([None])
    resp = _retrieve()
    assert resp["statusCode"] == 403 and _json(resp)["error"]["code"] == "no_team"
    assert not any("public_chunks" in s for s, _ in cur.executed) and cur.log_rows() == []


def test_a_search_with_no_matches_is_200_empty_and_logs_one_row_without_a_file(fake_db):
    cur = fake_db([TEAM, []])
    resp = _retrieve()
    assert resp["statusCode"] == 200 and _json(resp) == {"results": []}
    rows = cur.log_rows()
    assert len(rows) == 1 and rows[0][0] == "retrieval_search" and rows[0][3] is None


def test_each_matched_file_is_logged_once_even_with_several_chunks(fake_db):
    cur = fake_db([TEAM, [chunk_row("f1", index=0), chunk_row("f2", index=0), chunk_row("f1", index=1)]])
    _retrieve()
    rows = cur.log_rows()
    assert [r[0] for r in rows] == ["retrieval_search", "retrieval_search"]
    assert [r[3] for r in rows] == ["f1", "f2"]


def test_the_vector_and_chunk_text_are_never_logged_or_leaked(fake_db, capsys):
    cur = fake_db([TEAM, [chunk_row(text=SECRET)]])
    _retrieve()
    out = capsys.readouterr()
    assert all(SECRET not in repr(p) and "0.1" not in repr(p) for p in cur.log_rows())
    assert SECRET not in out.out + out.err and "0.1" not in out.out + out.err


def test_a_database_error_is_503_without_leaking(fake_db, capsys):
    cur = fake_db([TEAM, []])

    def boom():
        raise RuntimeError(f"boom {SECRET}")

    cur.fetchall = boom
    resp = _retrieve()
    out = capsys.readouterr()
    assert resp["statusCode"] == 503 and _json(resp)["error"]["code"] == "service_unavailable"
    assert SECRET not in resp["body"] + out.out + out.err and "RuntimeError" in out.out


def test_retrieval_without_a_token_is_401(fake_db):
    fake_db([])
    assert _call({"query_embedding": VEC}, route="POST /retrieval/search", authed=False)["statusCode"] == 401


@pytest.mark.skipif(not DSN, reason="set HIVEMIND_TEST_DATABASE_URL to run against a real Postgres (pgvector 0.8+)")
def test_retrieval_sql_against_real_postgres(fresh_db):
    def vec(*head):
        return "[" + ",".join(str(v) for v in list(head) + [0.0] * (384 - len(head))) + "]"

    mine, theirs = str(uuid.uuid4()), str(uuid.uuid4())
    with fresh_db, fresh_db.cursor() as cur:
        migrate.apply_migrations(cur)
        for team in (mine, theirs):
            cur.execute("INSERT INTO teams (id, name, created_by) VALUES (%s, 'T', 'x')", (team,))
        for user, team in (("seeker", mine), ("owner", mine), ("outsider", theirs)):
            cur.execute("INSERT INTO memberships (user_id, team_id) VALUES (%s, %s)", (user, team))

        def publish(file_id, owner, team, days=45):
            cur.execute("INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, expires_at) "
                        "VALUES (%s, %s, %s, %s, ARRAY['x'], now() + make_interval(days => %s))",
                        (file_id, owner, team, file_id + ".docx", days))

        publish("near", "owner", mine)
        publish("far", "owner", mine)
        publish("own", "seeker", mine)
        publish("expired", "owner", mine, days=-1)
        publish("other-team", "outsider", theirs)
        chunks = [("near", 0, vec(1, 0.1)), ("far", 0, vec(0, 1)), ("own", 0, vec(1)),
                  ("expired", 0, vec(1)), ("other-team", 0, vec(1))]
        for file_id, index, literal in chunks:
            cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) "
                        "VALUES (%s, %s, 'text', %s::vector)", (file_id, index, literal))
        body = {"query_embedding": [1.0] + [0.0] * 383}
        results = _json(search.retrieval_search(cur, "seeker", body))["results"]
        assert [r["file_id"] for r in results] == ["near", "far"]  # own, expired and other-team excluded
        assert results[0]["distance"] < results[1]["distance"]
        scoped = _json(search.retrieval_search(cur, "seeker", {**body, "file_ids": ["far", "other-team", "nope"]}))
        assert [r["file_id"] for r in scoped["results"]] == ["far"]  # foreign and unknown ids match nothing
