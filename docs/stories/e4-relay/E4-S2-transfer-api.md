# E4-S2: Transfer API

- **Epic:** E4 Relay and download
- **Track:** Central service
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E4-S1, E3-S2
- **Spec refs:** Feature_List 3.5; Interface B `/transfers*`

## Story
As a requester, I want to request a teammate's file and get a download link.

## Acceptance criteria
- [ ] `POST /transfers` creates a transfer and sends `upload_request` to the owner's socket; offline owner returns a clear error.
- [ ] `ack`, `complete` and `fail` update state; no ack within 60 seconds fails the transfer.
- [ ] `GET /transfers/{id}` returns a presigned GET URL when ready.
- [ ] Every request writes an access log entry.

## Technical notes
- `POST /transfers` `{file_id}` -> `202 {transfer_id,status:'requested'}`. Checks: file exists and not expired, same team, caller is not owner (`400 own_file`), owner has a live connection (`409 owner_offline`), no team (`403 no_team`), else `404 not_found`. Reuse an in-flight transfer for the same file and requester.
- Create `transfers` row, S3 key = transfer ID (random, no filename), short-lived presigned PUT, send `upload_request` `{action,transfer_id,file_id,upload_url,upload_url_expires_at,ack_deadline_seconds:60}` to the owner's connection.
- `GET /transfers/{id}` (requester only; others get 404) -> `{transfer_id,file_id,status,download_url?,download_url_expires_at?,error_code?}`; issue the presigned GET only when status is `ready`. `error_code`: `owner_unresponsive|file_unavailable|upload_failed`.
- Owner endpoints (owner only): `POST /transfers/{id}/ack` -> 204 (`uploading`), `/complete` `{size_bytes?}` -> 204 (`ready`), `/fail` `{reason: file_not_found|not_public|upload_error}` -> 204 (`failed`).
- No ack within 60 s -> `failed` with `owner_unresponsive` (also enforced by the sweeper). No owner approval step, no size cap. Write `transfer_request` access-log events.

## Notes
_(add during implementation)_
