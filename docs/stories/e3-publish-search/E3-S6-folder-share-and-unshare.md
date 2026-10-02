# E3-S6: Folder share and unshare

- **Epic:** E3 Publish and central search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E3-S5
- **Spec refs:** Feature_List 1.6; `/folders/{id}/share-preview|share|unshare`

## Story
As a user, I want to share a whole folder so that I don't publish files one by one.

## Acceptance criteria
- [ ] `share-preview` returns counts without publishing.
- [ ] `share` queues every eligible file; `unshare` queues unpublish for all.
- [ ] Progress is visible through `GET /folders`.

## Technical notes
- `GET /folders/{id}/share-preview` -> `{file_count}` (private files currently under the folder, including subfolders, not already public).
- `POST /folders/{id}/share` -> `202 {queued}`: **one-time snapshot**; later-added files stay private. `403 no_team` if no team. `POST /folders/{id}/unshare` -> `202 {queued}`: queues unpublish for every public file under it.
- Files with no tags still publish and are flagged `no_tags`.

## Notes
_(add during implementation)_
