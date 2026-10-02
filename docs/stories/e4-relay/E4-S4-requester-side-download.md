# E4-S4: Requester side download

- **Epic:** E4 Relay and download
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E4-S2
- **Spec refs:** Feature_List 1.8; `/transfers*` on Interface A

## Story
As a requester, I want the file saved to my Downloads folder.

## Acceptance criteria
- [ ] `POST /transfers` is protected against duplicate clicks.
- [ ] The agent polls every 1-2 seconds until ready, then downloads; name collisions get a suffix.
- [ ] `GET /transfers` lists recent transfers.

## Technical notes
- Agent endpoints: `POST /transfers` `{file_id}` -> `202 Transfer` (errors `409 owner_offline`, `404 not_found`, `400 own_file`); `GET /transfers/{id}` -> Transfer; `GET /transfers` -> this session's transfers.
- Transfer object: `{transfer_id,file_id,filename,status: requested|uploading|ready|downloading|downloaded|failed|expired, saved_path, error_code: owner_offline|upload_timeout|file_unavailable|download_failed}`.
- Agent polls central `GET /transfers/{id}` every 1-2 s; on `ready` downloads from the presigned GET (stream to disk) into the Windows Downloads folder (use the known-folder API, not a hardcoded path). On name collision add ` (1)`, ` (2)` suffix.
- A duplicate `POST /transfers` for an in-flight transfer returns the existing one.
- `POST /transfers/{id}/open` is only implemented if E0-S7 keeps it.

## Notes
_(add during implementation)_
