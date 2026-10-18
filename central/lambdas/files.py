"""Metadata API (Interface B /files/*). One Lambda behind five routes; dispatches on
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
from common.vectors import embedding_dimension, is_embedding, is_int, vector_literal

FILENAME_MAX_CHARS = 255
TAGS_MAX_COUNT = 50
TAG_MAX_CHARS = 100
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500


def retention_days():
    return int(os.environ.get("RETENTION_DAYS", "45"))


def chunk_batch_size():
    return int(os.environ.get("CHUNK_UPLOAD_BATCH_SIZE", "100"))


def max_chunks_per_file():
    return int(os.environ.get("MAX_CHUNKS_PER_FILE", "2000"))


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


def _validate_chunks(body):
    """Returns (batch, total_batches, [(chunk_index, text, vector_literal)]). Bad fields are reported
    by name only, never by value."""
    bad = []
    batch, total = body.get("batch"), body.get("total_batches")
    max_total = -(-max_chunks_per_file() // chunk_batch_size())
    if not is_int(batch) or batch < 1:
        bad.append("batch")
    if not is_int(total) or not 1 <= total <= max_total:
        bad.append("total_batches")
    elif "batch" not in bad and batch > total:
        bad.append("batch")
    chunks, rows = body.get("chunks"), []
    if not isinstance(chunks, list) or len(chunks) > chunk_batch_size() or (not chunks and total != 1):
        bad.append("chunks")
    else:
        seen, dimension, cap = set(), embedding_dimension(), max_chunks_per_file()
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                bad.append(f"chunks[{i}]")
                continue
            index, text, embedding = chunk.get("chunk_index"), chunk.get("text"), chunk.get("embedding")
            if not is_int(index) or not 0 <= index < cap or index in seen:
                bad.append(f"chunks[{i}].chunk_index")
            else:
                seen.add(index)
            if not isinstance(text, str) or not text.strip():
                bad.append(f"chunks[{i}].text")
            if not is_embedding(embedding, dimension):
                bad.append(f"chunks[{i}].embedding")
                continue
            rows.append((index, text, vector_literal(embedding)))
    if bad:
        raise invalid_request(*bad[:20])
    return batch, total, rows


def put_chunks(cur, user_id, event, body):
    """One batch of a file's chunks. Batches are staged and swapped into public_chunks in one
    transaction on the final batch, so a reader sees the old set or the new set, never a mix."""
    file_id = _file_id(event)
    batch, total, rows = _validate_chunks(body)
    team = get_membership(cur, user_id)
    if not team:
        raise ApiError(403, "no_team", "you are not in a team")
    # The row lock serializes concurrent uploads of the same file.
    cur.execute("SELECT owner_id FROM public_files WHERE file_id = %s FOR UPDATE", (file_id,))
    owner = cur.fetchone()
    if owner is None:
        raise ApiError(404, "not_found", "file not found")
    if owner[0] != user_id:
        raise ApiError(403, "forbidden", "this file belongs to another user")
    if batch == 1:
        cur.execute("DELETE FROM public_chunks_staging WHERE file_id = %s", (file_id,))
    if rows:
        placeholders = ", ".join(["(%s, %s, %s, %s, %s, %s::vector)"] * len(rows))
        params = [p for index, text, literal in rows for p in (file_id, index, batch, total, text, literal)]
        cur.execute(
            "INSERT INTO public_chunks_staging (file_id, chunk_index, batch, total_batches, text, embedding) "
            f"VALUES {placeholders} ON CONFLICT (file_id, chunk_index) DO UPDATE SET batch = EXCLUDED.batch, "
            "total_batches = EXCLUDED.total_batches, text = EXCLUDED.text, embedding = EXCLUDED.embedding, "
            "staged_at = now()", params)
    cur.execute(
        "SELECT count(*), count(DISTINCT batch), min(batch), max(batch), count(DISTINCT total_batches), "
        "min(total_batches), min(chunk_index), max(chunk_index) FROM public_chunks_staging WHERE file_id = %s",
        (file_id,))
    count, batches, first, last, totals, staged_total, low, high = cur.fetchone()
    if count > max_chunks_per_file():
        raise invalid_request("chunks")
    if totals > 1 or (count and staged_total != total):
        raise invalid_request("total_batches")
    if batch < total:
        return json_response(200, {"file_id": file_id, "chunk_count": 0, "committed": False})
    # Final batch: every batch must be staged and the chunk indexes contiguous from 0.
    if count == 0:
        if total != 1:
            raise invalid_request("batch")
    elif batches != total or first != 1 or last != total:
        raise invalid_request("batch")  # an earlier batch is missing: restart from batch 1
    elif low != 0 or high != count - 1:
        raise invalid_request("chunks")
    cur.execute("DELETE FROM public_chunks WHERE file_id = %s", (file_id,))
    cur.execute("INSERT INTO public_chunks (file_id, chunk_index, text, embedding) "
                "SELECT file_id, chunk_index, text, embedding FROM public_chunks_staging WHERE file_id = %s",
                (file_id,))
    cur.execute("DELETE FROM public_chunks_staging WHERE file_id = %s", (file_id,))
    cur.execute("UPDATE public_files SET chunk_count = %s, chunks_indexed_at = now() WHERE file_id = %s",
                (count, file_id))
    log_event(cur, "chunks_put", user_id, team[0], file_id)
    return json_response(200, {"file_id": file_id, "chunk_count": count, "committed": True})


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
        "SELECT file_id, filename, published_at, expires_at, last_confirmed, COALESCE(chunk_count, 0) "
        "FROM public_files "
        "WHERE owner_id = %s AND (%s::text IS NULL OR file_id > %s) ORDER BY file_id LIMIT %s",
        (user_id, cursor, cursor, limit + 1))
    rows = cur.fetchall()
    page = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        next_cursor = base64.urlsafe_b64encode(page[-1][0].encode()).decode()
    return json_response(200, {
        "files": [{"file_id": r[0], "filename": r[1], "published_at": iso(r[2]),
                   "expires_at": iso(r[3]), "last_confirmed": iso(r[4]), "chunk_count": r[5]} for r in page],
        "next_cursor": next_cursor,
    })


ROUTES = {
    "PUT /files/{file_id}": put_file,
    "DELETE /files/{file_id}": delete_file,
    "PUT /files/{file_id}/chunks": put_chunks,
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
