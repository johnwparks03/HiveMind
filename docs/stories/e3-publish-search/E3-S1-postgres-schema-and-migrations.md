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
- [x] Migrations create teams, memberships, invites, public_files, connections, transfers and access_log.
- [x] public_files has a tsvector column with a GIN index.
- [x] Migrations run from CI/CLI against a fresh database.

## Technical notes
- Postgres migrations using the tooling set up in E1-S4. `public_files`: `file_id` text PK, `owner_id`, `team_id`, `filename`, `tags text[]`, `file_created_at`, `file_modified_at`, `published_at`, `expires_at`, `last_confirmed`, plus a generated `tsvector` over normalized filename (underscores, dots, hyphens to spaces) and tags with a GIN index.
- `connections(connection_id, user_id, connected_at)`; `transfers(transfer_id, file_id, requester_id, owner_id, status, s3_key, created_at, updated_at)` with statuses `requested|uploading|ready|failed|expired`; `access_log(log_id, timestamp, user_id, event_type, details jsonb)`.
- DB roles: the Lambda role has `INSERT` only on `access_log`. Teams/memberships/invites tables are created in E1-S4.

## Notes
- **Status:** done. Deployed to the dev stack: the `RunMigrations` trigger applied `0002` on Aurora Postgres 16.8, and a manual `MigrateFn` invoke afterwards returned `{"applied": []}` (idempotent). Not verified on a real DB: search matching and the transfers status CHECK (the two skipped tests in `test_migrations.py`); E3-S7 will exercise search.
- **Migration:** `0002_publish_relay.sql` adds `public_files`, `connections`, `transfers`. `teams`/`memberships`/`invites` stay in `0001`.
- **tsvector:** `public_files.search_vector` is a generated stored column (`'english'`, filename with `[-_.]+` turned into spaces, plus tags) with a GIN index. `array_to_string` is only STABLE and generated columns require IMMUTABLE, so the migration defines `hm_tags_text(text[])` as an IMMUTABLE wrapper. **verify:** confirm this migration applies on Aurora Postgres 16.8.
- **Types:** `public_files.team_id` is `uuid` with an FK to `teams(id) ON DELETE CASCADE` (the blueprint says `text`; `teams.id` is uuid). `transfers.file_id` has no FK so a purge mid-transfer keeps the row.
- **access_log deviation:** kept the E1-S4 shape (`id, ts, event, user_id, team_id, file_id`) instead of `log_id, timestamp, event_type, details jsonb`; it is ids-only per CLAUDE.md and `teams.py` already uses it. E5-S3 owns gaps.
- **Known gap, INSERT-only role:** all Lambdas connect with the single Aurora master credential, so a table-level grant on `access_log` would not restrict anything. Needs a second DB user and secret in CDK; left for E5-S3/hardening.
- **CLI/CI:** `python central/lambdas/migrate.py --dsn <url>` (or `HIVEMIND_DATABASE_URL`) applies migrations to any Postgres; the Lambda handler shares `apply_migrations`.
- **leave_team:** now deletes the leaver's `public_files` and `connections` rows in the same transaction (E1-S4 handoff). The `transfers` rows are not touched.
- **Tests:** `central/tests/test_migrations.py`. Two tests (fresh-DB apply + idempotence; search matching and status CHECK) run only when `HIVEMIND_TEST_DATABASE_URL` points at a Postgres; they are skipped locally.
