"""Metadata API (Interface B /files/*). One Lambda behind four routes; dispatches on
routeKey. owner_id comes from the token and team_id from membership, never from input."""
import base64
import binascii
import os
import uuid

from common import db
from common.access_log import log_event
from common.auth import get_caller_sub
from common.errors import ApiError, Unauthorized, error_response, unauthorized_response
from common.http import get_membership, invalid_request, iso, json_response, optional_timestamp, parse_body

FILENAME_MAX_CHARS = 255
TAGS_MAX_COUNT = 50
TAG_MAX_CHARS = 100
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500


def retention_days():
    return int(os.environ.get("RETENTION_DAYS", "45"))


def _file_id(event):
    raw = (event.get("pathParameters") or {}).get("file_id", "")
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError, TypeError):
        raise invalid_request("file_id") from None


def _validate_put(body):
    bad = []
    filename = body.get("filename")
    if not isinstance(filename, str) or not filename.strip() or len(filename) > FILENAME_MAX_CHARS:
        bad.append("filename")
    tags = body.get("tags", [])
    if (not isinstance(tags, list) or len(tags) > TAGS_MAX_COUNT
            or any(not isinstance(t, str) or not t.strip() or len(t) > TAG_MAX_CHARS for t in tags)):
        bad.append("tags")
    stamps = {}
    for field in ("file_created_at", "file_modified_at"):
        try:
            stamps[field] = optional_timestamp(body, field)
        except ApiError:
            bad.append(field)
    if bad:
        raise invalid_request(*bad)
    return filename.strip(), [t.strip() for t in tags], stamps["file_created_at"], stamps["file_modified_at"]


def _owned_by_someone_else(cur, file_id, user_id):
    cur.execute("SELECT owner_id FROM public_files WHERE file_id = %s", (file_id,))
    row = cur.fetchone()
    return row is not None and row[0] != user_id


def put_file(cur, user_id, event, body):
    file_id = _file_id(event)
    filename, tags, created_at, modified_at = _validate_put(body)
    team = get_membership(cur, user_id)
    if not team:
        raise ApiError(403, "no_team", "you are not in a team")
    cur.execute(
        "INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, file_created_at, "
        "file_modified_at, published_at, expires_at, last_confirmed) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, now(), now() + make_interval(days => %s), now()) "
        "ON CONFLICT (file_id) DO UPDATE SET filename = EXCLUDED.filename, tags = EXCLUDED.tags, "
        "file_created_at = EXCLUDED.file_created_at, file_modified_at = EXCLUDED.file_modified_at "
        "WHERE public_files.owner_id = EXCLUDED.owner_id "
        "RETURNING published_at, expires_at, last_confirmed, (xmax = 0)",
        (file_id, user_id, team[0], filename, tags, created_at, modified_at, retention_days()))
    row = cur.fetchone()
    if row is None:
        raise ApiError(403, "forbidden", "this file belongs to another user")
    published_at, expires_at, last_confirmed, inserted = row
    if inserted:
        log_event(cur, "publish", user_id, team[0], file_id)
    return json_response(200, {"file_id": file_id, "published_at": iso(published_at),
                               "expires_at": iso(expires_at), "last_confirmed": iso(last_confirmed)})


def delete_file(cur, user_id, event, body):
    file_id = _file_id(event)
    cur.execute("DELETE FROM public_files WHERE file_id = %s AND owner_id = %s RETURNING team_id",
                (file_id, user_id))
    row = cur.fetchone()
    if row:
        log_event(cur, "unpublish", user_id, row[0], file_id)
    elif _owned_by_someone_else(cur, file_id, user_id):
        raise ApiError(403, "forbidden", "this file belongs to another user")
    return {"statusCode": 204, "headers": {}, "body": ""}


def confirm_file(cur, user_id, event, body):
    file_id = _file_id(event)
    cur.execute(
        "UPDATE public_files SET expires_at = now() + make_interval(days => %s), last_confirmed = now() "
        "WHERE file_id = %s AND owner_id = %s AND expires_at > now() "
        "RETURNING team_id, expires_at, last_confirmed",
        (retention_days(), file_id, user_id))
    row = cur.fetchone()
    if row is None:
        if _owned_by_someone_else(cur, file_id, user_id):
            raise ApiError(403, "forbidden", "this file belongs to another user")
        raise ApiError(404, "not_found", "file not found")
    team_id, expires_at, last_confirmed = row
    log_event(cur, "confirm", user_id, team_id, file_id)
    return json_response(200, {"expires_at": iso(expires_at), "last_confirmed": iso(last_confirmed)})


def _decode_cursor(raw):
    try:
        return str(uuid.UUID(base64.urlsafe_b64decode(raw.encode()).decode()))
    except (ValueError, binascii.Error, UnicodeError):
        raise invalid_request("cursor") from None


def list_mine(cur, user_id, event, body):
    params = event.get("queryStringParameters") or {}
    try:
        limit = int(params.get("limit", DEFAULT_PAGE_SIZE))
    except ValueError:
        raise invalid_request("limit") from None
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise invalid_request("limit")
    cursor = _decode_cursor(params["cursor"]) if params.get("cursor") else None
    cur.execute(
        "SELECT file_id, filename, published_at, expires_at, last_confirmed FROM public_files "
        "WHERE owner_id = %s AND (%s::text IS NULL OR file_id > %s) ORDER BY file_id LIMIT %s",
        (user_id, cursor, cursor, limit + 1))
    rows = cur.fetchall()
    page = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        next_cursor = base64.urlsafe_b64encode(page[-1][0].encode()).decode()
    return json_response(200, {
        "files": [{"file_id": r[0], "filename": r[1], "published_at": iso(r[2]),
                   "expires_at": iso(r[3]), "last_confirmed": iso(r[4])} for r in page],
        "next_cursor": next_cursor,
    })


ROUTES = {
    "PUT /files/{file_id}": put_file,
    "DELETE /files/{file_id}": delete_file,
    "POST /files/{file_id}/confirm": confirm_file,
    "GET /files/mine": list_mine,
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
        body = parse_body(event)
        with db.transaction() as cur:
            return route(cur, user_id, event, body)
    except ApiError as exc:
        return error_response(exc.status, exc.code, exc.message, exc.details)
    except Exception as exc:  # noqa: BLE001
        print(f"files handler error: {type(exc).__name__}")  # never log bodies or values
        return error_response(503, "service_unavailable", "service unavailable")
