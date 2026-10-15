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
- [x] A scheduled job (every minute) deletes S3 objects older than 15 minutes and marks transfers expired.
- [x] Idempotent on repeated runs.

## Technical notes
- EventBridge Scheduler rule every 1 minute -> Lambda. Delete transit objects older than 15 minutes (`SWEEPER_MAX_AGE_MINUTES`) and mark such transfers `expired`; mark transfers still `requested` with no ack after 60 seconds `failed` (`owner_unresponsive`).
- Must be idempotent and tolerate objects that are already gone. Effective object lifetime is up to ~16 minutes.

## Notes
Implemented, deployed and verified against the shared stack.
- **Age clock is `transfers.created_at`, not the S3 object's age.** No bucket listing is needed, and it bounds the object's life even if the owner uploads up to 10 minutes late (a LastModified clock could leave an object ~25 minutes). Trade-off: a very slow upload leaves the requester less time to download.
- **Idempotent and crash-safe:** objects are deleted first and `transfers.swept_at` is set second (migration `0004`), so a crash only repeats a harmless delete. S3 `DeleteObjects` reports a missing key as deleted. Only keys S3 reports deleted are marked, so a failed delete retries next minute. UPDATEs are guarded by `swept_at IS NULL`, so overlapping runs are safe (no reserved concurrency).
- **`expired` applies to `requested|uploading|ready`**; a `failed` transfer keeps its status (its object may still exist, since an owner can upload and then fail) and just gets `swept_at`. `expired` is outside the in-flight unique index, so the same file can be requested again.
- **Unacked requests** use the same SQL as the API's lazy timeout (`common/transfer_state.py`, shared with `transfers.py`).
- **Runs in the VPC** (it needs the DB), with a free S3 **gateway** endpoint added for S3 access. The interface-endpoint alternative would cost ~$7/month/AZ.
- **Schedule:** a plain EventBridge rule (`rate(1 minute)`), not EventBridge Scheduler: stable CDK construct, same behaviour.
- **Orphans:** objects with no transfer row (for example a failed insert) are not found; the bucket's one-day lifecycle rule remains the backstop. The sweeper never lists the bucket.
- **Test hook:** a direct invocation may pass `{"max_age_minutes": N}` to override the config; the scheduled event carries none. Only principals allowed to invoke the function can use it.
- Logs only counts (`failed_unacked`, `swept`, `delete_errors`), never keys or ids.
- verify-in-AWS results:
  - The VPC Lambda deletes through the S3 gateway endpoint (no NAT): the direct-invoke tests saw the object return 404 and the transfer become `expired`, with `delete_errors: 0`.
  - The rule fires about once a minute (at least 3 `sweeper run` log lines in a 5-minute window).
  - With no manual invocation, the schedule alone deleted a real object and expired its transfer at the configured age (about 15 minutes after the request).
  - A second run is a no-op, and an expired transfer can be requested again.
  - The sweeper fails an unacked request (`owner_unresponsive`) before anyone reads it.
  - Test lesson: the 5-minute download URL returns 403 once it lapses, so a 403 does not mean the object is gone. The tests require a 404 from a freshly signed URL.
