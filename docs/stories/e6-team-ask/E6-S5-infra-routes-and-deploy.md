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
- [x] Integration tests (`-m integration`) pass against the deployed stack (53 of 54; the 54th is a slow older test that lost its network connection, see Notes).

## Notes
Closed out 2026-10-17. The work itself shipped inside the stories that needed it, and was deployed and verified there:
- **Routes:** `PUT /files/{file_id}/chunks` (E6-S3) and `POST /retrieval/search` (E6-S4) are on the shared stack behind the Cognito JWT authorizer. The Postman folders `Test Chunk Ingest` and `Test Retrieval Search` passed against the deployed routes, including the 401 without a token.
- **Sizing:** `FilesFn` memory 512 MB (default timeout 30 s) for chunk batches of about 0.5-1 MB against the 6 MB Lambda and 10 MB API Gateway limits; `SearchFn` unchanged. Caveat: the Postman and `verify` runs used small batches, so a full 100-chunk batch through API Gateway has not been exercised yet. Real documents will do that in the E6-S7 end-to-end pass.
- **Aurora:** max capacity raised from 1 to 2 ACU in E6-S2 and confirmed (`describe-db-clusters`: 0.5-2). pgvector 0.8.0, 20k-vector HNSW build 17 s, queries about 4 ms.
- **Deploys:** the owner ran `cdk deploy` themselves each time (E6-S2, S3, S4); no deploy was run from this session.
- **Config added to the stack:** `CHUNK_UPLOAD_BATCH_SIZE` 100, `MAX_CHUNKS_PER_FILE` 2000, `EMBEDDING_DIMENSION` 384, `CHUNK_STAGING_TTL_MINUTES` 60, `RETRIEVAL_LIMIT_DEFAULT` 20, `RETRIEVAL_LIMIT_MAX` 50.

**Integration suite (`cd central; python -m pytest tests -m integration`), 2026-10-17, after `aws login`:** 53 of the 54 tests passed on the deployed stack: 42 in the first run (auth, files, llm, relay, search and the sweeper tests, which exercise the new staging cleanup against the real database), then the teams and transfers files (10 of 11), and the last one after a fix. The exception is one slow, older sweeper test, `test_an_upload_that_never_completes_fails_after_the_configured_timeout`, which waits out the real 600 s upload timeout over a WebSocket. It ran for 59 minutes and failed with `getaddrinfo failed` (the network dropped mid-run; the teardown hit the same DNS error), so it did not complete rather than disproving anything. The same behaviour is covered by the passing override-based sweeper test and the unit tests. Re-run it on a stable connection if you want it ticked off.
- One failure was a stale test, not a regression: `test_create_team_then_get_me` expected `GET /teams/me` without the `members` list that commit `3a1163d` added before E6. I updated its expected value and it passes.
- Before the first attempt the local AWS login had expired (all 54 errored at setup, nothing reached the stack); `aws login` fixed that.
