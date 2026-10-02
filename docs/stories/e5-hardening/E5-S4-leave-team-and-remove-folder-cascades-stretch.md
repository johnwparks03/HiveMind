# E5-S4: Leave-team and remove-folder cascades

- **Epic:** E5 Retention and hardening
- **Track:** Local agent + Central service
- **Estimate:** M
- **Priority:** Stretch (drop first if behind)
- **Depends on:** E3-S5, E1-S4
- **Spec refs:** Feature_List 1.6, 1.10

## Story
As a user, I want leaving a team or removing a folder to clean up what I shared.

## Acceptance criteria
- [ ] Leaving a team removes my public files centrally.
- [ ] Removing a folder queues unpublish for its public files.

## Technical notes
- Leave team: central deletes the user's `public_files` and `connections` rows (E1-S4); agent must then clear publish state for all its files and cancel queued publishes so they don't produce 403 `no_team` retries.
- Remove folder: `DELETE /folders/{id}` returns `202 {queued_unpublish:n}`; the unpublish queue rows must survive folder deletion.
- There is no push notification when a user is removed from a team; reconciliation (`GET /files/mine`) covers drift.

## Notes
_(add during implementation)_
