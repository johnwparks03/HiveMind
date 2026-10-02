# E2-S8: Search and Files pages (local)

- **Epic:** E2 Local indexing and search
- **Track:** Frontend
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E1-S6, E2-S2, E2-S7
- **Spec refs:** Feature_List 2.2, 2.3, 2.5

## Story
As a user, I want to search and manage watched folders in the UI.

## Acceptance criteria
- [ ] Search page shows local results with an Open action.
- [ ] Files page can add a folder, shows indexing progress and 'X of Y indexed', and lists files with all/failed filters.
- [ ] Polling is slow when idle and faster during indexing.

## Technical notes
- Search page: query box, states (searching, no results, service unavailable); local result row shows filename, dates, tags, **Open** (calls `POST /files/{id}/open`).
- Files page (local part): Add folder via `POST /folders/pick` then `POST /folders`; per-folder indexing progress from `counts`; file list from `GET /files?status=&folder_id=` with filters all/failed for now (public/private/expiring added in E3-S9/E5-S2); show `failure_reason`.
- Polling: ~1-2 s while any folder is `scanning` or files `pending`, ~10-15 s when idle (TanStack Query `refetchInterval`).
- `GET /files` is implemented in E2-S2.

## Notes
_(add during implementation)_
