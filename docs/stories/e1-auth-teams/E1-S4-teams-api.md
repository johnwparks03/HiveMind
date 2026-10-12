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
Implemented; acceptance boxes stay unticked until `pytest -m integration` passes against the deployed stack (unit tests use a scripted fake cursor, so the SQL itself is only exercised there).
- **Migrations:** plain SQL, no Alembic. `central/lambdas/migrations/NNNN_*.sql` is applied once each, in order, by `migrate.py` (tracked in `schema_migrations`, guarded by an advisory lock). The DB is only reachable inside the VPC, so a CDK `Trigger` runs `MigrateFn` on each deploy where its code changed; run it by hand with `aws lambda invoke` after adding a migration. E3-S1 adds its tables as `0002_*.sql`.
- **Infra:** one `TeamsFn` behind the five routes (dispatches on `routeKey`). Lambdas have no NAT, so a Secrets Manager interface VPC endpoint was added (small hourly cost) to fetch DB credentials. `psycopg2-binary` ships as a layer built by `infra/build_layer.py` (Linux wheels, no Docker): run it before `cdk diff/deploy`.
- **Access log:** the S4 migration creates a minimal `access_log` (`event, user_id, team_id, file_id`) and `common/access_log.log_event`; `team_create/join/leave` use it. E5-S3 adds tests and fills gaps.
- **Leave:** deletes the membership; if last member, deletes invites and the team (team row locked first). It does **not** yet delete `public_files`/`connections` rows because those tables don't exist; E3-S1 and E4 must extend `leave_team` in `teams.py`.
- **Join:** code is trimmed and uppercased. A used-up invite (`use_count >= max_uses`) returns 410 `invite_expired`; max_uses is NULL (multi-use) today. A malformed code returns 404 `invalid_code`. Concurrent joins/creates fall back to the `memberships.user_id` UNIQUE constraint (409 `already_in_team`).
- **Contract:** `invalid_code` and `invite_expired` added to API_Contract section 1.
- The optional expired-invite integration check needs `HIVEMIND_TEST_DB_DSN` (DB isn't reachable from a laptop); without it that assertion is skipped.
- **verify-in-AWS:** deploy, confirm the migration Trigger runs and the Secrets Manager endpoint lets `TeamsFn` connect to Aurora.
