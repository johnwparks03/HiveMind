# E6-S3: Chunk ingest endpoint

- **Epic:** E6 Ask over teammates' documents
- **Track:** Central service
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E6-S2
- **Spec refs:** API_Contract `PUT /files/{id}/chunks`, `central/lambdas/files.py`

## Story
As an owner's agent, I want to upload a published file's chunks and embeddings so that teammates can ask questions about it.

## Acceptance criteria
- [ ] `PUT /files/{id}/chunks` accepts `{chunks:[{chunk_index, text, embedding}], batch, total_batches}`.
- [ ] Caller must own the file and the file must exist in `public_files`; otherwise the contract's error codes.
- [ ] Idempotent replace: a retried batch or whole upload leaves exactly one chunk set. Batches are staged and swapped on the final batch, so readers never see a partial set.
- [ ] Embedding length is validated against the configured dimension; per-file max chunks enforced (config).
- [ ] Sets `chunks_indexed_at` and `chunk_count` on commit.
- [ ] Nothing in the request body is logged.
- [x] Unit tests: retry, partial upload, wrong owner, bad dimension, over-limit.

## Technical notes
- Batch size is config, sized under API Gateway and Lambda payload limits.
- The route, config values and the FilesFn memory bump (512 MB) were added to `infra/stack.py` in this story, so they deploy with it; E6-S5 now only adds the retrieval route and sizing.

## Notes
Implemented (2026-10-16), not yet deployed or verified on AWS, so the other acceptance boxes stay unticked:
- `files.put_chunks` in `central/lambdas/files.py`; migration `0007_chunk_staging.sql` (staging table, cascades with the file); sweeper clears uploads staged longer than `CHUNK_STAGING_TTL_MINUTES`; `GET /files/mine` now returns `chunk_count`.
- Config in `infra/stack.py`: `CHUNK_UPLOAD_BATCH_SIZE` 100, `MAX_CHUNKS_PER_FILE` 2000, `EMBEDDING_DIMENSION` 384, `CHUNK_STAGING_TTL_MINUTES` 60.
- Retry rule: a re-sent final batch after commit gets `400` (staging is empty) and leaves the committed set intact; the agent restarts from batch 1 (documented in the contract).
- `chunks_put` logs `file_id` only (the access log has no details column).
- Tests: `central/tests/test_chunks_put.py` (35 cases), plus migration, sweeper and `files/mine` tests. `python -m pytest tests` in `central/`: 297 passed, 5 skipped.
- The migrate Lambda's `verify` action now also runs the real `put_chunks` against Aurora in a rolled-back transaction (`ingest` section). After deploy, run it as described in E6-S2, then tick the remaining boxes.
- Postman: the `Test Chunk Ingest` folder (37 requests) is in the HiveMind collection, parks45 account. It follows the existing conventions (users A and B, `{{AWS_URL}}`, bearer auth). Pre-request scripts build 384-float vectors. A runtime variable `chunk_file_id` is set with `pm.collectionVariables.set`; no collection variables were declared or changed. Run it top to bottom after the deploy (requests 07-35 depend on each other). Not yet run against the deployed stack.
- Still to do: deploy, run `verify`, run the Postman folder, integration test.
