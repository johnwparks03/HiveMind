"""PUT /files/{file_id}/chunks (E6-S3). Same scripted-cursor style as test_files.py: results are
returned in the order put_chunks fetches them (membership, file owner, staging stats)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import files  # noqa: E402
from test_files import FILE_ID, TEAM, _body, _event, fake_db  # noqa: E402,F401  (fake_db is a fixture)

OWNER = ("user-1",)
SECRET = "SECRET-TEXT"


def _chunk(index, dim=384, text=SECRET):
    return {"chunk_index": index, "text": f"{text} {index}", "embedding": [0.1] * dim}


def _chunks_body(n=2, batch=1, total=1, start=0):
    return {"chunks": [_chunk(start + i) for i in range(n)], "batch": batch, "total_batches": total}


def _put_chunks(body, file_id=FILE_ID):
    return files.handler(_event("PUT /files/{file_id}/chunks", file_id, body), None)


def _stats(count, batches=1, first=1, last=1, totals=1, staged_total=1, low=0, high=None):
    return (count, batches, first, last, totals, staged_total, low, count - 1 if high is None else high)


def test_a_single_batch_upload_commits_and_swaps_the_chunks(fake_db):
    cur = fake_db([TEAM, OWNER, _stats(2)])
    resp = _put_chunks(_chunks_body(2))
    assert resp["statusCode"] == 200
    assert _body(resp) == {"file_id": FILE_ID, "chunk_count": 2, "committed": True}
    sqls = cur.sqls()
    assert "FOR UPDATE" in sqls and "INSERT INTO public_chunks_staging" in sqls
    assert "DELETE FROM public_chunks WHERE" in sqls and "INSERT INTO public_chunks (file_id" in sqls
    assert "UPDATE public_files SET chunk_count" in sqls and cur.log_events() == ["chunks_put"]
    assert sqls.rindex("DELETE FROM public_chunks_staging") > sqls.index("INSERT INTO public_chunks (file_id")


def test_a_non_final_batch_only_stages(fake_db):
    cur = fake_db([TEAM, OWNER, _stats(4, batches=2, last=2, staged_total=3, high=3)])
    resp = _put_chunks(_chunks_body(2, batch=2, total=3, start=2))
    assert _body(resp) == {"file_id": FILE_ID, "chunk_count": 0, "committed": False}
    assert "DELETE FROM public_chunks WHERE" not in cur.sqls() and cur.log_events() == []
    assert "DELETE FROM public_chunks_staging" not in cur.sqls()  # only batch 1 clears staging


def test_batch_one_discards_earlier_staging_before_staging_its_own_chunks(fake_db):
    cur = fake_db([TEAM, OWNER, _stats(2, staged_total=2)])
    _put_chunks(_chunks_body(2, batch=1, total=2))
    statements = [s for s, _ in cur.executed]
    clear = next(i for i, s in enumerate(statements) if s.startswith("DELETE FROM public_chunks_staging"))
    stage = next(i for i, s in enumerate(statements) if s.startswith("INSERT INTO public_chunks_staging"))
    assert clear < stage


def test_a_retried_batch_is_an_upsert_so_it_leaves_one_set(fake_db):
    cur = fake_db([TEAM, OWNER, _stats(2)])
    _put_chunks(_chunks_body(2))
    insert = next(s for s, _ in cur.executed if s.startswith("INSERT INTO public_chunks_staging"))
    assert "ON CONFLICT (file_id, chunk_index) DO UPDATE" in insert


def test_vectors_are_sent_as_text_literals_cast_to_vector(fake_db):
    cur = fake_db([TEAM, OWNER, _stats(1)])
    _put_chunks(_chunks_body(1))
    sql, params = next((s, p) for s, p in cur.executed if s.startswith("INSERT INTO public_chunks_staging"))
    assert "%s::vector" in sql
    literal = params[5]
    assert literal.startswith("[0.1,") and literal.endswith("]") and literal.count(",") == 383


def test_an_empty_file_commits_an_empty_set(fake_db):
    cur = fake_db([TEAM, OWNER, (0, 0, None, None, 0, None, None, None)])
    resp = _put_chunks({"chunks": [], "batch": 1, "total_batches": 1})
    assert _body(resp) == {"file_id": FILE_ID, "chunk_count": 0, "committed": True}
    assert "INSERT INTO public_chunks_staging" not in cur.sqls() and cur.log_events() == ["chunks_put"]


def test_chunks_without_a_team_is_403_no_team(fake_db):
    cur = fake_db([None])
    resp = _put_chunks(_chunks_body(1))
    assert resp["statusCode"] == 403 and _body(resp)["error"]["code"] == "no_team"
    assert "public_chunks_staging" not in cur.sqls()


def test_chunks_for_an_unpublished_file_is_404(fake_db):
    cur = fake_db([TEAM, None])
    resp = _put_chunks(_chunks_body(1))
    assert resp["statusCode"] == 404 and _body(resp)["error"]["code"] == "not_found"
    assert "public_chunks_staging" not in cur.sqls()


def test_chunks_for_another_users_file_is_403_forbidden(fake_db):
    cur = fake_db([TEAM, ("someone-else",)])
    resp = _put_chunks(_chunks_body(1))
    assert resp["statusCode"] == 403 and _body(resp)["error"]["code"] == "forbidden"
    assert "public_chunks_staging" not in cur.sqls() and cur.log_events() == []


def test_a_bad_file_id_is_400(fake_db):
    fake_db([])
    assert _put_chunks(_chunks_body(1), file_id="nope")["statusCode"] == 400


def _with(**override):
    body = _chunks_body(1)
    body.update(override)
    return body


def _one(embedding=None, index=0, text=SECRET):
    return {"chunks": [{"chunk_index": index, "text": text,
                        "embedding": [0.1] * 384 if embedding is None else embedding}],
            "batch": 1, "total_batches": 1}


@pytest.mark.parametrize("body,field", [
    (_one([0.1] * 383), "chunks[0].embedding"),
    (_one([float("nan")] * 384), "chunks[0].embedding"),
    (_one([float("inf")] * 384), "chunks[0].embedding"),
    (_one([True] * 384), "chunks[0].embedding"),
    (_one(["0.1"] * 384), "chunks[0].embedding"),
    ({"chunks": [_chunk(0), _chunk(0)], "batch": 1, "total_batches": 1}, "chunks[1].chunk_index"),
    (_one(index=2000), "chunks[0].chunk_index"),
    (_one(index=-1), "chunks[0].chunk_index"),
    (_one(text="  "), "chunks[0].text"),
    ({"chunks": [_chunk(i) for i in range(101)], "batch": 1, "total_batches": 1}, "chunks"),
    ({"chunks": [], "batch": 1, "total_batches": 2}, "chunks"),
    ({"chunks": "nope", "batch": 1, "total_batches": 1}, "chunks"),
    (_with(batch=0), "batch"),
    (_with(batch=2), "batch"),
    (_with(batch="1"), "batch"),
    (_with(total_batches=21), "total_batches"),
    (_with(total_batches=0), "total_batches"),
    ({"chunks": [_chunk(0)]}, "batch"),
])
def test_bad_chunk_bodies_are_400_naming_fields_and_never_echoing_values(fake_db, body, field):
    cur = fake_db([])
    resp = _put_chunks(body)
    err = _body(resp)["error"]
    assert resp["statusCode"] == 400 and err["code"] == "invalid_request"
    assert field in err["details"]["fields"]
    assert SECRET not in resp["body"] and cur.executed == []  # rejected before touching the database


def test_the_batch_and_file_limits_come_from_config(fake_db, monkeypatch):
    monkeypatch.setenv("CHUNK_UPLOAD_BATCH_SIZE", "2")
    monkeypatch.setenv("MAX_CHUNKS_PER_FILE", "4")
    fake_db([])
    assert _put_chunks(_chunks_body(3, total=2))["statusCode"] == 400  # over the batch size
    assert _put_chunks(_chunks_body(2, total=3))["statusCode"] == 400  # more batches than 4 chunks allow


def test_a_file_over_the_chunk_limit_is_rejected(fake_db):
    fake_db([TEAM, OWNER, _stats(2001, batches=2, last=2, staged_total=3, high=2000)])
    resp = _put_chunks(_chunks_body(2, batch=2, total=3))
    assert resp["statusCode"] == 400 and _body(resp)["error"]["details"]["fields"] == ["chunks"]


def test_batches_that_disagree_on_total_batches_are_rejected(fake_db):
    fake_db([TEAM, OWNER, _stats(4, batches=2, last=2, totals=2, staged_total=2)])
    resp = _put_chunks(_chunks_body(2, batch=2, total=3))
    assert resp["statusCode"] == 400 and _body(resp)["error"]["details"]["fields"] == ["total_batches"]


def test_a_final_batch_with_a_missing_earlier_batch_is_rejected_and_changes_nothing(fake_db):
    # Also the retry-after-commit case: staging was emptied by the commit, so only this batch is
    # there. The swap must not run, and the committed set stays as it was.
    cur = fake_db([TEAM, OWNER, _stats(2, batches=1, first=3, last=3, staged_total=3)])
    resp = _put_chunks(_chunks_body(2, batch=3, total=3))
    assert resp["statusCode"] == 400 and _body(resp)["error"]["details"]["fields"] == ["batch"]
    assert "DELETE FROM public_chunks WHERE" not in cur.sqls() and cur.log_events() == []


def test_a_final_batch_with_gaps_in_chunk_indexes_is_rejected(fake_db):
    cur = fake_db([TEAM, OWNER, _stats(3, high=5)])
    resp = _put_chunks(_chunks_body(3))
    assert resp["statusCode"] == 400 and _body(resp)["error"]["details"]["fields"] == ["chunks"]
    assert "DELETE FROM public_chunks WHERE" not in cur.sqls()


def test_chunk_text_and_vectors_are_never_logged_or_returned(fake_db, capsys):
    fake_db([TEAM, OWNER])  # the stats query finds no scripted result: an unexpected error -> 503
    resp = _put_chunks(_chunks_body(1))
    out = capsys.readouterr()
    assert resp["statusCode"] == 503
    for text in (resp["body"], out.out, out.err):
        assert SECRET not in text and "0.1" not in text


def test_the_audit_event_carries_ids_only(fake_db):
    cur = fake_db([TEAM, OWNER, _stats(1)])
    _put_chunks(_chunks_body(1))
    params = next(p for s, p in cur.executed if s.startswith("INSERT INTO access_log"))
    assert params[0] == "chunks_put" and SECRET not in repr(params)
