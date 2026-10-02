# E2-S7: Local search and open file

- **Epic:** E2 Local indexing and search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E2-S4, E2-S6
- **Spec refs:** Feature_List 1.5; `POST /search`, `POST /files/{id}/open`

## Story
As a user, I want to ask 'meeting notes from 3 days ago' and get my matching files.

## Acceptance criteria
- [ ] The date filter is applied first, then vector ranking.
- [ ] Results include path, dates and a snippet.
- [ ] `POST /files/{id}/open` opens the file in its default Windows app.
- [ ] If the LLM proxy is down, the UI shows 'service unavailable' with no fallback.

## Technical notes
- `POST /search` `{query, include_teammates?}` -> `{interpreted:{topic,date_from,date_to}, local_results:[{file_id,filename,path,file_created_at,file_modified_at,tags,score}], teammate:{searched,skipped_reason,results}}`.
- Flow: call `/llm/query` with local date and IANA timezone; Chroma query with date `where` filter first (a file matches if created **or** modified date is in range, and the in-document date counts if present), then rank by similarity. Null dates means no date filter; null topic with dates means list by recency.
- Group chunks to one result per file (best chunk score). The 'comes up short' similarity threshold is a config value, tuned against real files (record the chosen value).
- `POST /files/{id}/open` -> `204` using `os.startfile`; `404 file_missing` if the path is gone. Teammate part is added in E3-S8; for now return `searched=false`.

## Notes
_(add during implementation)_
