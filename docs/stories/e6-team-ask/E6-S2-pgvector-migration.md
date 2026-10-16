# E6-S2: pgvector migration and chunk table

- **Epic:** E6 Ask over teammates' documents
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E6-S1
- **Spec refs:** API_Contract (chunks), `central/lambdas/migrations/0001`-`0005`, `infra/stack.py` Aurora definition

## Story
As the central service, I want a vector-capable chunk table so that teammate content can be searched by similarity.

## Acceptance criteria
- [x] Migration `0006` runs `CREATE EXTENSION vector` and creates `public_chunks(file_id, chunk_index, text, embedding vector(384))`, primary key `(file_id, chunk_index)`, `file_id` references `public_files` with `ON DELETE CASCADE`.
- [x] HNSW index on `embedding vector_cosine_ops`.
- [x] `public_files` gains `chunks_indexed_at` and `chunk_count`.
- [x] Deleting or expiring a `public_files` row removes its chunks.
- [x] Aurora ACU range reviewed against index build and query load; adjusted if needed.

## Technical notes
- **verify-in-AWS:** pgvector version available on Aurora PG 16.8 and HNSW support; the migration user must be allowed to create the extension. Record findings in Notes.
- Embedding dimension is a config value; the 384 here matches all-MiniLM-L6-v2.
- Check how `central/tests` provide Postgres and whether the test DB can load pgvector (or needs a fake).

## Notes
Implemented (2026-10-16): `0006_chunk_index.sql`, Aurora max ACU 1 -> 2 (`infra/stack.py`), and migration tests. The `fresh_db` test fixture now installs pgvector in `public` and keeps `public` on the search_path (the test Postgres must ship pgvector, e.g. `pgvector/pgvector:pg16`).

Verified locally: `python -m pytest tests` in `central/` gives 257 passed, 5 skipped. The DB-backed tests (cascade from file and team, publish upsert keeps chunks, dimension check, cosine ordering) are written but **skipped here**: no Docker or Postgres on this machine. Run them with `HIVEMIND_TEST_DATABASE_URL` pointing at a pgvector Postgres.

Still to do (acceptance boxes stay unticked until then):
- [ ] verify-in-AWS: pgvector version and HNSW support on Aurora PG 16.8 (`pg_available_extensions`), and that user `hivemind` can `CREATE EXTENSION vector`. Do this before deploying, because the migration batch is one transaction and a failure blocks the deploy.
- [ ] Synthetic load (e.g. 50k x 384) for HNSW build time and top-20 cosine latency at 0.5-2 ACU.
- [ ] Run the DB-backed tests against a pgvector Postgres.
- [ ] `cdk diff`, then a coordinated `cdk deploy`; confirm `schema_migrations` lists `0006_chunk_index.sql`.

Post-deploy check (added after the first deploy; the migration ran and the cluster is 0.5-2 ACU): the migrate Lambda has a read-only `verify` action. It reports the pgvector version, `public_chunks` columns and the HNSW index, runs the cascade / dimension / cosine smoke tests, and times an HNSW build and top-20 query on random vectors in a temp table. It runs in one transaction that is always rolled back.

    aws lambda invoke --function-name <MigrateFn> --region us-east-1 --cli-binary-format raw-in-base64-out --payload '{"action":"verify","rows":5000}' out.json; cat out.json

Needs a deploy of this commit first. Record the output here. `rows` is clamped to 100-50000; the Lambda timeout is 120 s, so raise `rows` gradually.

## Verification results (2026-10-16, deployed stack, `verify` action)
- pgvector **0.8.0** on Aurora PG 16.8 (installed = available); HNSW supported. User `hivemind` can create the extension. Migrations 0001-0006 applied.
- `public_chunks` and both new `public_files` columns exist; index is `hnsw (embedding vector_cosine_ops)`.
- Smoke (rolled back): cosine ordering correct, wrong dimension rejected, chunks kept on publish re-sync, cascade works from file and from team.
- Load on random 384-dim vectors, cluster at 0.5-2 ACU:
  - 5,000 rows: insert 1.2 s, HNSW build 2.2 s, top-20 query 1.5-3.6 ms.
  - 20,000 rows: insert 5.6 s, HNSW build 16.9 s, top-20 query 3.2-4.7 ms.
  - Build time grows faster than linearly; a 50k+ index build would approach the Lambda's 120 s limit in the verify action, but real ingest builds the index incrementally per insert, so this is not a runtime limit. The query planner uses the index when forced (`index_used_when_forced`).
- ACU max 2 is sufficient for this scale; revisit if a team's index passes ~50k chunks.
- Not run: the DB-backed pytest tests (no pgvector Postgres locally), though the same behaviours passed on the real database via `verify`.
