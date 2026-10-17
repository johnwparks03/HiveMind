# E6-S5: Infra routes, sizing and deploy

- **Epic:** E6 Ask over teammates' documents
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E6-S3, E6-S4
- **Spec refs:** `infra/stack.py` (routes, Aurora, Lambdas), CLAUDE.md AWS section

## Story
As the team, I want the new endpoints deployed to the shared stack so that agents can use them.

## Acceptance criteria
- [x] Routes for `PUT /files/{id}/chunks` (added in E6-S3) and `POST /retrieval/search` (added in E6-S4) added with the JWT authorizer.
- [x] Lambda memory, timeout and request-size settings fit batch ingest and vector search.
- [x] Aurora capacity adjusted if E6-S2 found it necessary.
- [x] `cdk diff` reviewed and the deploy coordinated with the team before `cdk deploy`.
- [ ] Integration tests (`-m integration`) pass against the deployed stack.

## Notes
Closed out 2026-10-17. The work itself shipped inside the stories that needed it, and was deployed and verified there:
- **Routes:** `PUT /files/{file_id}/chunks` (E6-S3) and `POST /retrieval/search` (E6-S4) are on the shared stack behind the Cognito JWT authorizer. The Postman folders `Test Chunk Ingest` and `Test Retrieval Search` passed against the deployed routes, including the 401 without a token.
- **Sizing:** `FilesFn` memory 512 MB (default timeout 30 s) for chunk batches of about 0.5-1 MB against the 6 MB Lambda and 10 MB API Gateway limits; `SearchFn` unchanged. Caveat: the Postman and `verify` runs used small batches, so a full 100-chunk batch through API Gateway has not been exercised yet. Real documents will do that in the E6-S7 end-to-end pass.
- **Aurora:** max capacity raised from 1 to 2 ACU in E6-S2 and confirmed (`describe-db-clusters`: 0.5-2). pgvector 0.8.0, 20k-vector HNSW build 17 s, queries about 4 ms.
- **Deploys:** the owner ran `cdk deploy` themselves each time (E6-S2, S3, S4); no deploy was run from this session.
- **Config added to the stack:** `CHUNK_UPLOAD_BATCH_SIZE` 100, `MAX_CHUNKS_PER_FILE` 2000, `EMBEDDING_DIMENSION` 384, `CHUNK_STAGING_TTL_MINUTES` 60, `RETRIEVAL_LIMIT_DEFAULT` 20, `RETRIEVAL_LIMIT_MAX` 50.

**Still open: the `-m integration` suite.** Attempted 2026-10-17: all 54 tests errored at setup because the local AWS login had expired (`aws login` required), so nothing reached the stack and nothing was created. The existing integration tests cover the older endpoints (auth, teams, files, search, transfers, sweeper); the new endpoints are covered by the two Postman folders. Run `cd central; python -m pytest tests -m integration` after `aws login` and tick the last box when it passes.
