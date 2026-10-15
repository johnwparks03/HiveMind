"""Transfer sweeper, run by an EventBridge rule every minute. Enforces the two timing rules for
transfers: an unacknowledged request fails after TRANSFER_ACK_TIMEOUT_SECONDS, and a transit object
is deleted (and its transfer marked `expired`) once the transfer is SWEEPER_MAX_AGE_MINUTES old.

Age is the transfer's created_at, not the S3 object's age: no bucket listing is needed and it bounds
the object's life even when the owner uploads late. S3 is deleted first and `swept_at` is set second,
so a crash between them only repeats a harmless delete. Overlapping runs are safe because every
UPDATE is guarded by `swept_at IS NULL`. Objects with no transfer row are left to the bucket's
one-day lifecycle rule. Nothing but counts is logged."""
import os

from common import db, transit
from common.transfer_state import expire_unacked

IN_FLIGHT = "('requested', 'uploading', 'ready')"


def max_age_minutes(event):
    """SWEEPER_MAX_AGE_MINUTES, unless a direct invocation overrides it with a non-negative
    integer `max_age_minutes` (the scheduled event carries none; tests use it to avoid waiting)."""
    override = (event or {}).get("max_age_minutes")
    if isinstance(override, int) and not isinstance(override, bool) and override >= 0:
        return override
    return int(os.environ.get("SWEEPER_MAX_AGE_MINUTES", "15"))


def _sweep_batch(age_minutes):
    """Delete one batch of due objects and mark their transfers. Returns (rows seen, swept, errors)."""
    with db.transaction() as cur:
        cur.execute("SELECT transfer_id, s3_key FROM transfers WHERE swept_at IS NULL "
                    "AND created_at < now() - make_interval(mins => %s) ORDER BY created_at LIMIT %s",
                    (age_minutes, transit.DELETE_BATCH))
        rows = cur.fetchall()
    if not rows:
        return 0, 0, 0
    deleted, errors = transit.delete_objects([key for _, key in rows if key])
    done = [str(transfer_id) for transfer_id, key in rows if key is None or key in deleted]
    if done:
        with db.transaction() as cur:
            cur.execute(
                f"UPDATE transfers SET swept_at = now(), "
                f"status = CASE WHEN status IN {IN_FLIGHT} THEN 'expired' ELSE status END, "
                f"updated_at = now() WHERE transfer_id = ANY(%s::uuid[]) AND swept_at IS NULL", (done,))
    return len(rows), len(done), errors


def handler(event, context):
    age_minutes = max_age_minutes(event)
    with db.transaction() as cur:
        failed_unacked = expire_unacked(cur)
    swept = delete_errors = 0
    while True:
        seen, done, errors = _sweep_batch(age_minutes)
        swept += done
        delete_errors += errors
        if seen < transit.DELETE_BATCH or done == 0:  # drained, or stuck on errors: retry next minute
            break
    result = {"failed_unacked": failed_unacked, "swept": swept, "delete_errors": delete_errors}
    print(f"sweeper run: {result}")
    return result
