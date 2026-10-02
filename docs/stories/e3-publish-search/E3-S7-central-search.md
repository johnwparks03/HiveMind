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
- [ ] Results come only from the caller's team, exclude the caller's own files, and cap at ~20.
- [ ] Each result includes tags, dates and whether the owner is online.
- [ ] Expired files never appear.

## Technical notes
- `POST /search` request `{topic|null, date_from|null, date_to|null}` -> `{results:[{file_id,filename,tags,file_created_at,file_modified_at,expires_at,owner_online}]}`. No LLM call here.
- Filters: caller's team, exclude caller's own files, `expires_at > now()`. Date match: created **or** modified in range. `owner_online` = a row exists in `connections` for the owner.
- Topic: `websearch_to_tsquery` or OR-ing terms against the generated tsvector (looser than all-words). Topic null: all files in range newest first. Dates null: topic-only over all non-expired team files. Order by `ts_rank` then recency, cap `SEARCH_RESULT_CAP`. `403 no_team` without a team.
- Do not return owner identity. Write a `search` access-log event with topic, dates, count and matched file_ids (no filenames).

## Notes
_(add during implementation)_
