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
Implemented; boxes stay unticked until checked against the deployed E1-S4 stack (unit tests fake central).
- `app/api/routes_team.py` proxies via `app/central/teams.py`; central error envelopes are re-raised one to one (code, status, message, details). An unparseable central reply becomes 503 `service_unavailable`.
- `POST /team` returns `{team_id, name}`; `created_at` from central is dropped (the contract's Interface A shape has no `created_at`).
- Leave: local publish state is reset only after central returns 204 (`public_state='private'`, publish/expiry columns cleared, tags kept). Cancelling queued publishes is deferred to E3, which owns the queue (hook: `clear_local_publish_state`).
- `GET /session` now fills `team` from central, only when signed in and central is reachable, cached `TEAM_CACHE_SECONDS` (5) and cleared on create/join/leave/login/logout. A failed lookup yields `null`, never an error.
- Local search never calls central, so a user without a team keeps working; `no_team` only comes from team-scoped central calls.
