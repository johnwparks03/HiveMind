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
- [ ] Unit tests: retry, partial upload, wrong owner, bad dimension, over-limit.

## Technical notes
- Batch size is config, sized under API Gateway and Lambda payload limits.
- Route and IAM go in `infra/stack.py` (E6-S5).

## Notes
_(add during implementation)_
