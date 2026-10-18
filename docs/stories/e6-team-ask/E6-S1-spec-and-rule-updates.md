# E6-S1: Spec and rule updates for the central chunk index

- **Epic:** E6 Ask over teammates' documents
- **Track:** All tracks
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** -
- **Spec refs:** Technical_Blueprint (lines on embeddings/content staying local, central search, "possible later feature"), Feature_List 1.5 / Ask scope, API_Contract sections 1-3 and 7, CLAUDE.md architecture rules and Known limitations

## Story
As a developer, I want the docs to describe the central chunk index so that the code and the rules agree before we build it.

## Decision recorded
Ask will answer from teammates' public documents by storing chunk text and 384-dim embeddings centrally (Aurora Postgres + pgvector), not by relaying questions to owner agents. Reason: it works when the owner is offline, is fast and consistently ranked, and avoids per-question fan-out to laptops. Cost: new ingest and sync pipeline, content at rest in AWS. This deliberately overrides the earlier rule that content and embeddings never go central.

## Acceptance criteria
- [x] `API_Contract.md` documents `PUT /files/{id}/chunks` and `POST /retrieval/search` (request/response, errors, idempotency). It wins on any conflict with the other docs.
- [x] `Technical_Blueprint.md` and `Feature_List.md` no longer say embeddings or content are never central or that Ask is local-only.
- [x] `CLAUDE.md` architecture rules and Known limitations are updated (central search is no longer metadata-only for Ask; chunk text is stored centrally and purged with the file).
- [x] Consent wording decided: publishing a file now means its content chunks are readable by teammates (UI copy updated in E6-S7).
- [x] Bedrock path decided (default: stays agent-direct for the demo) and recorded in Notes.

## Technical notes
- Chunks are purged by FK cascade when a file is unpublished, deleted or expires (45 days).
- Never log request bodies, chunk text, query vectors or tokens.

## Notes
Decisions recorded (2026-10-16):
1. **Consent:** publishing a file means its content chunks are readable by teammates. No separate setting for the demo; UI copy says so (E6-S7).
2. **Bedrock path:** Ask stays agent-direct (the 2026-10-15 demo/MVP exception). Teammate chunks reach the requester's laptop and its `agent/.env` credentials; listed as a known limitation in CLAUDE.md and Feature_List.
3. **Embeddings:** still computed locally; only the "never leave the machine" claim changes. The in-document date stays local and is not uploaded.
4. **Names:** reuse existing error codes (`403 no_team`, `403 forbidden`, `404 not_found`, `400 invalid_request` with `details.fields`, `503 service_unavailable`), no new codes. Access-log events `chunks_put` and `retrieval_search`. Config: `CHUNK_UPLOAD_BATCH_SIZE`, `RETRIEVAL_LIMIT_DEFAULT`, `RETRIEVAL_LIMIT_MAX`, `MAX_CHUNKS_PER_FILE`, `EMBEDDING_DIMENSION`. Platform payload limits (API Gateway 10 MB, Lambda sync 6 MB) are external facts, not in the repo.

Status: all four doc updates landed (API_Contract, Technical_Blueprint, Feature_List, CLAUDE.md).
