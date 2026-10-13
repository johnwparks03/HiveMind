# E3-S2: Metadata API

- **Epic:** E3 Publish and central search
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E3-S1, E1-S4
- **Spec refs:** Feature_List 3.2; Interface B `/files/*`

## Story
As an agent, I want to publish and remove file metadata centrally.

## Acceptance criteria
- [x] `PUT /files/{id}` is idempotent (upsert) and server-sets `expires_at` (45 days).
- [x] `DELETE /files/{id}` removes it; `GET /files/mine` lists my published files.
- [x] A user can only modify their own files; no team returns 403 `no_team`.

## Technical notes
- `PUT /files/{file_id}` request `{filename, tags, file_created_at, file_modified_at}` -> `200 {file_id, published_at, expires_at, last_confirmed}`. `owner_id` from token, `team_id` from membership.
- Idempotent upsert. **On an existing row preserve `published_at`, `expires_at`, `last_confirmed`**; only `confirm` extends expiry. Another user's row -> `403 forbidden`. No team -> `403 no_team`.
- `DELETE /files/{file_id}` -> `204`, also `204` if missing; other user's -> `403 forbidden`.
- `GET /files/mine?limit=&cursor=` -> `{files:[{file_id,filename,published_at,expires_at,last_confirmed}], next_cursor}` (pagination per E0-S7).
- `POST /files/{file_id}/confirm` -> `200 {expires_at,last_confirmed}` sets expires_at = now + 45 days; `404` if purged. (Endpoint built here; used by E5-S2.)
- Write `publish` (first publish only) and `unpublish` access-log events.

## Notes
- **Status:** done. `FilesFn` deployed to the dev stack; offline tests (72) and the 8 integration tests in `test_files_integration.py` pass against it, including the `xmax = 0` first-publish check on Aurora. The Postman folder "Test Metadata API" was created but not run by the implementer.
- **Code:** `central/lambdas/files.py` (one Lambda, four routes, same shape as `teams.py`); shared `parse_body`/`json_response`/`get_membership`/`iso` moved to `central/lambdas/common/http.py`; `FilesFn` and routes added in `infra/stack.py`.
- **Upsert:** a single `INSERT ... ON CONFLICT (file_id) DO UPDATE ... WHERE owner_id = EXCLUDED.owner_id RETURNING ..., (xmax = 0)`. No returned row means another owner holds the id (`403 forbidden`). `xmax = 0` marks a first publish, so only that writes the `publish` access-log event. Re-PUT never touches `published_at`/`expires_at`/`last_confirmed`. **verify-in-AWS:** confirm the `xmax` trick behaves on Aurora Postgres 16.8 (integration test `test_publish_is_idempotent_and_preserves_expiry`).
- **`no_team` scope:** enforced on `PUT` only, as in the contract. A user with no team has no rows (leaving a team deletes them), so `DELETE` returns 204, `confirm` 404 and `GET /files/mine` an empty list.
- **Confirm and expiry:** `confirm` only matches rows with `expires_at > now()`; an expired, not-yet-purged row returns 404. `PUT` on such a row preserves the old expiry per the contract, so it stays hidden until the purge removes it.
- **Pagination (E0-S7 open item 4):** implemented with a keyset cursor on `file_id` (base64url of the last id), default limit 100, max 500; bad `limit`/`cursor` is `400 invalid_request` with `details.fields`. E0-S7 should record this decision.
- **Access log:** also writes `confirm` (listed in the contract and blueprint, not in this story).
- **Validation:** `file_id` must be a UUID; `filename` 1-255 chars; `tags` up to 50 strings of 1-100 chars; timestamps ISO 8601 with a timezone or null. Failures return `details.fields` (names only, never values).
- **Tags** are only stored here; generation is E3-S3 (`/llm/tags`) and the agent pipeline (E3-S4/S5).
- **Postman:** folder "Test Metadata API" in the HiveMind collection (31 requests) calls central directly with a Cognito access token (Bearer), unlike the agent-based folders. It needs `AWS_URL`, `cognito_client_id`, `user_a_email`, `user_b_email` and `user_password` set.
