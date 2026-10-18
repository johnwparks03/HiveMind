"""Central search (Interface B): team-scoped search over published files. POST /search is full-text
search over file metadata; POST /retrieval/search (E6-S4) is vector search over the chunks teammates
published. No LLM call. team_id comes from membership, never from input; owner identity is never
returned; the topic, dates, query vector and chunk text are never logged."""
import os
import re

from common import db
from common.access_log import log_event
from common.auth import get_caller_sub
from common.errors import ApiError, Unauthorized, error_response, unauthorized_response
from common.http import (get_membership, invalid_request, iso, json_response, optional_timestamp,
                         parse_body)
from common.vectors import is_embedding, is_int, vector_literal

TOPIC_MAX_CHARS = 500
FILE_IDS_MAX = 200
# Unicode letters and digits; underscore is a separator, as in the filename vector, so accented
# and non-Latin words ("résumé", "契約書") stay whole and match what Postgres stored.
WORD_RE = re.compile(r"[^\W_]+")

# Recency: latest known activity on the file, falling back to when it was published.
RECENCY = "coalesce(pf.file_modified_at, pf.file_created_at, pf.published_at)"
IN_RANGE = "{col} BETWEEN coalesce(%(date_from)s::timestamptz, '-infinity') " \
           "AND coalesce(%(date_to)s::timestamptz, 'infinity')"

SEARCH_SQL = f"""
SELECT pf.file_id, pf.filename, pf.tags, pf.file_created_at, pf.file_modified_at, pf.expires_at,
       EXISTS (SELECT 1 FROM connections c WHERE c.user_id = pf.owner_id) AS owner_online
FROM public_files pf
{{topic_join}}
WHERE pf.team_id = %(team_id)s
  AND pf.owner_id <> %(user_id)s
  AND pf.expires_at > now()
  AND (
    (%(date_from)s::timestamptz IS NULL AND %(date_to)s::timestamptz IS NULL)
    OR {IN_RANGE.format(col="pf.file_created_at")}
    OR {IN_RANGE.format(col="pf.file_modified_at")}
  )
  {{topic_filter}}
ORDER BY {{rank}}{RECENCY} DESC, pf.file_id
LIMIT %(cap)s
"""


def result_cap():
    return int(os.environ.get("SEARCH_RESULT_CAP", "20"))


RETRIEVAL_SQL = """
SELECT pc.file_id, pf.filename, pc.chunk_index, pc.text, pc.embedding <=> %(q)s::vector AS distance
FROM public_chunks pc
JOIN public_files pf ON pf.file_id = pc.file_id
WHERE pf.team_id = %(team_id)s
  AND pf.owner_id <> %(user_id)s
  AND pf.expires_at > now()
  AND (%(file_ids)s::text[] IS NULL OR pf.file_id = ANY(%(file_ids)s))
ORDER BY pc.embedding <=> %(q)s::vector, pc.file_id, pc.chunk_index
LIMIT %(limit)s
"""
# The HNSW index filters after its scan, so a selective WHERE (team, not-own, expiry, file_ids) can
# starve the result. Iterative scans (pgvector 0.8+) keep scanning until the LIMIT is met, in order.
ITERATIVE_SCAN_SQL = "SET LOCAL hnsw.iterative_scan = 'strict_order'"


def retrieval_limit_default():
    return int(os.environ.get("RETRIEVAL_LIMIT_DEFAULT", "20"))


def retrieval_limit_max():
    return int(os.environ.get("RETRIEVAL_LIMIT_MAX", "50"))


def _validate(body):
    bad = []
    topic = body.get("topic")
    if topic is not None and (not isinstance(topic, str) or len(topic) > TOPIC_MAX_CHARS):
        bad.append("topic")
    stamps = {}
    for field in ("date_from", "date_to"):
        try:
            stamps[field] = optional_timestamp(body, field)
        except ApiError:
            bad.append(field)
    if not bad and stamps["date_from"] and stamps["date_to"] and stamps["date_from"] > stamps["date_to"]:
        bad += ["date_from", "date_to"]
    if bad:
        raise invalid_request(*bad)
    return (topic if topic and topic.strip() else None), stamps["date_from"], stamps["date_to"]


def _or_query(topic):
    """Any-word matching: websearch_to_tsquery reads 'or' as OR and never raises on odd input."""
    return " or ".join(WORD_RE.findall(topic))


def search(cur, user_id, body):
    topic, date_from, date_to = _validate(body)
    team = get_membership(cur, user_id)
    if not team:
        raise ApiError(403, "no_team", "you are not in a team")
    params = {"team_id": team[0], "user_id": user_id, "date_from": date_from,
              "date_to": date_to, "cap": result_cap()}
    if topic is None:
        sql = SEARCH_SQL.format(topic_join="", topic_filter="", rank="")
    else:
        params["topic_query"] = _or_query(topic)
        sql = SEARCH_SQL.format(
            topic_join="CROSS JOIN websearch_to_tsquery('english', %(topic_query)s) AS q",
            topic_filter="AND pf.search_vector @@ q",
            rank="ts_rank(pf.search_vector, q) DESC, ")
    cur.execute(sql, params)
    rows = cur.fetchall()
    # Ids only (see CLAUDE.md): one row per matched file, or one row with no file when empty.
    for row in rows:
        log_event(cur, "search", user_id, team[0], row[0])
    if not rows:
        log_event(cur, "search", user_id, team[0])
    return json_response(200, {"results": [
        {"file_id": r[0], "filename": r[1], "tags": list(r[2] or []),
         "file_created_at": iso(r[3]), "file_modified_at": iso(r[4]),
         "expires_at": iso(r[5]), "owner_online": bool(r[6])} for r in rows]})


def _validate_retrieval(body):
    """Returns (vector literal, file_ids or None, limit). Bad fields are named, never echoed."""
    bad = []
    embedding = body.get("query_embedding")
    if not is_embedding(embedding):
        bad.append("query_embedding")
    file_ids = body.get("file_ids")
    if file_ids is not None and (not isinstance(file_ids, list) or len(file_ids) > FILE_IDS_MAX
                                 or any(not isinstance(f, str) or not f.strip() for f in file_ids)):
        bad.append("file_ids")
    limit = body.get("limit")
    if limit is not None and (not is_int(limit) or limit < 1):
        bad.append("limit")
    if bad:
        raise invalid_request(*bad)
    limit = retrieval_limit_default() if limit is None else min(limit, retrieval_limit_max())
    return vector_literal(embedding), file_ids, limit


def retrieval_search(cur, user_id, body):
    """The closest chunks of teammates' published files to a query vector. The agent embeds the
    question locally, so the question text never reaches this service."""
    literal, file_ids, limit = _validate_retrieval(body)
    team = get_membership(cur, user_id)
    if not team:
        raise ApiError(403, "no_team", "you are not in a team")
    cur.execute(ITERATIVE_SCAN_SQL)
    cur.execute(RETRIEVAL_SQL, {"q": literal, "team_id": team[0], "user_id": user_id,
                                "file_ids": file_ids, "limit": limit})
    rows = cur.fetchall()
    # Ids only: one row per distinct matched file, or one row with no file when empty.
    matched = list(dict.fromkeys(row[0] for row in rows))
    for file_id in matched:
        log_event(cur, "retrieval_search", user_id, team[0], file_id)
    if not matched:
        log_event(cur, "retrieval_search", user_id, team[0])
    return json_response(200, {"results": [
        {"file_id": r[0], "filename": r[1], "chunk_index": r[2], "text": r[3],
         "distance": round(float(r[4]), 6)} for r in rows]})


ROUTES = {
    "POST /search": search,
    "POST /retrieval/search": retrieval_search,
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
            return route(cur, user_id, body)
    except ApiError as exc:
        return error_response(exc.status, exc.code, exc.message, exc.details)
    except Exception as exc:  # noqa: BLE001
        print(f"search handler error: {type(exc).__name__}")  # never log bodies or values
        return error_response(503, "service_unavailable", "service unavailable")
