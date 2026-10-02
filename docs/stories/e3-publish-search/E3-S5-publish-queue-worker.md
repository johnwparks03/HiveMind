# E3-S5: Publish queue worker

- **Epic:** E3 Publish and central search
- **Track:** Local agent
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E3-S2, E3-S4
- **Spec refs:** Feature_List 1.6; `/files/{id}/publish|unpublish|retry|tags`

## Story
As a user, I want publishing to be reliable so that my intent survives failures and restarts.

## Acceptance criteria
- [ ] Queue is persistent in SQLite; only the latest intent per file is kept; calls are idempotent.
- [ ] Exponential backoff, max 5 concurrent central requests.
- [ ] `publish_state` is pending, published or failed with a reason.
- [ ] Reconciliation against `GET /files/mine` fixes drift.
- [ ] Deleted or moved public files are unpublished.

## Technical notes
- Agent endpoints (API_Contract 2.4): `POST /files/{id}/publish` -> `202 File` (`visibility=public`, `publish_state=pending`; `403 no_team`, `409 file_unavailable` if `missing`); `POST /files/{id}/unpublish` -> `202`; `POST /files/{id}/retry` -> `202`. Publish is immediate, no tag preview.
- Queue worker: ops `publish|unpublish|resync|confirm`; exponential backoff with a retry cap (suggest base 2 s, max ~5 attempts; record); survives restarts; **latest intent per file wins** (publish then unpublish does not replay both); central calls limited to `PUBLISH_CONCURRENCY` (5).
- Publish = tags step (E3-S4) then `PUT /files/{id}`. Unpublish = `DELETE /files/{id}`. Success sets `publish_state=published` and stores `published_at/expires_at/last_confirmed` from the response; permanent failure sets `failed` with `publish_error`.
- Reconciliation: periodically (suggest every few minutes and at startup) call `GET /files/mine`; any file the registry thinks is published but the server lacks becomes private/unpublished (e.g. purged or after leaving a team).
- Public file deleted or moved on disk: queue an unpublish (coordinate with E2-S5).

## Notes
_(add during implementation)_
