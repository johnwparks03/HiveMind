# E1-S5: Agent team endpoints

- **Epic:** E1 Auth and teams
- **Track:** Local agent
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** E1-S3, E1-S4
- **Spec refs:** Feature_List 1.10; Interface A `/team*`

## Story
As a user, I want the agent to expose team actions so that the UI can manage my team.

## Acceptance criteria
- [ ] `GET/POST /team`, `/team/invites`, `/team/join`, `/team/leave` proxy to central and map errors correctly.
- [ ] A user without a team gets 403 `no_team` for team-scoped calls but can still use local search.

## Technical notes
- Interface A: `GET /team` -> `{team:{team_id,name}}|{team:null}`; `POST /team` `{name}` -> `201`; `POST /team/invites` -> `201 {code,expires_at}`; `POST /team/join` `{code}` -> `200`; `POST /team/leave` -> `204`.
- Map central errors one to one (e.g. 409 `already_in_team`, 410 `invite_expired`). Leave also clears local publish state for the user's files and cancels queued publishes.

## Notes
_(add during implementation)_
