"""Read-only post-deploy check of the E6 chunk index (E6-S2). Invoked through the migrate Lambda:
aws lambda invoke --function-name <MigrateFn> --payload '{"action":"verify","rows":5000}' out.json
Everything runs in one transaction that is always rolled back, so nothing is left behind. The
database is only reachable from inside the VPC, which is why this lives in a Lambda."""
import time
import uuid

DEFAULT_ROWS = 5000
MAX_ROWS = 50000
DIMENSION = 384


def _vec(*head):
    return "[" + ",".join(str(v) for v in list(head) + [0.0] * (DIMENSION - len(head))) + "]"


def _count(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchone()[0]


def _schema(cur):
    cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    row = cur.fetchone()
    cur.execute("SELECT default_version FROM pg_available_extensions WHERE name = 'vector'")
    available = cur.fetchone()
    cur.execute("SELECT version FROM schema_migrations ORDER BY version")
    migrations = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name = 'public_chunks' ORDER BY ordinal_position")
    chunk_columns = {name: kind for name, kind in cur.fetchall()}
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'public_files' "
                "AND column_name IN ('chunks_indexed_at', 'chunk_count') ORDER BY column_name")
    file_columns = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_public_chunks_embedding'")
    index = cur.fetchone()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'public_chunks_staging' "
                "ORDER BY ordinal_position")
    staging_columns = [r[0] for r in cur.fetchall()]
    return {
        "pgvector_installed": row[0] if row else None,
        "pgvector_available": available[0] if available else None,
        "migrations": migrations,
        "public_chunks_columns": chunk_columns,
        "public_files_new_columns": file_columns,
        "hnsw_index": index[0] if index else None,
        "staging_columns": staging_columns,
    }


def _smoke(cur):
    """Cascade, dimension check and cosine ordering on real tables (rolled back by the caller)."""
    team_id, file_id = str(uuid.uuid4()), "verify-" + uuid.uuid4().hex[:8]
    cur.execute("INSERT INTO teams (id, name, created_by) VALUES (%s, 'verify', 'verify')", (team_id,))
    cur.execute("INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, expires_at) "
                "VALUES (%s, 'verify', %s, 'v.txt', ARRAY['v'], now() + interval '1 day')", (file_id, team_id))
    cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) VALUES "
                "(%s, 0, 'far', %s::vector), (%s, 1, 'near', %s::vector)",
                (file_id, _vec(0, 1), file_id, _vec(1, 0.1)))
    cur.execute("SELECT text FROM public_chunks WHERE file_id = %s ORDER BY embedding <=> %s::vector LIMIT 1",
                (file_id, _vec(1)))
    nearest = cur.fetchone()[0]
    cur.execute("SAVEPOINT dim")
    try:
        cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) "
                    "VALUES (%s, 2, 'bad', '[1,2,3]'::vector)", (file_id,))
        rejects_wrong_dimension = False
    except Exception:  # a psycopg2 DataException; the layer's driver is not importable in unit tests
        rejects_wrong_dimension = True
    cur.execute("ROLLBACK TO SAVEPOINT dim")
    # Re-sync keeps chunks: the publish upsert never replaces the row.
    cur.execute("INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, expires_at) "
                "VALUES (%s, 'verify', %s, 'renamed.txt', ARRAY['w'], now() + interval '1 day') "
                "ON CONFLICT (file_id) DO UPDATE SET filename = EXCLUDED.filename", (file_id, team_id))
    kept_on_resync = _count(cur, "SELECT count(*) FROM public_chunks WHERE file_id = %s", (file_id,)) == 2
    cur.execute("DELETE FROM public_files WHERE file_id = %s", (file_id,))
    cascade_from_file = _count(cur, "SELECT count(*) FROM public_chunks WHERE file_id = %s", (file_id,)) == 0
    cur.execute("INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, expires_at) "
                "VALUES (%s, 'verify', %s, 'again.txt', ARRAY['v'], now() + interval '1 day')", (file_id, team_id))
    cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) VALUES (%s, 0, 'x', %s::vector)",
                (file_id, _vec(1)))
    cur.execute("DELETE FROM teams WHERE id = %s", (team_id,))
    cascade_from_team = _count(cur, "SELECT count(*) FROM public_chunks WHERE file_id = %s", (file_id,)) == 0
    return {"nearest_is_near": nearest == "near", "rejects_wrong_dimension": rejects_wrong_dimension,
            "chunks_kept_on_resync": kept_on_resync, "cascade_from_file": cascade_from_file,
            "cascade_from_team": cascade_from_team}


def _load(cur, rows):
    """HNSW build and top-20 query timings on random vectors in a temp table (not public_chunks)."""
    cur.execute("CREATE TEMP TABLE verify_chunks (id integer, embedding vector(384)) ON COMMIT DROP")
    start = time.perf_counter()
    cur.execute("INSERT INTO verify_chunks SELECT i, ('[' || string_agg(random()::text, ',') || ']')::vector "
                "FROM generate_series(1, %s) i, generate_series(1, 384) d GROUP BY i", (rows,))
    insert_s = time.perf_counter() - start
    start = time.perf_counter()
    cur.execute("CREATE INDEX ON verify_chunks USING hnsw (embedding vector_cosine_ops)")
    build_s = time.perf_counter() - start
    cur.execute("SELECT embedding::text FROM verify_chunks WHERE id = 1")
    probe = cur.fetchone()[0]
    timings = []
    for _ in range(5):
        start = time.perf_counter()
        cur.execute("SELECT id FROM verify_chunks ORDER BY embedding <=> %s::vector LIMIT 20", (probe,))
        cur.fetchall()
        timings.append((time.perf_counter() - start) * 1000)
    cur.execute("SET LOCAL enable_seqscan = off")
    cur.execute("EXPLAIN SELECT id FROM verify_chunks ORDER BY embedding <=> %s::vector LIMIT 20", (probe,))
    plan = "\n".join(r[0] for r in cur.fetchall())
    return {"rows": rows, "insert_seconds": round(insert_s, 2), "hnsw_build_seconds": round(build_s, 2),
            "top20_ms": [round(t, 1) for t in timings], "index_used_when_forced": "verify_chunks_embedding_idx" in plan}


def _ingest(cur):
    """Runs the real files.put_chunks handler against real tables (rolled back by the caller):
    batched upload, atomic swap, retries and the failure paths."""
    import files
    from common.errors import ApiError

    user, team_id, file_id = "verify-" + uuid.uuid4().hex[:8], str(uuid.uuid4()), str(uuid.uuid4())
    cur.execute("INSERT INTO teams (id, name, created_by) VALUES (%s, 'verify', %s)", (team_id, user))
    cur.execute("INSERT INTO memberships (user_id, team_id) VALUES (%s, %s)", (user, team_id))
    cur.execute("INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, expires_at) "
                "VALUES (%s, %s, %s, 'v.txt', ARRAY['v'], now() + interval '1 day')", (file_id, user, team_id))
    event = {"pathParameters": {"file_id": file_id}}

    def put(start, n, batch, total):
        chunks = [{"chunk_index": start + i, "text": f"verify {start + i}",
                   "embedding": [float(start + i + 1)] + [0.1] * 383} for i in range(n)]
        return files.put_chunks(cur, user, event, {"chunks": chunks, "batch": batch, "total_batches": total})

    def visible():
        return _count(cur, "SELECT count(*) FROM public_chunks WHERE file_id = %s", (file_id,))

    def rejected(call):
        try:
            call()
        except ApiError as exc:
            return exc.status == 400
        return False

    import json

    def answer(resp):
        return json.loads(resp["body"])

    first = [answer(put(0, 2, 1, 3)), answer(put(2, 2, 2, 3))]
    hidden_until_final = visible() == 0
    final = answer(put(4, 1, 3, 3))
    committed = final == {"file_id": file_id, "chunk_count": 5, "committed": True} and visible() == 5
    # A new upload does not disturb the committed set until its final batch.
    put(0, 2, 1, 2)
    old_set_visible_mid_upload = visible() == 5
    put(0, 2, 1, 2)  # a retried batch
    swapped = answer(put(2, 1, 2, 2))["chunk_count"] == 3 and visible() == 3
    retried_final_rejected = rejected(lambda: put(2, 1, 2, 2)) and visible() == 3
    cur.execute("SELECT chunk_count, chunks_indexed_at IS NOT NULL FROM public_files WHERE file_id = %s", (file_id,))
    counted = cur.fetchone() == (3, True)
    missing_batch_rejected = rejected(lambda: (put(0, 1, 1, 3), put(1, 1, 3, 3))) and visible() == 3
    cur.execute("UPDATE public_chunks_staging SET staged_at = now() - interval '2 hours' WHERE file_id = %s", (file_id,))
    cur.execute("DELETE FROM public_chunks_staging WHERE staged_at < now() - make_interval(mins => %s)", (60,))
    stale_staging_cleared = cur.rowcount > 0
    cur.execute("DELETE FROM public_files WHERE file_id = %s", (file_id,))
    cascade_clears_chunks = visible() == 0 and _count(
        cur, "SELECT count(*) FROM public_chunks_staging WHERE file_id = %s", (file_id,)) == 0
    return {"batches_not_committed_early": [r["committed"] for r in first] == [False, False],
            "hidden_until_final": hidden_until_final, "final_batch_commits": committed,
            "old_set_visible_mid_upload": old_set_visible_mid_upload, "reupload_swaps_atomically": swapped,
            "retried_final_batch_rejected_set_intact": retried_final_rejected,
            "file_row_counts_set": counted, "missing_batch_rejected_set_intact": missing_batch_rejected,
            "stale_staging_cleared": stale_staging_cleared, "cascade_clears_chunks_and_staging": cascade_clears_chunks}


def _retrieval(cur, other_team_chunks):
    """The real search.retrieval_search against real tables (rolled back by the caller). Another team
    holds many chunks nearer to the query than the caller's own team: the HNSW index filters after
    its scan, so without iterative scans the caller's results would be starved."""
    import search

    seeker, owner, outsider = ("verify-" + uuid.uuid4().hex[:8] for _ in range(3))
    mine, theirs = str(uuid.uuid4()), str(uuid.uuid4())
    files = {name: str(uuid.uuid4()) for name in ("mine", "own", "expired", "theirs")}
    for team in (mine, theirs):
        cur.execute("INSERT INTO teams (id, name, created_by) VALUES (%s, 'verify', 'verify')", (team,))
    for user, team in ((seeker, mine), (owner, mine), (outsider, theirs)):
        cur.execute("INSERT INTO memberships (user_id, team_id) VALUES (%s, %s)", (user, team))
    for name, who, team, days in (("mine", owner, mine, 45), ("own", seeker, mine, 45),
                                  ("expired", owner, mine, -1), ("theirs", outsider, theirs, 45)):
        cur.execute("INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, expires_at) "
                    "VALUES (%s, %s, %s, %s, ARRAY['v'], now() + make_interval(days => %s))",
                    (files[name], who, team, name + ".docx", days))
    near_query = _vec(1)
    for i in range(5):  # the caller's team: moderately far from the query
        cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) VALUES (%s, %s, %s, %s::vector)",
                    (files["mine"], i, f"mine {i}", _vec(0.5, 0.5 + i / 100)))
    for name in ("own", "expired"):  # identical to the query, but must be excluded
        cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) VALUES (%s, 0, 'x', %s::vector)",
                    (files[name], near_query))
    cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) "
                "SELECT %s, i, 'theirs', ('[1,' || string_agg((random() * 0.01)::text, ',') || ']')::vector "
                "FROM generate_series(0, %s - 1) i, generate_series(1, 383) d GROUP BY i",
                (files["theirs"], other_team_chunks))
    params = {"q": near_query, "team_id": mine, "user_id": seeker, "file_ids": None, "limit": 5}
    cur.execute("SET LOCAL enable_seqscan = off")  # make the planner use the HNSW index
    cur.execute("EXPLAIN " + search.RETRIEVAL_SQL, params)
    index_used = "idx_public_chunks_embedding" in " ".join(r[0] for r in cur.fetchall())
    cur.execute("SET LOCAL hnsw.iterative_scan = 'off'")
    cur.execute(search.RETRIEVAL_SQL, params)
    without_iterative_scan = len(cur.fetchall())  # informational: how many rows the filter leaves
    import json

    body = {"query_embedding": [1.0] + [0.0] * 383, "limit": 5}
    results = json.loads(search.retrieval_search(cur, seeker, body)["body"])["results"]
    scoped = json.loads(search.retrieval_search(cur, seeker, {**body, "file_ids": [files["theirs"]]})["body"])
    distances = [r["distance"] for r in results]
    return {"other_team_chunks": other_team_chunks, "index_used_by_planner": index_used,
            "rows_without_iterative_scan": without_iterative_scan,
            "caller_gets_full_limit": len(results) == 5,
            "only_own_team_files_returned": {r["file_id"] for r in results} == {files["mine"]},
            "ordered_by_distance": distances == sorted(distances),
            "no_owner_identity": all(set(r) == {"file_id", "filename", "chunk_index", "text", "distance"}
                                     for r in results),
            "foreign_file_ids_match_nothing": scoped["results"] == []}


def run(conn, rows=DEFAULT_ROWS):
    rows = max(100, min(int(rows), MAX_ROWS))
    try:
        with conn.cursor() as cur:
            return {"schema": _schema(cur), "smoke": _smoke(cur), "load": _load(cur, rows), "ingest": _ingest(cur),
                    "retrieval": _retrieval(cur, min(rows, 3000))}
    finally:
        conn.rollback()  # never commit: the check leaves no data behind
