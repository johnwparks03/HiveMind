"""Transfer state rules shared by the Transfer API (lazy) and the sweeper (scheduled)."""
import os


def ack_timeout_seconds():
    return int(os.environ.get("TRANSFER_ACK_TIMEOUT_SECONDS", "60"))


def expire_unacked(cur, where="TRUE", params=()):
    """A transfer still `requested` after TRANSFER_ACK_TIMEOUT_SECONDS has failed. `where` narrows
    which transfers (the API passes one pair; the sweeper passes all). Returns the rows changed."""
    cur.execute(
        "UPDATE transfers SET status = 'failed', error_code = 'owner_unresponsive', updated_at = now() "
        f"WHERE status = 'requested' AND created_at < now() - make_interval(secs => %s) AND {where}",
        (ack_timeout_seconds(), *params))
    return cur.rowcount
