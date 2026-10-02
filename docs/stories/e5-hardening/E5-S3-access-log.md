# E5-S3: Access log

- **Epic:** E5 Retention and hardening
- **Track:** Central service
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** E3-S7, E4-S2
- **Spec refs:** Feature_List 3.7

## Story
As an admin, I want an audit trail of searches, publishes and transfers.

## Acceptance criteria
- [ ] Search, publish, team and transfer endpoints write access_log rows.
- [ ] Rows do not store file content.

## Technical notes
- Event types: `search` (topic, date_from, date_to, count, matched_file_ids), `publish` (file_id, first publish only), `unpublish`, `confirm`, `transfer_request` (file_id, transfer_id, outcome), `team_create`/`team_join`/`team_leave` (team_id).
- Never store filenames, file content, queries or excerpts. `/llm/*` calls are not content-logged. Lambda DB role has INSERT only. No admin screen; viewed by direct query.
- Implemented as a shared helper called from the endpoints in E1-S4, E3-S2, E3-S7 and E4-S2; this story adds the helper's tests and fills any gaps.

## Notes
_(add during implementation)_
