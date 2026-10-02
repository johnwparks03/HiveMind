# E3-S9: Publish and teammate UI

- **Epic:** E3 Publish and central search
- **Track:** Frontend
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E3-S5, E3-S6, E3-S8
- **Spec refs:** Feature_List 2.2, 2.3

## Story
As a user, I want to publish, tag and share from the UI.

## Acceptance criteria
- [ ] File detail side panel shows tags (editable), publish status, failure reason and 'no tags'.
- [ ] Share folder asks for confirmation; 'make all private' exists; bulk progress is shown.
- [ ] Filters for public/private/failed work.
- [ ] Search page shows teammate results.

## Technical notes
- Files page additions: team panel (create/join/leave, invite code) when no team; per-folder 'X of Y public', **Share current files** (confirm using `share-preview`: 'Share 142 files with your team?'), **Make all private**, remove; bulk progress ('37 of 142 published') from folder counts.
- File list filters all/public/private/failed; row shows tags (editable, calls `PUT /files/{id}/tags`), public/private control, `publish_state`, `publish_error`, 'no tags' flag, Retry button; detail in a **side panel**, not a separate page.
- Search page: 'also search teammates' control sets `include_teammates`; teammate rows show filename, tags, created/modified, expiry, **owner online/offline**; never show owner identity.
- Optional UI hint that tags set before publishing are used as-is (E0-S7 item 8).

## Notes
_(add during implementation)_
