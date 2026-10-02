# E4-S5: Sweeper Lambda

- **Epic:** E4 Relay and download
- **Track:** Central service
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** E4-S2
- **Spec refs:** Feature_List 3.6
- **Flags:** verify-in-AWS

## Story
As an admin, I want transit files deleted quickly so files are never held long.

## Acceptance criteria
- [ ] A scheduled job (every minute) deletes S3 objects older than 15 minutes and marks transfers expired.
- [ ] Idempotent on repeated runs.

## Technical notes
- EventBridge Scheduler rule every 1 minute -> Lambda. Delete transit objects older than 15 minutes (`SWEEPER_MAX_AGE_MINUTES`) and mark such transfers `expired`; mark transfers still `requested` with no ack after 60 seconds `failed` (`owner_unresponsive`).
- Must be idempotent and tolerate objects that are already gone. Effective object lifetime is up to ~16 minutes.

## Notes
_(add during implementation)_
