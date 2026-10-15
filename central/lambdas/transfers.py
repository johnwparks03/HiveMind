"""Transfer API (Interface B /transfers*). One Lambda behind five routes; dispatches on
routeKey. The requester and owner come from the token and the team from membership, never
from input. Each route opens its own transactions: POST /transfers commits the row before it
notifies the owner, so the owner can never ack a transfer that is not yet visible."""
import os
import uuid

from common import db, relay, transit
from common.access_log import log_event
from common.auth import get_caller_sub
from common.errors import ApiError, Unauthorized, error_response, unauthorized_response
from common.http import get_membership, invalid_request, iso, json_response, parse_body

IN_FLIGHT = "('requested', 'uploading', 'ready')"
FAIL_ERROR_CODES = {"file_not_found": "file_unavailable", "not_public": "file_unavailable",
                    "upload_error": "upload_failed"}


def ack_timeout_seconds():
    return int(os.environ.get("TRANSFER_ACK_TIMEOUT_SECONDS", "60"))


def _uuid_or_none(raw):
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError, TypeError):
        return None


def _transfer_id(event):
    transfer_id = _uuid_or_none((event.get("pathParameters") or {}).get("transfer_id", ""))
    if transfer_id is None:
        raise invalid_request("transfer_id")
    return transfer_id


def _expire_unacked(cur, where, params):
    """Lazily apply the ack timeout (the sweeper does it too): a transfer still `requested`
    after TRANSFER_ACK_TIMEOUT_SECONDS has failed."""
    cur.execute(
        "UPDATE transfers SET status = 'failed', error_code = 'owner_unresponsive', updated_at = now() "
        f"WHERE status = 'requested' AND created_at < now() - make_interval(secs => %s) AND {where}",
        (ack_timeout_seconds(), *params))


def _accepted(transfer_id, status):
    return json_response(202, {"transfer_id": transfer_id, "status": status})


def _existing_in_flight(cur, file_id, user_id):
    cur.execute(f"SELECT transfer_id, status FROM transfers WHERE file_id = %s AND requester_id = %s "
                f"AND status IN {IN_FLIGHT}", (file_id, user_id))
    return cur.fetchone()


def _check_and_record(cur, user_id, file_id):
    """Phase 1 of POST /transfers. Returns ("reused", id, status), ("offline",), or
    ("created", transfer_id, owner_id, team_id). Raises ApiError for the validation failures,
    which are not logged: they identify no file."""
    team = get_membership(cur, user_id)
    if not team:
        raise ApiError(403, "no_team", "you are not in a team")
    team_id = team[0]
    cur.execute("SELECT owner_id FROM public_files WHERE file_id = %s AND team_id = %s AND expires_at > now()",
                (file_id, team_id))
    row = cur.fetchone()
    if row is None:
        raise ApiError(404, "not_found", "file not found")
    owner_id = row[0]
    if owner_id == user_id:
        raise ApiError(400, "own_file", "this is your own file")
    _expire_unacked(cur, "file_id = %s AND requester_id = %s", (file_id, user_id))
    existing = _existing_in_flight(cur, file_id, user_id)
    if existing:
        log_event(cur, "transfer_request", user_id, team_id, file_id, str(existing[0]), "reused")
        return ("reused", str(existing[0]), existing[1])
    cur.execute("SELECT 1 FROM connections WHERE user_id = %s LIMIT 1", (owner_id,))
    if cur.fetchone() is None:
        log_event(cur, "transfer_request", user_id, team_id, file_id, outcome="owner_offline")
        return ("offline",)
    transfer_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO transfers (transfer_id, file_id, requester_id, owner_id, status, s3_key) "
        "VALUES (%s, %s, %s, %s, 'requested', %s) "
        f"ON CONFLICT (file_id, requester_id) WHERE status IN {IN_FLIGHT} DO NOTHING "
        "RETURNING transfer_id", (transfer_id, file_id, user_id, owner_id, transfer_id))
    if cur.fetchone() is None:  # a concurrent identical request won the race: reuse it
        existing = _existing_in_flight(cur, file_id, user_id)
        log_event(cur, "transfer_request", user_id, team_id, file_id, str(existing[0]), "reused")
        return ("reused", str(existing[0]), existing[1])
    log_event(cur, "transfer_request", user_id, team_id, file_id, transfer_id, "requested")
    return ("created", transfer_id, owner_id, team_id)


def create_transfer(user_id, event, body):
    file_id = _uuid_or_none(body.get("file_id"))
    if file_id is None:
        raise invalid_request("file_id")
    with db.transaction() as cur:
        result = _check_and_record(cur, user_id, file_id)
    if result[0] == "reused":
        return _accepted(result[1], result[2])
    if result[0] == "offline":
        raise ApiError(409, "owner_offline", "the file's owner is not online")
    _, transfer_id, owner_id, team_id = result

    # The row is committed, so the owner's ack cannot race ahead of it.
    delivered, failure = False, "owner_offline"
    try:
        upload_url, expires_at = transit.presign_put(transfer_id)
        delivered = relay.send_to_user(owner_id, {
            "action": "upload_request", "transfer_id": transfer_id, "file_id": file_id,
            "upload_url": upload_url, "upload_url_expires_at": iso(expires_at),
            "ack_deadline_seconds": ack_timeout_seconds()})
    except Exception as exc:  # noqa: BLE001
        print(f"transfer notify error: {type(exc).__name__}")  # never log urls or ids
        failure = "send_failed"
    if delivered:
        return _accepted(transfer_id, "requested")
    with db.transaction() as cur:
        cur.execute("UPDATE transfers SET status = 'failed', error_code = 'owner_unresponsive', "
                    "updated_at = now() WHERE transfer_id = %s AND status = 'requested'", (transfer_id,))
        log_event(cur, "transfer_request", user_id, team_id, file_id, transfer_id, failure)
    if failure == "send_failed":
        raise ApiError(503, "service_unavailable", "could not reach the file's owner")
    raise ApiError(409, "owner_offline", "the file's owner is not online")


def get_transfer(user_id, event, body):
    transfer_id = _transfer_id(event)
    with db.transaction() as cur:
        _expire_unacked(cur, "transfer_id = %s AND requester_id = %s", (transfer_id, user_id))
        cur.execute("SELECT file_id, status, s3_key, error_code FROM transfers "
                    "WHERE transfer_id = %s AND requester_id = %s", (transfer_id, user_id))
        row = cur.fetchone()
    if row is None:
        raise ApiError(404, "not_found", "transfer not found")
    file_id, status, s3_key, error_code = row
    result = {"transfer_id": transfer_id, "file_id": file_id, "status": status, "error_code": error_code}
    if status == "ready":
        url, expires_at = transit.presign_get(s3_key)
        result.update(download_url=url, download_url_expires_at=iso(expires_at))
    return json_response(200, result)


def _transition(user_id, event, to_status, from_statuses, set_sql="", set_params=()):
    """Owner-only state change. Repeating the transition already made is a 204 (retries are
    safe); any other state is 409 conflict. Not the owner, or no such transfer, is 404."""
    transfer_id = _transfer_id(event)
    with db.transaction() as cur:
        _expire_unacked(cur, "transfer_id = %s AND owner_id = %s", (transfer_id, user_id))
        placeholders = ", ".join(["%s"] * len(from_statuses))
        cur.execute(
            f"UPDATE transfers SET status = %s, updated_at = now(){set_sql} "
            f"WHERE transfer_id = %s AND owner_id = %s AND status IN ({placeholders}) RETURNING 1",
            (to_status, *set_params, transfer_id, user_id, *from_statuses))
        if cur.fetchone() is not None:
            return {"statusCode": 204, "headers": {}, "body": ""}
        cur.execute("SELECT status FROM transfers WHERE transfer_id = %s AND owner_id = %s",
                    (transfer_id, user_id))
        row = cur.fetchone()
    if row is None:
        raise ApiError(404, "not_found", "transfer not found")
    if row[0] == to_status:
        return {"statusCode": 204, "headers": {}, "body": ""}
    raise ApiError(409, "conflict", "transfer is not in a state that allows this", {"status": row[0]})


def ack_transfer(user_id, event, body):
    return _transition(user_id, event, "uploading", ("requested",))


def complete_transfer(user_id, event, body):
    size = body.get("size_bytes")
    if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 0):
        raise invalid_request("size_bytes")
    return _transition(user_id, event, "ready", ("requested", "uploading"),
                       ", size_bytes = %s", (size,))


def fail_transfer(user_id, event, body):
    reason = body.get("reason")
    if reason not in FAIL_ERROR_CODES:
        raise invalid_request("reason")
    return _transition(user_id, event, "failed", ("requested", "uploading"),
                       ", error_code = %s", (FAIL_ERROR_CODES[reason],))


ROUTES = {
    "POST /transfers": create_transfer,
    "GET /transfers/{transfer_id}": get_transfer,
    "POST /transfers/{transfer_id}/ack": ack_transfer,
    "POST /transfers/{transfer_id}/complete": complete_transfer,
    "POST /transfers/{transfer_id}/fail": fail_transfer,
}


def handler(event, context):
    try:
        user_id = get_caller_sub(event)
    except Unauthorized:
        return unauthorized_response()
    route = ROUTES.get(event.get("routeKey"))
    if route is None:
        return error_response(404, "not_found", "route not found")
    try:
        return route(user_id, event, parse_body(event))
    except ApiError as exc:
        return error_response(exc.status, exc.code, exc.message, exc.details)
    except Exception as exc:  # noqa: BLE001
        print(f"transfers handler error: {type(exc).__name__}")  # never log bodies or values
        return error_response(503, "service_unavailable", "service unavailable")
