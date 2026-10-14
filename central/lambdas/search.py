"""Central search (Interface B POST /search): team-scoped full-text search over published
file metadata. No LLM call. team_id comes from membership, never from input; owner identity
is never returned; the topic and dates are never logged."""
import os
import re

from common import db
from common.access_log import log_event
from common.auth import get_caller_sub
from common.errors import ApiError, Unauthorized, error_response, unauthorized_response
from common.http import (get_membership, invalid_request, iso, json_response, optional_timestamp,
                         parse_body)

TOPIC_MAX_CHARS = 500
WORD_RE = re.compile(r"[A-Za-z0-9]+")  # the same word splitting the filename vector uses

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


ROUTES = {
    "POST /search": search,
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
