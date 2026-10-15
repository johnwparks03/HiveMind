"""Transfer state rules shared by the Transfer API (lazy) and the sweeper (scheduled)."""
import os

# Statuses in which a transfer is still live for its (file, requester) pair. Must match the
# predicate of the partial unique index in migrations/0003_transfers_api.sql (a test checks it).
IN_FLIGHT = "('requested', 'uploading', 'ready')"


def ack_timeout_seconds():
    return int(os.environ.get("TRANSFER_ACK_TIMEOUT_SECONDS", "60"))


def upload_timeout_seconds():
    return int(os.environ.get("TRANSFER_UPLOAD_TIMEOUT_SECONDS", "600"))


def expire_unacked(cur, where="TRUE", params=()):
    """A transfer still `requested` after TRANSFER_ACK_TIMEOUT_SECONDS has failed. `where` narrows
    which transfers (the API passes one pair; the sweeper passes all). Returns the rows changed."""
    cur.execute(
        "UPDATE transfers SET status = 'failed', error_code = 'owner_unresponsive', updated_at = now() "
        f"WHERE status = 'requested' AND created_at < now() - make_interval(secs => %s) AND {where}",
        (ack_timeout_seconds(), *params))
    return cur.rowcount


def expire_stalled_uploads(cur, where="TRUE", params=(), seconds=None):
    """A transfer still `uploading` TRANSFER_UPLOAD_TIMEOUT_SECONDS after the owner's ack has failed.
    The ack sets updated_at, so the clock runs from the ack. `seconds` overrides the config (tests
    through the sweeper). Returns the rows changed."""
    cur.execute(
        "UPDATE transfers SET status = 'failed', error_code = 'upload_failed', updated_at = now() "
        f"WHERE status = 'uploading' AND updated_at < now() - make_interval(secs => %s) AND {where}",
        (upload_timeout_seconds() if seconds is None else seconds, *params))
    return cur.rowcount


def apply_timeouts(cur, where="TRUE", params=(), upload_seconds=None):
    """Both timeouts, unacknowledged first. Returns (failed_unacked, failed_stalled)."""
    return expire_unacked(cur, where, params), expire_stalled_uploads(cur, where, params, upload_seconds)
