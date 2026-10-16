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
- [ ] Migration `0006` runs `CREATE EXTENSION vector` and creates `public_chunks(file_id, chunk_index, text, embedding vector(384))`, primary key `(file_id, chunk_index)`, `file_id` references `public_files` with `ON DELETE CASCADE`.
- [ ] HNSW index on `embedding vector_cosine_ops`.
- [ ] `public_files` gains `chunks_indexed_at` and `chunk_count`.
- [ ] Deleting or expiring a `public_files` row removes its chunks.
- [ ] Aurora ACU range reviewed against index build and query load; adjusted if needed.

## Technical notes
- **verify-in-AWS:** pgvector version available on Aurora PG 16.8 and HNSW support; the migration user must be allowed to create the extension. Record findings in Notes.
- Embedding dimension is a config value; the 384 here matches all-MiniLM-L6-v2.
- Check how `central/tests` provide Postgres and whether the test DB can load pgvector (or needs a fake).

## Notes
_(add during implementation)_
