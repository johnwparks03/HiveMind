# E6-S4: Retrieval search endpoint

- **Epic:** E6 Ask over teammates' documents
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E6-S2
- **Spec refs:** API_Contract `POST /retrieval/search`, `central/lambdas/search.py` (team scoping pattern), access log (E5-S3)

## Story
As a requester's agent, I want the top matching teammate chunks for a query vector so that Ask can answer from them.

## Acceptance criteria
- [x] `POST /retrieval/search` takes `{query_embedding, file_ids?, limit?}`; the server derives `team_id` from membership.
- [x] Excludes the caller's own files and expired rows; only files with indexed chunks are searched.
- [x] Returns `{file_id, filename, chunk_index, text, distance}` ordered by cosine distance; no owner identity.
- [x] Limit has a configured default and cap.
- [x] Query text never reaches central (vector only). Vectors and chunk text are never logged.
- [x] Access log records a retrieval event with ids only (new `event_type` in the contract).
- [x] Unit tests: team isolation, own-file exclusion, expiry, limit cap, dimension validation.

## Notes
Implemented (2026-10-16), not yet deployed or verified on AWS, so the other acceptance boxes stay unticked:
- `retrieval_search` in `central/lambdas/search.py` (same Lambda as `/search`), route `POST /retrieval/search` and config `RETRIEVAL_LIMIT_DEFAULT` 20 / `RETRIEVAL_LIMIT_MAX` 50 in `infra/stack.py`. No migration.
- Vector helpers moved from `files.py` to `central/lambdas/common/vectors.py` (`is_int`, `is_number`, `is_embedding`, `vector_literal`, `embedding_dimension`); behaviour unchanged.
- The query runs `SET LOCAL hnsw.iterative_scan = 'strict_order'` first. The HNSW index filters after its scan, so a selective filter (team, not-own, expiry, `file_ids`) could otherwise return too few rows.
- `limit` above the max is clamped, below 1 or non-integer is 400. `file_ids` that are foreign, unknown, expired or own match nothing (no error). Audit logs matched `file_id`s only (one row per distinct file; one id-less row when empty); the contract's section 5 row is corrected to match.
- Tests: `test_retrieval_search.py` (SQL scope and ordering, limits, 18 invalid bodies, no-team, logging, no leaks, 503, 401, plus a real-Postgres test that is skipped locally), `test_vectors.py`. `python -m pytest tests` in `central/`: 346 passed, 6 skipped.
- The migrate Lambda's `verify` action now also runs the real `retrieval_search` on Aurora (rolled back), with another team holding thousands of chunks nearer to the query than the caller's own. After deploy, run it and record `retrieval` here: `caller_gets_full_limit` and `only_own_team_files_returned` should be true; `rows_without_iterative_scan` shows what the filter would have left.
- Postman: the `Test Retrieval Search` folder (31 requests) is in the HiveMind collection (users A and B, `{{AWS_URL}}`, bearer auth, vectors built in pre-request scripts, runtime variables `retr_file_id` and `retr_own_file_id`, no collection variables declared or changed). Run it top to bottom.
- Postman `Test Retrieval Search` passed against the deployed stack (reported by the story owner, 2026-10-16). All acceptance criteria met; E6-S4 is done (see the iterative-scan caveat below).

## Verification on the deployed stack (2026-10-16)
`verify` action (real `retrieval_search` on Aurora, rolled back; the other team held 2,000 chunks nearer to the query than the caller's own): `caller_gets_full_limit`, `only_own_team_files_returned`, `ordered_by_distance`, `no_owner_identity` and `foreign_file_ids_match_nothing` are all true. The ingest and smoke checks from S2/S3 still pass.

Caveat: `index_used_by_planner` was **false** even with `enable_seqscan = off`, and `rows_without_iterative_scan` was 5 (no starvation). At this table size the planner does not choose the HNSW index for the join query, so the starvation scenario that the iterative scan protects against was not actually exercised. The results are correct; what is not yet proven is that `hnsw.iterative_scan = 'strict_order'` rescues a filtered HNSW scan on this stack. It is harmless when the index is not used, and matters only once tables are large enough for the planner to pick the index. Revisit if the team's chunk count grows into the tens of thousands.
