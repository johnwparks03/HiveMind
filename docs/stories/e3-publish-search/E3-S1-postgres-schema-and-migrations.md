# E3-S1: Postgres schema and migrations

- **Epic:** E3 Publish and central search
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E0-S2, E1-S4
- **Spec refs:** Blueprint (tables); Feature_List 3.2

## Story
As a developer, I want the central schema so that APIs can persist data.

## Acceptance criteria
- [ ] Migrations create teams, memberships, invites, public_files, connections, transfers and access_log.
- [ ] public_files has a tsvector column with a GIN index.
- [ ] Migrations run from CI/CLI against a fresh database.

## Technical notes
- Postgres migrations using the tooling set up in E1-S4. `public_files`: `file_id` text PK, `owner_id`, `team_id`, `filename`, `tags text[]`, `file_created_at`, `file_modified_at`, `published_at`, `expires_at`, `last_confirmed`, plus a generated `tsvector` over normalized filename (underscores, dots, hyphens to spaces) and tags with a GIN index.
- `connections(connection_id, user_id, connected_at)`; `transfers(transfer_id, file_id, requester_id, owner_id, status, s3_key, created_at, updated_at)` with statuses `requested|uploading|ready|failed|expired`; `access_log(log_id, timestamp, user_id, event_type, details jsonb)`.
- DB roles: the Lambda role has `INSERT` only on `access_log`. Teams/memberships/invites tables are created in E1-S4.

## Notes
_(add during implementation)_
