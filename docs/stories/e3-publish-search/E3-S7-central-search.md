# E3-S7: Central search

- **Epic:** E3 Publish and central search
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E3-S2
- **Spec refs:** Feature_List 3.3; Interface B `POST /search`

## Story
As an agent, I want team-scoped full-text search over public metadata.

## Acceptance criteria
- [x] Results come only from the caller's team, exclude the caller's own files, and cap at ~20.
- [x] Each result includes tags, dates and whether the owner is online.
- [x] Expired files never appear. (Verified by the `expires_at > now()` predicate in offline tests only; the API cannot create an expired row, and the real-Postgres test is skipped until `HIVEMIND_TEST_DATABASE_URL` is set.)

## Technical notes
- `POST /search` request `{topic|null, date_from|null, date_to|null}` -> `{results:[{file_id,filename,tags,file_created_at,file_modified_at,expires_at,owner_online}]}`. No LLM call here.
- Filters: caller's team, exclude caller's own files, `expires_at > now()`. Date match: created **or** modified in range. `owner_online` = a row exists in `connections` for the owner.
- Topic: `websearch_to_tsquery` or OR-ing terms against the generated tsvector (looser than all-words). Topic null: all files in range newest first. Dates null: topic-only over all non-expired team files. Order by `ts_rank` then recency, cap `SEARCH_RESULT_CAP`. `403 no_team` without a team.
- Do not return owner identity. Write a `search` access-log event with topic, dates, count and matched file_ids (no filenames).

## Notes
**Status:** done. `SearchFn` deployed; 134 offline tests pass and all 10 integration tests in `test_search_integration.py` pass against the deployed stack (first real-Postgres run of `search_vector`: stemming, any-word matching, created-or-modified dates, ordering and team scoping all behaved as designed). Postman folder not yet run by the user.

- **Code:** `central/lambdas/search.py` (route `POST /search`, `SearchFn` in `infra/stack.py`; shared DB role, VPC). `invalid_request` and `optional_timestamp` moved from `files.py` into `common/http.py` so both Lambdas share them.
- **Topic matching:** the topic is reduced to its words (`[A-Za-z0-9]+`, the same splitting the filename vector uses), joined with ` or ` and passed to `websearch_to_tsquery('english', ...)`. That gives any-word matching, English stemming ("contract" finds "Contracts"), and no syntax-error or injection surface. A topic with no usable words (e.g. `???`) returns an empty list, not an error. A blank topic is treated as null. Topic is capped at 500 characters.
- **Dates:** a file matches if created **or** modified is inside the range; either bound may be null. A bounded range never matches a file with no dates; with both bounds null, undated files are returned. Dates must carry a timezone, and `date_from > date_to` is a 400 naming both fields.
- **Ordering:** topic given gives `ts_rank` first, then recency; no topic gives recency only. Recency is `coalesce(file_modified_at, file_created_at, published_at)`, so an undated file sorts by when it was published. Capped at `SEARCH_RESULT_CAP` (env, default 20).
- **Access log (diverges from the contract table):** `API_Contract.md` section 5 lists `topic`, `date_from`, `date_to`, `count` and `matched_file_ids`, but CLAUDE.md says never to log queries and the table only stores ids. Decision: one `search` row per matched `file_id`, or one row with no `file_id` when nothing matched. No topic, dates or filenames are stored. Reconcile the contract in E5-S3.
- **Expiry:** the API cannot create an expired row, so "expired files never appear" is covered by an offline SQL-predicate test and by `test_search_sql_against_real_postgres` in `test_search.py`, which runs the real query against a scratch schema. That test is skipped unless `HIVEMIND_TEST_DATABASE_URL` is set (no Postgres on the dev machine), so it has not been run yet.
- **`owner_online`:** reads the `connections` table; nothing writes it until the WebSocket story (E4), so it is always `false` for now.
- **Postman:** folder "Test Search" (30 requests) in the HiveMind collection. It covers no-team, team setup, topic/stem/any-word/tag matching, created and modified date ranges, newest-first ordering, own-file exclusion, 400s, 401, and cleanup.
