# E2-S5: Change detection

- **Epic:** E2 Local indexing and search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E2-S2, E2-S4
- **Spec refs:** Feature_List 1.2

## Story
As a user, I want edits, moves and deletes picked up automatically so that results stay current.

## Acceptance criteria
- [ ] watchdog events are debounced into a work queue; unchanged content (same hash) is skipped.
- [ ] Deleted or moved files have their chunks removed or re-pointed.
- [ ] A file added while the agent was off is found on next start.

## Technical notes
- watchdog observer per watched folder; debounce bursts of events (e.g. 1-2 s; record the value). Compare SHA-256 content hash before re-indexing.
- Moves: update `path` on the existing `file_id` (match by hash) rather than re-embedding. Deletes: mark `missing`, remove chunks; if public, queue an unpublish.
- On public file content change: queue a metadata `resync` (modified date), do **not** regenerate tags.
- On startup, run a reconcile scan so changes made while the agent was off are found.

## Notes
_(add during implementation)_
