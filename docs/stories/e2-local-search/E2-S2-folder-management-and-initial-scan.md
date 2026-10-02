# E2-S2: Folder management and initial scan

- **Epic:** E2 Local indexing and search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E2-S1, E0-S4
- **Spec refs:** Feature_List 1.1; `/folders*`

## Story
As a user, I want to add folders to watch so that my files become searchable.

## Acceptance criteria
- [ ] `POST /folders` adds a recursive watched folder and starts an initial scan; `GET /folders` shows progress.
- [ ] `GET /files` and `GET /files/{id}` return the File object from the contract.
- [ ] `DELETE /folders/{id}` removes the folder and its index entries.
- [ ] Only PDF, DOCX, PPTX and TXT files are registered.

## Technical notes
- `GET /folders` -> `{folders:[{folder_id,path,scan_state,counts:{total,indexed,pending,failed,public},shared}]}`.
- This story also owns the read endpoints `GET /files` (query `folder_id`, `status=all|public|private|failed|expiring_soon`, `limit` default 100, `cursor`; returns `{files:[File],next_cursor}`) and `GET /files/{id}`, using the File object in API_Contract 2.4.
- `POST /folders` `{path}` -> `201 Folder` and starts the scan in the background; errors `404 path_not_found`, `409 already_watched`.
- `DELETE /folders/{id}` -> `202 {queued_unpublish:n}`: stop watching, remove chunks and file rows, queue an unpublish for every public file (entries must survive folder deletion; coordinate with E5-S4).
- Use the folder-picker approach recorded in E0-S4 for `POST /folders/pick`. Scan is recursive; only PDF/DOCX/PPTX/TXT are registered.

## Notes
_(add during implementation)_
