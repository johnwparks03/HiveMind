# E6-S6: Agent chunk upload and Ask merge

- **Epic:** E6 Ask over teammates' documents
- **Track:** Local agent
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E6-S5
- **Spec refs:** `agent/app/central/publish.py`, `agent/app/indexing/indexer.py`, `agent/app/indexing/vector_store.py`, `agent/app/search/ask_service.py`, `agent/app/search/search_service.py`

## Story
As a user, I want my published files' chunks uploaded and my Ask to include teammates' chunks so that answers draw on the team's knowledge.

## Acceptance criteria
- [x] After `PUT /files/{id}` succeeds, the publish queue reads the file's chunks and embeddings from Chroma and uploads them in batches via `PUT /files/{id}/chunks` (reuses queue retries and concurrency).
- [x] Re-indexing a public file re-uploads its chunks. Unpublish and delete remove them centrally through the existing cascade, and the agent now actually sends the central unpublish when a published file is deleted, removed with its folder or found missing (decided with the user, 2026-10-17).
- [x] Backfill: already-published files without central chunks are uploaded.
- [x] Central client call for retrieval (`agent/app/central/retrieval.py`).
- [x] `ask()` accepts an include-teammates option: embeds the topic locally, calls central retrieval, merges with local chunks (rank by distance, existing `ASK_MAX_*` caps), labels teammate excerpts.
- [x] Sources saved in chats carry `source` ("local" | "teammate") and `file_id`.
- [x] If central is unreachable, Ask falls back to local files and says so.
- [x] Tests for publish upload, backfill, merge ranking and source flagging.

## Technical notes
- Bedrock stays agent-direct for the demo (see E6-S1).
- The system prompt must still treat excerpts as data, never instructions; teammate text is untrusted input.

## Notes
Implemented (2026-10-17). Decisions confirmed with the user: when Ask is narrowed to chosen folders/files, teammates are skipped (`local_scope`); delete sync is part of this story.

**Publish side**
- `config.py`: `CHUNK_UPLOAD_BATCH_SIZE` 100, `MAX_CHUNKS_PER_FILE` 2000 (must match central), `CHUNK_UPLOAD_TIMEOUT_SECONDS` 60, `TEAMMATE_CHUNK_LIMIT` 20. `central/client.py` lets a caller pass its own timeout.
- `indexing/vector_store.py`: `get_file_chunks` (sorted, paged, list embeddings) and `has_chunks`.
- `central/publish.py`: after `PUT /files/{id}` and the state write, `_upload_chunks` sends batches of `{chunks, batch, total_batches}`, always starting at batch 1; only the first `MAX_CHUNKS_PER_FILE` chunks are sent; a file with no chunks uploads an empty set (this also clears an earlier version's chunks; I changed the plan, which said to skip); a gap in the chunk indexes (mid re-index) sends nothing and retries. A 400/403/404 on the chunk upload fails the file at once (`_PermanentFailure`).
- **Bug avoided:** `retry()` used to decide the direction from `public_state`, so a public file whose chunk upload failed would have been retried as an unpublish. The failed direction is now stored in a new `files.publish_failed_intent` column (older rows keep the old guess).
- `db.py`: `publish_queue` loses its foreign key to `files` (so a queued unpublish can outlive a deleted file) and `files` gains `publish_failed_intent`. Both are applied to existing databases by idempotent migrations in `init_db`, keeping queued rows.
- `folders/scanner.py`: re-indexing a public file queues a publish (or an unpublish if it no longer indexes); deleting a file, removing a folder, `exclude_files` and a rescan that finds a file missing queue an unpublish for every file that is public or has a publish queued. These are queued after the scan's own transaction closes (SQLite allows one writer).
- Reconcile follows every page of `GET /files/mine` (before, only the first page was read, which would also have wrongly un-published files beyond 100) and backfills `chunk_count == 0` files that are indexed, public, not failed, have local chunks and nothing queued, without resetting any backoff.

**Ask side**
- `central/retrieval.py` (`search`): `no_team` / `central_unavailable` mapping like the existing central search.
- `search/ask_service.py`: `ask(..., include_teammates=False)`. Teammate rows are grouped per file into the same dicts as local ones, ranked together by cosine distance, and the existing caps apply unchanged; teammate blocks are headed `(teammate)` and sources carry `source`. No more early "no match" before teammates are consulted. The prompt now covers teammate text and keeps the untrusted-text sentence. Response shape is unchanged when the option is off.
- Skip reasons: `local_scope`, `no_topic`, `no_team`, `central_unavailable`, and one I added, `date_filter` (central cannot apply a date range to chunks, so mixing teammates in would contradict the question).
- Routes: `include_teammates` on `POST /ask` and `POST /chats/{id}/messages`; the live chat message carries `teammate_skipped_reason`, which is not saved with the chat (saved sources keep their `source` flag).

**Docs:** contract 2.5a and section 6, Feature_List and Blueprint known limitations, `CLAUDE.md` limitations.

**Tests (agent):** `test_chunk_sync.py` (40) and `test_ask_teammates.py` (22) are new; `test_publish.py` and `test_chats.py` needed small updates (the metadata call is no longer the last central call; the faked `ask` takes the new keyword). Full agent suite (`cd agent; .venv\Scripts\python -m pytest tests`, about 8 minutes): **278 passed, 9 skipped** (baseline before the story was 216 passed, 9 skipped).

**Not verified:** a real end-to-end run with real 384-dim embeddings and Bedrock (two agents, a real central). Unit tests use fake 32-dim embeddings against a faked central. See the E2E steps in the plan for S6/S7; the UI toggle and download button are S7.

Known limitations recorded: files beyond 2,000 chunks are only partly shared; teammates are skipped for narrowed scopes, topic-less questions and date ranges; `BedrockUnavailable` still reaches the user as a generic 500 from `/ask` (existing behaviour).

**Postman:** the `Test Ask Teammates` folder (14 requests) is in the HiveMind collection. It runs against a local agent (`AGENT_URL`, startup `token`) and needs an indexed folder and AWS credentials in `agent/.env`. It checks bad bodies, that the response shape is unchanged without `include_teammates`, the skip reasons that can be forced (`local_scope`, `no_topic`, and `date_filter`/`no_topic` for a dated question), the whole-library case (reason is null, `no_team` or `central_unavailable`), and the chat route (live reason present, saved chat keeps source flags but not the reason). Runtime variables `ask_file_id` and `ask_chat_id` only; no collection variables declared or changed. Not run yet. The real teammate-answer case stays a manual end-to-end check.

**Postman run (reported by the story owner, 2026-10-17):** the `Test Ask Teammates` folder passed against a running agent. This confirms the `POST /ask` and chat-route shapes and the forced skip reasons on a real agent. All acceptance criteria are met and the agent suite is green (278 passed); the one thing still unproven is the full path with real 384-dim embeddings, a live central and two agents (publish, teammate answer, delete). That check is part of the E6-S7 end-to-end pass.
