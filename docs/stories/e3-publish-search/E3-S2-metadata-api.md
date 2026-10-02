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
- [ ] `PUT /files/{id}` is idempotent (upsert) and server-sets `expires_at` (45 days).
- [ ] `DELETE /files/{id}` removes it; `GET /files/mine` lists my published files.
- [ ] A user can only modify their own files; no team returns 403 `no_team`.

## Technical notes
- `PUT /files/{file_id}` request `{filename, tags, file_created_at, file_modified_at}` -> `200 {file_id, published_at, expires_at, last_confirmed}`. `owner_id` from token, `team_id` from membership.
- Idempotent upsert. **On an existing row preserve `published_at`, `expires_at`, `last_confirmed`**; only `confirm` extends expiry. Another user's row -> `403 forbidden`. No team -> `403 no_team`.
- `DELETE /files/{file_id}` -> `204`, also `204` if missing; other user's -> `403 forbidden`.
- `GET /files/mine?limit=&cursor=` -> `{files:[{file_id,filename,published_at,expires_at,last_confirmed}], next_cursor}` (pagination per E0-S7).
- `POST /files/{file_id}/confirm` -> `200 {expires_at,last_confirmed}` sets expires_at = now + 45 days; `404` if purged. (Endpoint built here; used by E5-S2.)
- Write `publish` (first publish only) and `unpublish` access-log events.

## Notes
_(add during implementation)_
