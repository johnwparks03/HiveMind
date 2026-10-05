# E2-S7: Local search and open file

- **Epic:** E2 Local indexing and search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E2-S4
- **Spec refs:** Feature_List 1.5; `POST /search`, `POST /files/{id}/open`

## Story
As a user, I want to ask 'meeting notes from 3 days ago' and get my matching files — on my own machine, even with no network connection.

## Acceptance criteria
- [ ] A local deterministic parser (`dateparser` + regex) splits the query into topic and date range with no network call; this is the required baseline.
- [ ] If the agent is online and logged in, it also tries the central `/llm/query` (E2-S6) with a short timeout and uses that result instead on success; on failure, timeout, or offline, it keeps the local parse.
- [ ] Local search succeeds and returns results with no network connection at all (verify by disabling networking and running a search).
- [ ] The date filter is applied first, then vector ranking.
- [ ] Results include path, dates and a snippet, plus which parser produced the interpreted query (`"local"` or `"llm"`).
- [ ] `POST /files/{id}/open` opens the file in its default Windows app.
- [ ] `POST /search` never returns `503` due to the LLM proxy being unreachable.

## Technical notes
- `POST /search` `{query, include_teammates?}` -> `{interpreted:{topic,date_from,date_to,source}, local_results:[{file_id,filename,path,file_created_at,file_modified_at,tags,score}], teammate:{searched,skipped_reason,results}}`.
- Flow: run the local parser first. If online, race it against `/llm/query` (local date and IANA timezone) with a short timeout (config value; tune during development) — on success, replace the local parse and set `source: "llm"`; otherwise keep the local parse with `source: "local"`. Then run the Chroma query with date `where` filter first (a file matches if created **or** modified date is in range, and the in-document date counts if present), then rank by similarity. Null dates means no date filter; null topic with dates means list by recency.
- Local parser approach: `dateparser` (or equivalent) resolves relative-date phrases ("3 days ago", "last week", explicit dates) against the agent's local date and timezone; the matched phrase is stripped from the query and the remainder, trimmed, is the topic. No topic left after stripping means list by recency within the date range.
- Group chunks to one result per file (best chunk score). The 'comes up short' similarity threshold is a config value, tuned against real files (record the chosen value).
- `POST /files/{id}/open` -> `204` using `os.startfile`; `404 file_missing` if the path is gone. Teammate part is added in E3-S8; for now return `searched=false`.
- This story does not depend on E2-S6 or E1 auth — a build with no Cognito/central infrastructure deployed yet must still be able to demo local search end to end.

## Notes
_(add during implementation)_
