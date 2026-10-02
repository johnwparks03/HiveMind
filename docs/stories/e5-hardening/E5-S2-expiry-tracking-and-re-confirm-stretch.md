# E5-S2: Expiry tracking and re-confirm

- **Epic:** E5 Retention and hardening
- **Track:** Local agent + Frontend
- **Estimate:** M
- **Priority:** Stretch (drop first if behind)
- **Depends on:** E5-S1
- **Spec refs:** Feature_List 1.7; `POST /files/{id}/confirm`

## Story
As a user, I want to keep a file public beyond 45 days by confirming.

## Acceptance criteria
- [ ] Files within 7 days of expiry show 'expiring soon' and filter correctly.
- [ ] Re-confirm resets expiry and `last_confirmed`.

## Technical notes
- Agent: `POST /files/{id}/confirm` -> `202 File`, queues a `confirm` op that calls central `POST /files/{id}/confirm`; on success update `expires_at`/`last_confirmed`. If central returns 404 (purged), mark the file no longer published.
- `expiring_soon` = `expires_at` within 7 days (`EXPIRING_SOON_DAYS`); `GET /files?status=expiring_soon` filters on it.
- UI: 'expiring soon' filter and a **Re-confirm** button on those rows (and in the side panel).

## Notes
_(add during implementation)_
