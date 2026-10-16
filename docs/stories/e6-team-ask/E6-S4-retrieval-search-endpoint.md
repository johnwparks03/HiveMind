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
- [ ] `POST /retrieval/search` takes `{query_embedding, file_ids?, limit?}`; the server derives `team_id` from membership.
- [ ] Excludes the caller's own files and expired rows; only files with indexed chunks are searched.
- [ ] Returns `{file_id, filename, chunk_index, text, distance}` ordered by cosine distance; no owner identity.
- [ ] Limit has a configured default and cap.
- [ ] Query text never reaches central (vector only). Vectors and chunk text are never logged.
- [ ] Access log records a retrieval event with ids only (new `event_type` in the contract).
- [ ] Unit tests: team isolation, own-file exclusion, expiry, limit cap, dimension validation.

## Notes
_(add during implementation)_
