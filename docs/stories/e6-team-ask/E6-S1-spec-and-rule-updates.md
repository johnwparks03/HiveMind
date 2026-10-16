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
- [ ] `API_Contract.md` documents `PUT /files/{id}/chunks` and `POST /retrieval/search` (request/response, errors, idempotency). It wins on any conflict with the other docs.
- [ ] `Technical_Blueprint.md` and `Feature_List.md` no longer say embeddings or content are never central or that Ask is local-only.
- [ ] `CLAUDE.md` architecture rules and Known limitations are updated (central search is no longer metadata-only for Ask; chunk text is stored centrally and purged with the file).
- [ ] Consent wording decided: publishing a file now means its content chunks are readable by teammates (UI copy updated in E6-S7).
- [ ] Bedrock path decided (default: stays agent-direct for the demo) and recorded in Notes.

## Technical notes
- Chunks are purged by FK cascade when a file is unpublished, deleted or expires (45 days).
- Never log request bodies, chunk text, query vectors or tokens.

## Notes
_(add during implementation)_
