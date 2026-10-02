# E2-S4: Chunking, embeddings and Chroma

- **Epic:** E2 Local indexing and search
- **Track:** Local agent
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E2-S3
- **Spec refs:** Feature_List 1.4

## Story
As a user, I want content indexed by meaning so that vague queries still work.

## Acceptance criteria
- [ ] Text is chunked and embedded locally with all-MiniLM-L6-v2 and upserted to Chroma with date metadata.
- [ ] No file content leaves the machine during indexing.
- [ ] Re-indexing a changed file replaces its old chunks.

## Technical notes
- Model: sentence-transformers `all-MiniLM-L6-v2`, loaded once, CPU is fine. Chroma persistent client (file-backed) in the agent data dir.
- Chunk size/overlap: choose and record (suggest ~500 tokens with ~50 overlap). Chunk metadata: `file_id`, `file_created_at`, `file_modified_at`, `doc_date`, numeric timestamps so Chroma `where` range filters work.
- Replace, don't append: delete all chunks for `file_id` before upserting. Indexing runs in a background worker, never in a request handler.
- No tags are generated at index time.

## Notes
_(add during implementation)_
