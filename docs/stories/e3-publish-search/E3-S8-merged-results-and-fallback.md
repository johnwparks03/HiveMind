# E3-S8: Merged results and fallback

- **Epic:** E3 Publish and central search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E3-S7, E2-S7
- **Spec refs:** Feature_List 1.5

## Story
As a user, I want teammate results when my own files fall short.

## Acceptance criteria
- [ ] When local results fall below the threshold (or `include_teammates` is true), central search is called and merged.
- [ ] Teammate results hide the owner's identity.
- [ ] Central failure shows 'service unavailable' and local results remain.

## Technical notes
- Extend `POST /search` (E2-S7). Call central `/search` with the already-resolved `topic/date_from/date_to` when no local result clears the threshold **or** `include_teammates` is true and the user has a team.
- Response `teammate`: `{searched, skipped_reason: 'local_sufficient'|'no_team'|null, results}`.
- If `/llm/query` fails -> `503 service_unavailable` for the whole search (no degraded fallback). If only central search fails after local succeeded, return local results with `teammate.searched=false` and an indication of failure (record the shape you choose in the contract).

## Notes
_(add during implementation)_
