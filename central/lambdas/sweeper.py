"""Transfer sweeper, run by an EventBridge rule every minute. Enforces the timing rules for
transfers: an unacknowledged request fails after TRANSFER_ACK_TIMEOUT_SECONDS, an upload that never
completes fails after TRANSFER_UPLOAD_TIMEOUT_SECONDS, and a transit object is deleted (and its
transfer marked `expired`) once the transfer is SWEEPER_MAX_AGE_MINUTES old.

Age is the transfer's created_at, not the S3 object's age: no bucket listing is needed and it bounds
the object's life even when the owner uploads late. S3 is deleted first and `swept_at` is set second,
so a crash between them only repeats a harmless delete. Overlapping runs are safe because every
UPDATE is guarded by `swept_at IS NULL`. A run pages through the due rows with a keyset cursor, so
rows whose delete keeps failing are skipped for this run (and retried next minute) instead of
blocking newer rows. Objects with no transfer row are left to the bucket's one-day lifecycle rule.
Nothing but counts is logged."""
import os

from common import db, transit
from common.transfer_state import IN_FLIGHT, apply_timeouts


def _override(event, key):
    """A non-negative integer `key` in a direct invocation's event, else None. The scheduled event
    carries none; tests use these to avoid waiting for the real timeouts."""
    value = (event or {}).get(key)
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def max_age_minutes(event):
    """SWEEPER_MAX_AGE_MINUTES, unless a direct invocation overrides it with `max_age_minutes`."""
    override = _override(event, "max_age_minutes")
    return override if override is not None else int(os.environ.get("SWEEPER_MAX_AGE_MINUTES", "15"))


def _sweep_page(age_minutes, after):
    """Delete one page of due objects after the cursor `after` ((created_at, transfer_id) or None)
    and mark their transfers. Returns (rows seen, swept, errors, new cursor)."""
    cursor_sql, cursor_params = ("AND (created_at, transfer_id) > (%s, %s) ", after) if after else ("", ())
    with db.transaction() as cur:
        cur.execute("SELECT transfer_id, s3_key, created_at FROM transfers WHERE swept_at IS NULL "
                    f"AND created_at < now() - make_interval(mins => %s) {cursor_sql}"
                    "ORDER BY created_at, transfer_id LIMIT %s",
                    (age_minutes, *cursor_params, transit.DELETE_BATCH))
        rows = cur.fetchall()
    if not rows:
        return 0, 0, 0, after
    deleted, errors = transit.delete_objects([key for _, key, _ in rows if key])
    done = [str(transfer_id) for transfer_id, key, _ in rows if key is None or key in deleted]
    if done:
        with db.transaction() as cur:
            cur.execute(
                f"UPDATE transfers SET swept_at = now(), "
                f"status = CASE WHEN status IN {IN_FLIGHT} THEN 'expired' ELSE status END, "
                f"updated_at = now() WHERE transfer_id = ANY(%s::uuid[]) AND swept_at IS NULL", (done,))
    return len(rows), len(done), errors, (rows[-1][2], rows[-1][0])


def staging_ttl_minutes():
    return int(os.environ.get("CHUNK_STAGING_TTL_MINUTES", "60"))


def clear_stale_staging():
    """Drop chunk uploads (E6-S3) that were started but never committed. Returns the row count."""
    with db.transaction() as cur:
        cur.execute("DELETE FROM public_chunks_staging WHERE staged_at < now() - make_interval(mins => %s)",
                    (staging_ttl_minutes(),))
        return cur.rowcount


def handler(event, context):
    age_minutes = max_age_minutes(event)
    with db.transaction() as cur:
        failed_unacked, failed_stalled = apply_timeouts(cur, upload_seconds=_override(event, "upload_timeout_seconds"))
    swept = delete_errors = 0
    after = None
    while True:
        seen, done, errors, after = _sweep_page(age_minutes, after)
        swept += done
        delete_errors += errors
        if seen < transit.DELETE_BATCH:  # a short page means everything due has been visited
            break
    staging_cleared = clear_stale_staging()  # last, so the transfer statements keep their order
    result = {"failed_unacked": failed_unacked, "failed_stalled": failed_stalled,
              "swept": swept, "delete_errors": delete_errors}
    print(f"sweeper run: {result} staging_cleared={staging_cleared}")
    return result
