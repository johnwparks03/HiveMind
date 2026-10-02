# E5-S1: Nightly purge and 45-day retention

- **Epic:** E5 Retention and hardening
- **Track:** Central service
- **Estimate:** S
- **Priority:** Stretch (drop first if behind)
- **Depends on:** E3-S2
- **Spec refs:** Feature_List 3.6

## Story
As an admin, I want old public metadata removed automatically.

## Acceptance criteria
- [ ] A nightly job deletes files past `expires_at`.
- [ ] Only a re-confirm extends expiry.

## Technical notes
- EventBridge nightly -> Lambda: delete `public_files` rows past `expires_at`, expired `invites`, stale `connections` rows. Search already excludes expired rows, so this is cleanup.
- Retention is 45 days from publish or from the latest confirm (config).

## Notes
_(add during implementation)_
