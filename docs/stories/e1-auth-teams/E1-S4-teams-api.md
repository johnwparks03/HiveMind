# E1-S4: Teams API

- **Epic:** E1 Auth and teams
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E1-S1
- **Spec refs:** Feature_List 3.1; Interface B `/teams/*`

## Story
As a user, I want to create a team, invite colleagues and join so that we can share files.

## Acceptance criteria
- [ ] Given I am signed in, when I create a team, then I am its member and `GET /teams/me` returns it.
- [ ] Invites expire after 7 days; joining with an expired or used invite returns an error.
- [ ] Leaving removes my membership; team-scoped endpoints return 403 `no_team` afterwards.
- [ ] `team_id` is always derived server-side from membership.

## Technical notes
- Interface B: `POST /teams` `{name}` -> `201 {team_id,name,created_at}` (409 `already_in_team`); `GET /teams/me` -> `{team:{team_id,name}}` or `{team:null}`; `POST /teams/me/invites` -> `201 {code,expires_at}`; `POST /teams/join` `{code}` -> `200 {team_id,name}` (404 `invalid_code`, 410 `invite_expired`, 409 `already_in_team`); `POST /teams/me/leave` -> `204` (403 `no_team`).
- Tables: `teams(id,name,created_by,created_at)`, `memberships(user_id UNIQUE,team_id,joined_at)`, `invites(code,team_id,created_by,expires_at,use_count,max_uses NULL)`. Invites are multi-use, 7-day lifetime (config); code format like `K7Q2-9XPD`.
- Leave: delete the user's `public_files` rows and `connections` rows; if last member, delete team and its invites. Do it in one transaction.
- This story sets up the Postgres migration tooling (Alembic or plain SQL; record the choice) and creates the teams/memberships/invites tables. E3-S1 adds the rest.
- Write `team_create`, `team_join`, `team_leave` access-log events (see E5-S3).

## Notes
_(add during implementation)_
