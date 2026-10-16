# E6-S6: Agent chunk upload and Ask merge

- **Epic:** E6 Ask over teammates' documents
- **Track:** Local agent
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E6-S5
- **Spec refs:** `agent/app/central/publish.py`, `agent/app/indexing/indexer.py`, `agent/app/search/vector_store.py`, `agent/app/search/ask_service.py`, `agent/app/search/search_service.py`

## Story
As a user, I want my published files' chunks uploaded and my Ask to include teammates' chunks so that answers draw on the team's knowledge.

## Acceptance criteria
- [ ] After `PUT /files/{id}` succeeds, the publish queue reads the file's chunks and embeddings from Chroma and uploads them in batches via `PUT /files/{id}/chunks` (reuses queue retries and concurrency).
- [ ] Re-indexing a public file re-uploads its chunks; unpublish and delete rely on the central cascade.
- [ ] Backfill: already-published files without central chunks are uploaded.
- [ ] Central client method `retrieval_search(query_embedding, ...)`.
- [ ] `ask()` accepts an include-teammates option: embeds the topic locally, calls central retrieval, merges with local chunks (rank by distance, existing `ASK_MAX_*` caps), labels teammate excerpts.
- [ ] Sources saved in chats carry `source: "teammate"` and `file_id`.
- [ ] If central is unreachable, Ask falls back to local files and says so.
- [ ] Tests for publish upload, backfill, merge ranking and source flagging.

## Technical notes
- Bedrock stays agent-direct for the demo (see E6-S1).
- The system prompt must still treat excerpts as data, never instructions; teammate text is untrusted input.

## Notes
_(add during implementation)_
